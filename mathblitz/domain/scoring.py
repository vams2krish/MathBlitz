"""Answer evaluation and score policy."""

from decimal import Decimal

from .difficulty import Difficulty, profile_for


def answers_match(expected: Decimal, submitted: Decimal, answer_mode: str) -> bool:
    tolerance = Decimal("0.01") if answer_mode in {"currency", "decimal"} else Decimal("0")
    return abs(expected - submitted) <= tolerance


def points_for_correct_answer(difficulty: Difficulty, elapsed_seconds: float) -> int:
    profile = profile_for(difficulty)
    base = 10 * profile.points_multiplier
    remaining_seconds = max(0.0, profile.time_limit_seconds - elapsed_seconds)
    speed_bonus = int(remaining_seconds // 5)
    return base + speed_bonus
