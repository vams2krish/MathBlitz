"""Daily-life activity catalog and pluggable problem generators."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import math
import random
from typing import Protocol

from .difficulty import Difficulty, profile_for


CENT = Decimal("0.01")
TENTH = Decimal("0.1")
DEFAULT_ACTIVITY_ID = "shopping-value"


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def one_decimal(value: Decimal) -> Decimal:
    return value.quantize(TENTH, rounding=ROUND_HALF_UP)


def cents(value: int) -> Decimal:
    return money(Decimal(value) / Decimal(100))


def level_for(difficulty: Difficulty) -> int:
    return profile_for(difficulty).magnitude


@dataclass(frozen=True)
class GeneratedTask:
    prompt: str
    correct_answer: Decimal
    answer_mode: str
    hint: str
    context: dict[str, str | int | float | bool]


class ActivityGenerator(Protocol):
    def generate(self, difficulty: Difficulty, rng: random.Random) -> GeneratedTask: ...


@dataclass(frozen=True)
class ActivitySpec:
    id: str
    name: str
    description: str
    skill: str
    icon: str
    accent: str
    generator: ActivityGenerator
    variant_estimate: int = 10000


class ShoppingValue:
    def generate(self, difficulty: Difficulty, rng: random.Random) -> GeneratedTask:
        level = level_for(difficulty)
        branch = rng.randrange(3 if level >= 3 else 2)
        if branch == 0:
            qty_a = rng.randint(4, 12 + level * 4)
            qty_b = rng.randint(4, 12 + level * 5)
            unit_a_cents = rng.randint(18, 95 + level * 65)
            delta = rng.choice((-24, -18, -12, -8, 8, 12, 18, 24))
            unit_b_cents = max(5, unit_a_cents + delta)
            price_a = cents(unit_a_cents * qty_a)
            price_b = cents(unit_b_cents * qty_b)
            best = 1 if unit_a_cents < unit_b_cents else 2
            return GeneratedTask(
                (
                    f"At the store, Option 1 is ${price_a:.2f} for {qty_a} oz. "
                    f"Option 2 is ${price_b:.2f} for {qty_b} oz. "
                    "Which option has the lower unit price? Enter 1 or 2."
                ),
                Decimal(best),
                "choice",
                "Divide each price by the number of ounces, then pick the lower unit cost.",
                {"template": "unit-price", "options": 2},
            )
        if branch == 1:
            price = cents(rng.randint(150, 900 + level * 260))
            needed = rng.randint(3 + level, 8 + level * 3)
            paid_items = (needed // 3) * 2 + needed % 3
            answer = money(price * Decimal(paid_items) / Decimal(needed))
            return GeneratedTask(
                (
                    f"A buy 2, get 1 free offer applies to ${price:.2f} items. "
                    f"If you need {needed} items, what is the true cost per item?"
                ),
                answer,
                "currency",
                "Count how many items you actually pay for, then divide the total paid by the number you take home.",
                {"template": "bogo", "needed": needed},
            )
        needed_units = rng.randint(7 + level, 28 + level * 8)
        pack_a = rng.randint(3, 8 + level)
        pack_b = rng.randint(4, 10 + level)
        price_a = cents(rng.randint(260, 980 + level * 220))
        price_b = cents(rng.randint(340, 1200 + level * 250))
        total_a = money(price_a * Decimal(math.ceil(needed_units / pack_a)))
        total_b = money(price_b * Decimal(math.ceil(needed_units / pack_b)))
        best = 1 if total_a < total_b else 2
        return GeneratedTask(
            (
                f"You need at least {needed_units} servings. Option 1 has {pack_a} servings for ${price_a:.2f}; "
                f"Option 2 has {pack_b} servings for ${price_b:.2f}. Including extra servings you may not use, "
                "which option costs less? Enter 1 or 2."
            ),
            Decimal(best),
            "choice",
            "Round each package count up to cover the need, then compare total checkout cost.",
            {"template": "bulk-waste", "needed_units": needed_units},
        )


class DiscountsChange:
    def generate(self, difficulty: Difficulty, rng: random.Random) -> GeneratedTask:
        level = level_for(difficulty)
        if level <= 2:
            item_count = rng.randint(2, 3 + level)
            prices = [cents(rng.randint(75, 650)) for _ in range(item_count)]
            subtotal = money(sum(prices, Decimal("0")))
            paid = Decimal(math.ceil(float(subtotal) / 5) * 5 + rng.choice((0, 5, 10)))
            answer = money(paid - subtotal)
            listed = ", ".join(f"${price:.2f}" for price in prices)
            return GeneratedTask(
                f"You buy items costing {listed} and pay ${paid:.2f}. How much change should you get?",
                answer,
                "currency",
                "Add the item prices, then subtract that total from the cash paid.",
                {"template": "change", "item_count": item_count},
            )
        original = cents(rng.randint(1800, 16000 + level * 2800))
        first = rng.choice((10, 15, 20, 25, 30))
        second = rng.choice((5, 10, 15, 20)) if level >= 4 else 0
        taxed = rng.choice((0, 6, 7, 8, 9)) if level == 5 else 0
        discounted = original * Decimal(100 - first) / Decimal(100)
        if second:
            discounted = discounted * Decimal(100 - second) / Decimal(100)
        final = money(discounted * Decimal(100 + taxed) / Decimal(100))
        extra = f", then another {second}% off" if second else ""
        tax = f", then {taxed}% sales tax" if taxed else ""
        return GeneratedTask(
            f"A ${original:.2f} item is {first}% off{extra}{tax}. What is the final price?",
            final,
            "currency",
            "Apply each discount to the current price, not the original price, then apply tax if present.",
            {"template": "successive-discount", "first_discount": first, "second_discount": second},
        )


class BudgetPlanner:
    def generate(self, difficulty: Difficulty, rng: random.Random) -> GeneratedTask:
        level = level_for(difficulty)
        branch = rng.randrange(3)
        if branch == 0:
            days = rng.randint(5, 14 + level)
            reserve = Decimal(rng.randint(0, 5 + level * 5) * 5)
            spendable = Decimal(rng.randint(days * 8, days * (16 + level * 6)))
            budget = reserve + spendable
            answer = money((budget - reserve) / Decimal(days))
            return GeneratedTask(
                (
                    f"You have ${budget:.2f} for {days} days and want ${reserve:.2f} left over. "
                    "What is the most you can spend per day?"
                ),
                answer,
                "currency",
                "Set aside the leftover amount first, then divide the rest by the number of days.",
                {"template": "daily-budget"},
            )
        if branch == 1:
            goal = Decimal(rng.randint(20 + level * 5, 120 + level * 70) * 25)
            months = rng.randint(2 + level, 8 + level * 3)
            answer = money(goal / Decimal(months))
            return GeneratedTask(
                f"You want to save ${goal:.2f} in {months} months. How much should you set aside each month?",
                answer,
                "currency",
                "Monthly savings equals the goal divided by the number of months.",
                {"template": "sinking-fund"},
            )
        income = Decimal(rng.randint(35 + level * 8, 130 + level * 35) * 20)
        fixed = Decimal(rng.randint(8 + level * 4, 35 + level * 12) * 10)
        savings_rate = rng.choice((5, 10, 15, 20, 25))
        answer = money(income - fixed - income * Decimal(savings_rate) / Decimal(100))
        return GeneratedTask(
            (
                f"This week you have ${income:.2f} available, ${fixed:.2f} in fixed bills, "
                f"and want to save {savings_rate}%. How much can you spend after bills and savings?"
            ),
            answer,
            "currency",
            "Subtract fixed bills and the planned savings amount from the weekly money available.",
            {"template": "spending-cap", "savings_rate": savings_rate},
        )


class InterestCredit:
    def generate(self, difficulty: Difficulty, rng: random.Random) -> GeneratedTask:
        level = level_for(difficulty)
        if level <= 2:
            principal = Decimal(rng.randint(5, 70 + level * 30) * 100)
            rate = rng.choice((2, 3, 4, 5, 6, 8))
            years = rng.randint(1, 2 + level)
            answer = money(principal * Decimal(rate) * Decimal(years) / Decimal(100))
            return GeneratedTask(
                f"Simple interest: ${principal:.2f} earns {rate}% per year for {years} years. How much interest is earned?",
                answer,
                "currency",
                "Simple interest is principal x annual rate x years.",
                {"template": "simple-interest"},
            )
        if level <= 4:
            principal = Decimal(rng.randint(8, 90 + level * 45) * 100)
            rate = rng.choice((3, 4, 5, 6, 8, 10))
            years = rng.randint(2, 5 + level)
            answer = money(principal * ((Decimal(1) + Decimal(rate) / Decimal(100)) ** years))
            return GeneratedTask(
                f"${principal:.2f} grows at {rate}% compounded annually for {years} years. What is the final balance?",
                answer,
                "currency",
                "Multiply by 1 plus the rate once for each year.",
                {"template": "compound-interest"},
            )
        balance = Decimal(rng.randint(8, 80) * 50)
        apr = rng.choice((12, 16, 18, 20, 24, 29))
        payment = Decimal(rng.randint(3, 14) * 25)
        monthly_interest = money(balance * Decimal(apr) / Decimal(1200))
        answer = money(balance + monthly_interest - payment)
        return GeneratedTask(
            (
                f"A credit-card balance is ${balance:.2f} at {apr}% APR. If one month of interest is added "
                f"and then you pay ${payment:.2f}, what is the new balance?"
            ),
            answer,
            "currency",
            "Estimate monthly interest as APR divided by 12, add it, then subtract the payment.",
            {"template": "credit-month", "apr": apr},
        )


class HousingRealEstate:
    def generate(self, difficulty: Difficulty, rng: random.Random) -> GeneratedTask:
        level = level_for(difficulty)
        branch = rng.randrange(4)
        if branch == 0:
            bedrooms = rng.randint(2, 5 + level)
            people = bedrooms * rng.randint(2, 3)
            new_people = people + rng.randint(2, 4 + level * 2)
            answer = Decimal(math.ceil(new_people / (people / bedrooms)))
            return GeneratedTask(
                (
                    f"A {bedrooms}-bedroom home sleeps {people} people at the same density. "
                    f"How many bedrooms are needed for {new_people} people?"
                ),
                answer,
                "integer",
                "Find people per bedroom, then round up because a partial bedroom is not useful.",
                {"template": "bedroom-proportion"},
            )
        if branch == 1:
            sale_price = Decimal(rng.randint(18 + level * 8, 85 + level * 35) * 10000)
            commission = rng.choice((3, 4, 5, 6))
            split = rng.choice((1, 2)) if level >= 3 else 1
            answer = money(sale_price * Decimal(commission) / Decimal(100) / Decimal(split))
            split_text = " split evenly by two agents" if split == 2 else ""
            return GeneratedTask(
                f"A property sells for ${sale_price:,.2f} with a {commission}% commission{split_text}. How much does one side earn?",
                answer,
                "currency",
                "Find the commission, then divide it if the commission is split.",
                {"template": "commission", "split": split},
            )
        if branch == 2:
            rent = Decimal(rng.randint(90, 220 + level * 80) * 10)
            mortgage = rent + Decimal(rng.randint(10, 80 + level * 30) * 10)
            years = rng.randint(1, 5 + level)
            answer = money((mortgage - rent) * Decimal(12 * years))
            return GeneratedTask(
                (
                    f"Rent is ${rent:.2f}/month and a mortgage is ${mortgage:.2f}/month. "
                    f"Ignoring other costs, how much extra is the mortgage over {years} years?"
                ),
                answer,
                "currency",
                "Find the monthly difference, then multiply by 12 months and by the number of years.",
                {"template": "rent-buy-delta"},
            )
        value = Decimal(rng.randint(20 + level * 10, 90 + level * 40) * 10000)
        annual_tax_rate = Decimal(rng.choice((8, 10, 12, 14, 16, 18))) / Decimal(10)
        answer = money(value * annual_tax_rate / Decimal(100) / Decimal(12))
        return GeneratedTask(
            f"A home is valued at ${value:,.2f}. Property tax is {annual_tax_rate}% per year. What is the monthly tax amount?",
            answer,
            "currency",
            "Find the annual tax, then divide by 12 months.",
            {"template": "property-tax", "tax_rate": float(annual_tax_rate)},
        )


class OfficeMeetings:
    def generate(self, difficulty: Difficulty, rng: random.Random) -> GeneratedTask:
        level = level_for(difficulty)
        branch = rng.randrange(4)
        if branch == 0:
            people = rng.randint(3, 8 + level * 2)
            minutes = rng.choice((15, 20, 30, 45, 60, 75, 90))
            answer = one_decimal(Decimal(people * minutes) / Decimal(60))
            return GeneratedTask(
                f"{people} people attend a {minutes}-minute meeting. How many total person-hours are used?",
                answer,
                "decimal",
                "Multiply people by minutes, then divide by 60.",
                {"template": "person-hours"},
            )
        if branch == 1:
            start_hour = rng.randint(8, 15)
            start_minute = rng.choice((0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50))
            duration = rng.randint(18, 90 + level * 20)
            late = rng.randint(4, 10 + level * 5)
            answer = Decimal(max(0, duration - late))
            end_total = start_hour * 60 + start_minute + duration
            end_hour = (end_total // 60) % 24
            end_minute = end_total % 60
            return GeneratedTask(
                (
                    f"A call starts at {start_hour}:{start_minute:02d} and ends at {end_hour}:{end_minute:02d}. "
                    f"If someone joins {late} minutes late, how many minutes were they present?"
                ),
                answer,
                "integer",
                "Find the call duration, then subtract the late-arrival minutes.",
                {"template": "late-join"},
            )
        if branch == 2:
            total_hours = Decimal(rng.randint(6 + level, 20 + level * 8))
            answer = one_decimal(total_hours * Decimal(2) / Decimal(3))
            return GeneratedTask(
                (
                    f"A project has {total_hours} hours of work. One coworker works twice as fast as another, "
                    "so they take two shares of every three. How many work-hours should the faster coworker take?"
                ),
                answer,
                "decimal",
                "Split the work in a 2-to-1 ratio; the faster coworker takes 2/3 of the work.",
                {"template": "work-ratio"},
            )
        tasks = rng.randint(12, 40 + level * 20)
        minutes_each = rng.choice((3, 4, 5, 6, 8, 10, 12))
        people = rng.randint(2, 4 + level)
        answer = one_decimal(Decimal(tasks * minutes_each) / Decimal(60 * people))
        return GeneratedTask(
            f"{tasks} updates each take {minutes_each} minutes. Split evenly among {people} coworkers, how many hours per coworker?",
            answer,
            "decimal",
            "Find total minutes, divide by coworkers, then convert minutes to hours.",
            {"template": "task-division"},
        )


class CommuteCosts:
    def generate(self, difficulty: Difficulty, rng: random.Random) -> GeneratedTask:
        level = level_for(difficulty)
        branch = rng.randrange(3)
        if branch == 0:
            miles_one_way = rng.randint(2 + level, 15 + level * 9)
            days = rng.randint(3, 6)
            mpg = rng.randint(18, 40)
            gas = cents(rng.randint(280, 620))
            answer = money(Decimal(miles_one_way * 2 * days) / Decimal(mpg) * gas)
            return GeneratedTask(
                (
                    f"Gas is ${gas:.2f}/gallon, your car gets {mpg} mpg, and your one-way commute is "
                    f"{miles_one_way} miles for {days} days. What is the weekly fuel cost?"
                ),
                answer,
                "currency",
                "Use round-trip miles, multiply by days, divide by mpg, then multiply by gas price.",
                {"template": "fuel-weekly"},
            )
        if branch == 1:
            daily_parking = Decimal(rng.randint(4, 10 + level * 5))
            workdays = rng.randint(12, 22)
            parking_total = daily_parking * Decimal(workdays)
            transit_pass = Decimal(rng.randint(20, max(25, int(parking_total) - 5)))
            answer = money(parking_total - transit_pass)
            return GeneratedTask(
                (
                    f"Parking costs ${daily_parking:.2f} per workday for {workdays} days. "
                    f"A transit pass costs ${transit_pass:.2f}. How much cheaper is the pass?"
                ),
                answer,
                "currency",
                "Compare the monthly parking total with the pass cost.",
                {"template": "parking-vs-transit"},
            )
        minutes_one_way = rng.randint(8 + level * 2, 45 + level * 10)
        days = rng.randint(3, 6)
        weeks = rng.randint(20, 52)
        answer = one_decimal(Decimal(minutes_one_way * 2 * days * weeks) / Decimal(60))
        return GeneratedTask(
            (
                f"A one-way commute takes {minutes_one_way} minutes, {days} days each week, for {weeks} weeks. "
                "How many hours are spent commuting?"
            ),
            answer,
            "decimal",
            "Use round-trip minutes, multiply by days and weeks, then divide by 60.",
            {"template": "commute-time"},
        )


class BuildMeasure:
    def generate(self, difficulty: Difficulty, rng: random.Random) -> GeneratedTask:
        level = level_for(difficulty)
        branch = rng.randrange(3)
        if branch == 0:
            width = rng.randint(8, 12 + level * 4)
            height = rng.randint(7, 10 + level * 3)
            walls = rng.randint(1, 4)
            coats = 1 if level == 1 else rng.choice((1, 2))
            coverage = rng.choice((250, 300, 350, 400))
            answer = Decimal(math.ceil(width * height * walls * coats / coverage))
            return GeneratedTask(
                (
                    f"{walls} wall(s) are {width} ft by {height} ft. Paint covers {coverage} sq ft per gallon "
                    f"and you need {coats} coat(s). How many gallons should you buy?"
                ),
                answer,
                "integer",
                "Calculate total paint area, include coats, divide by coverage, then round up.",
                {"template": "paint"},
            )
        if branch == 1:
            length = rng.randint(8, 14 + level * 5)
            width = rng.randint(7, 12 + level * 4)
            tile_side_inches = rng.choice((6, 8, 12, 16, 18, 24))
            waste = rng.choice((5, 10, 12, 15))
            room_sqft = Decimal(length * width)
            tile_sqft = Decimal(tile_side_inches * tile_side_inches) / Decimal(144)
            answer = Decimal(
                math.ceil(float(room_sqft / tile_sqft * Decimal(100 + waste) / Decimal(100)))
            )
            return GeneratedTask(
                (
                    f"A room is {length} ft by {width} ft. Tiles are {tile_side_inches}-inch squares. "
                    f"With {waste}% extra for cuts, how many tiles are needed?"
                ),
                answer,
                "integer",
                "Find room area, divide by tile area, add waste, then round up.",
                {"template": "flooring", "waste": waste},
            )
        load = rng.randint(35 + level * 10, 160 + level * 45)
        bracket_limit = rng.choice((20, 25, 30, 40, 50, 60))
        safety = Decimal(rng.choice((12, 15, 20))) / Decimal(10)
        answer = Decimal(math.ceil(Decimal(load) * safety / Decimal(bracket_limit)))
        return GeneratedTask(
            (
                f"A shelf will hold {load} lb. Each bracket is rated for {bracket_limit} lb. "
                f"Using a {safety}x safety margin, how many brackets are needed?"
            ),
            answer,
            "integer",
            "Multiply the load by the safety margin, divide by bracket rating, then round up.",
            {"template": "safety-margin", "safety": float(safety)},
        )


class HealthScience:
    def generate(self, difficulty: Difficulty, rng: random.Random) -> GeneratedTask:
        level = level_for(difficulty)
        branch = rng.randrange(4)
        if branch == 0:
            goal = rng.choice((6000, 7500, 8000, 10000, 12000))
            completed = rng.randint(8, 75 + level * 5) * 100
            completed = min(completed, goal - 500)
            answer = Decimal(goal - completed)
            return GeneratedTask(
                f"Your step goal is {goal:,}. You have walked {completed:,} steps. How many steps remain?",
                answer,
                "integer",
                "Subtract the steps already done from the goal.",
                {"template": "steps"},
            )
        if branch == 1:
            serving_cups = Decimal(rng.choice(("0.5", "0.75", "1", "1.25")))
            sugar = Decimal(rng.randint(4, 18 + level * 3))
            target_cups = Decimal(rng.choice(("1", "1.5", "2", "2.5", "3")))
            answer = one_decimal(sugar * target_cups / serving_cups)
            return GeneratedTask(
                f"A nutrition label says {serving_cups} cup has {sugar} g sugar. How many grams are in {target_cups} cups?",
                answer,
                "decimal",
                "Find sugar per cup, then multiply by the cups eaten.",
                {"template": "nutrition-label"},
            )
        if branch == 2:
            bedtime_hour = rng.randint(20, 23)
            bedtime_min = rng.choice((0, 15, 30, 45))
            wake_hour = rng.randint(5, 8)
            wake_min = rng.choice((0, 15, 30, 45))
            bedtime_total = bedtime_hour * 60 + bedtime_min
            wake_total = wake_hour * 60 + wake_min + 24 * 60
            answer = Decimal(wake_total - bedtime_total)
            return GeneratedTask(
                f"Bedtime is {bedtime_hour}:{bedtime_min:02d} and wake-up is {wake_hour}:{wake_min:02d}. How many minutes of sleep is that?",
                answer,
                "integer",
                "Count from bedtime to midnight, then add the minutes from midnight to wake-up.",
                {"template": "sleep-minutes"},
            )
        age = rng.randint(10, 85)
        percent = rng.choice((50, 60, 65, 70, 75, 80))
        max_hr = 220 - age
        answer = Decimal(round(max_hr * percent / 100))
        return GeneratedTask(
            (
                f"Using the rough estimate max heart rate = 220 - age, what is {percent}% of max "
                f"for someone age {age}? This is practice math, not medical advice."
            ),
            answer,
            "integer",
            "Estimate max heart rate first, then multiply by the percent.",
            {"template": "heart-rate-zone", "medical_disclaimer": True},
        )


class RecipeScaling:
    def generate(self, difficulty: Difficulty, rng: random.Random) -> GeneratedTask:
        level = level_for(difficulty)
        branch = rng.randrange(3)
        if branch == 0:
            base_servings = rng.choice((4, 6, 8, 10, 12))
            target_servings = rng.randint(2 + level, 18 + level * 4)
            cups = Decimal(rng.choice(("0.5", "0.75", "1", "1.5", "2", "2.5")))
            answer = one_decimal(cups * Decimal(target_servings) / Decimal(base_servings))
            return GeneratedTask(
                (
                    f"A recipe for {base_servings} servings uses {cups} cups of an ingredient. "
                    f"How many cups are needed for {target_servings} servings?"
                ),
                answer,
                "decimal",
                "Scale the ingredient by target servings divided by original servings.",
                {"template": "recipe-scale"},
            )
        if branch == 1:
            total_cost = cents(rng.randint(600, 4800 + level * 1200))
            servings = rng.randint(3 + level, 12 + level * 5)
            answer = money(total_cost / Decimal(servings))
            return GeneratedTask(
                f"A batch costs ${total_cost:.2f} and makes {servings} servings. What is the cost per serving?",
                answer,
                "currency",
                "Divide total cost by servings.",
                {"template": "cost-per-serving"},
            )
        people = rng.randint(3, 10 + level * 3)
        slices_per_person = rng.randint(1, 3 + level)
        slices_per_pan = rng.choice((6, 8, 10, 12))
        answer = Decimal(math.ceil(people * slices_per_person / slices_per_pan))
        return GeneratedTask(
            f"{people} people each need {slices_per_person} slices. Each pan gives {slices_per_pan} slices. How many pans are needed?",
            answer,
            "integer",
            "Find total slices needed, then round up by slices per pan.",
            {"template": "serving-count"},
        )


class HomeUtilities:
    def generate(self, difficulty: Difficulty, rng: random.Random) -> GeneratedTask:
        level = level_for(difficulty)
        branch = rng.randrange(3)
        if branch == 0:
            watts = rng.choice((60, 75, 100, 150, 250, 500, 800, 1000, 1500))
            hours = rng.randint(1 + level, 8 + level * 4)
            rate = cents(rng.randint(10, 34))
            kwh = Decimal(watts * hours) / Decimal(1000)
            answer = money(kwh * rate)
            return GeneratedTask(
                f"An appliance uses {watts} watts for {hours} hours. Electricity is ${rate:.2f}/kWh. What is the cost?",
                answer,
                "currency",
                "Convert watts to kilowatts, multiply by hours, then by the kWh price.",
                {"template": "electricity"},
            )
        if branch == 1:
            gallons_per_min = Decimal(rng.randint(15, 35 + level * 4)) / Decimal(10)
            minutes = rng.randint(4 + level, 18 + level * 4)
            people = rng.randint(1, 2 + level)
            answer = one_decimal(gallons_per_min * Decimal(minutes * people))
            return GeneratedTask(
                f"A shower uses {gallons_per_min} gallons per minute. {people} person/people shower for {minutes} minutes. How many gallons are used?",
                answer,
                "decimal",
                "Multiply gallons per minute by minutes and by people.",
                {"template": "water-use"},
            )
        monthly = Decimal(rng.randint(45, 220 + level * 50))
        increase = rng.choice((5, 8, 10, 12, 15, 18))
        answer = money(monthly * Decimal(100 + increase) / Decimal(100))
        return GeneratedTask(
            f"A utility bill is ${monthly:.2f} and rises by {increase}%. What is the new bill?",
            answer,
            "currency",
            "Find the percent increase and add it to the original bill.",
            {"template": "bill-increase"},
        )


class QuickEstimates:
    def generate(self, difficulty: Difficulty, rng: random.Random) -> GeneratedTask:
        level = level_for(difficulty)
        branch = rng.randrange(3)
        if branch == 0:
            diameter_a = rng.choice((10, 12, 14, 16, 18, 20))
            diameter_b = rng.choice((8, 10, 12, 14))
            count_b = rng.choice((2, 3))
            area_a = Decimal(diameter_a * diameter_a)
            area_b = Decimal(count_b * diameter_b * diameter_b)
            best = 1 if area_a > area_b else 2
            return GeneratedTask(
                (
                    f"Which gives more pizza: Option 1, one {diameter_a}-inch pizza, or Option 2, "
                    f"{count_b} pizzas that are {diameter_b} inches each? Enter 1 or 2."
                ),
                Decimal(best),
                "choice",
                "Pizza area is proportional to diameter squared, so compare squared diameters times count.",
                {"template": "pizza-area"},
            )
        if branch == 1:
            options = rng.randint(8 + level * 4, 60 + level * 12)
            answer = Decimal(max(1, round(options * 0.37)))
            return GeneratedTask(
                (
                    f"You can inspect {options} apartments one at a time and cannot go back. "
                    "Using the rough 37% rule, how many should you sample before choosing the next best one?"
                ),
                answer,
                "integer",
                "Multiply the total options by 0.37 and round to a practical whole number.",
                {"template": "optimal-stopping"},
            )
        people = rng.randint(1, 6 + level)
        gallons_per_day = rng.randint(35, 95 + level * 15)
        days = rng.choice((30, 90, 180, 365))
        answer = Decimal(people * gallons_per_day * days)
        return GeneratedTask(
            f"Estimate water use: {people} people use about {gallons_per_day} gallons each per day for {days} days. How many gallons total?",
            answer,
            "integer",
            "Multiply people by gallons per person per day, then by days.",
            {"template": "fermi-water"},
        )


ACTIVITIES = (
    ActivitySpec("shopping-value", "Shopping Value", "Compare packages, offers, and real checkout value.", "Shopping & Purchases", "cart", "blue", ShoppingValue(), 125000),
    ActivitySpec("discounts-change", "Discounts & Change", "Handle sales, tax, cash, and receipt checks.", "Everyday Purchases", "receipt", "orange", DiscountsChange(), 110000),
    ActivitySpec("budget-planner", "Budget Planner", "Plan daily spending, savings goals, and flexible budgets.", "Money Saving", "piggy", "teal", BudgetPlanner(), 100000),
    ActivitySpec("interest-credit", "Interest & Credit", "Reason about savings growth, APR, and monthly balances.", "Financing", "credit", "purple", InterestCredit(), 105000),
    ActivitySpec("housing-real-estate", "Housing Math", "Estimate rent, property tax, commissions, and space needs.", "Real Estate", "home", "vermillion", HousingRealEstate(), 130000),
    ActivitySpec("office-meetings", "Meeting Math", "Calculate time, effort, person-hours, and task splits.", "Office & Meetings", "meeting", "sky", OfficeMeetings(), 115000),
    ActivitySpec("commute-costs", "Commute Costs", "Compare fuel, parking, transit, and travel time.", "Travel & Commute", "car", "blue", CommuteCosts(), 100000),
    ActivitySpec("build-measure", "Build & Measure", "Estimate paint, tile, materials, and safety margins.", "Engineering & DIY", "tools", "teal", BuildMeasure(), 100000),
    ActivitySpec("health-science", "Health Science", "Practice steps, sleep, nutrition labels, and body-data math.", "Health & Science", "health", "purple", HealthScience(), 100000),
    ActivitySpec("recipe-scaling", "Recipe Scaling", "Scale ingredients, servings, and cost per portion.", "Food & Cooking", "recipe", "orange", RecipeScaling(), 100000),
    ActivitySpec("home-utilities", "Home Utilities", "Estimate electricity, water, and household bill changes.", "Home Management", "utilities", "sky", HomeUtilities(), 100000),
    ActivitySpec("quick-estimates", "Quick Estimates", "Use back-of-envelope math for real decisions.", "Estimation", "estimate", "vermillion", QuickEstimates(), 100000),
)

ACTIVITY_BY_ID = {activity.id: activity for activity in ACTIVITIES}

LEGACY_ACTIVITY_ALIASES = {
    "equation-quest": "office-meetings",
    "pattern-detective": "quick-estimates",
    "prime-detective": "quick-estimates",
    "geometry-studio": "build-measure",
    "number-sprint": "office-meetings",
    "times-tables": "recipe-scaling",
    "division-builder": "budget-planner",
    "percent-lab": "discounts-change",
    "money-math": "discounts-change",
    "shared-budget": "budget-planner",
    "best-buy": "shopping-value",
    "savings-growth": "interest-credit",
}


def normalize_activity_id(activity_id: str) -> str | None:
    if activity_id in ACTIVITY_BY_ID:
        return activity_id
    return LEGACY_ACTIVITY_ALIASES.get(activity_id)


def list_activities() -> tuple[ActivitySpec, ...]:
    return ACTIVITIES


def get_activity(activity_id: str) -> ActivitySpec | None:
    normalized = normalize_activity_id(activity_id)
    if normalized is None:
        return None
    return ACTIVITY_BY_ID[normalized]
