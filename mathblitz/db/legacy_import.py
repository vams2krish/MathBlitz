"""One-time import adapter for data created by the original file-based app."""

from __future__ import annotations

import csv
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path

from sqlalchemy.orm import Session

from .models import Attempt, TaskSession, UserPreference
from .repositories import AttemptRepository, TaskRepository, UserRepository


ACTIVITY_MAP = {
    "Cash Counting": "discounts-change",
    "Billing Calculation": "budget-planner",
    "Tip Calculator": "discounts-change",
    "Discount Calculator": "discounts-change",
    "Tax Calculator": "discounts-change",
    "Split Bill": "budget-planner",
    "Profit/Loss": "budget-planner",
    "Unit Price Compare": "shopping-value",
    "Percentage": "discounts-change",
    "Currency Convert": "shopping-value",
    "Simple Interest": "interest-credit",
    "Compound Interest": "interest-credit",
    "Multiplication": "recipe-scaling",
}


def normalized_difficulty(value: str) -> str:
    if value == "Very Hard":
        return "Extreme Hard"
    allowed = {"Very Easy", "Easy", "Medium", "Hard", "Extreme Hard"}
    return value if value in allowed else "Medium"


def import_legacy_dataset(session: Session, data_dir: Path) -> dict[str, int]:
    """Import users and their CSV attempts once, skipping existing users."""

    users_path = data_dir / "users.json"
    if not users_path.exists():
        return {"users": 0, "attempts": 0, "skipped_attempt_files": 0}
    users_source = json.loads(users_path.read_text(encoding="utf-8"))
    user_repository = UserRepository(session)
    task_repository = TaskRepository(session)
    attempt_repository = AttemptRepository(session)
    imported_users = 0
    imported_attempts = 0

    for username, legacy in users_source.items():
        if user_repository.by_username(username) is not None:
            continue
        user = user_repository.create(username, str(legacy["password"]))
        settings = legacy.get("settings", {})
        preference = user.preference or UserPreference(user_id=user.id)
        preference.default_activity_id = ACTIVITY_MAP.get(
            settings.get("default_exercise", ""), "shopping-value"
        )
        preference.default_difficulty = normalized_difficulty(
            settings.get("default_difficulty", "Medium")
        )
        preference.sound_enabled = bool(settings.get("sound_enabled", True))
        session.add(preference)
        imported_users += 1
        progress_path = data_dir / "progress" / f"{username}.csv"
        if not progress_path.exists():
            continue
        with progress_path.open("r", newline="", encoding="utf-8") as source:
            for row in csv.DictReader(source):
                try:
                    submitted = Decimal(row.get("UserAnswer", "0"))
                    answer = Decimal(row.get("CorrectAnswer", "0"))
                    submitted_at = datetime.fromisoformat(row["Timestamp"])
                    duration_ms = int(float(row.get("TimeTaken", 0)) * 1000)
                except (InvalidOperation, ValueError, KeyError):
                    continue
                difficulty = normalized_difficulty(row.get("Difficulty", "Medium"))
                activity_id = ACTIVITY_MAP.get(row.get("Exercise", ""), "office-meetings")
                task = TaskSession(
                    user_id=user.id,
                    activity_id=activity_id,
                    difficulty=difficulty,
                    prompt="Imported legacy task",
                    hint="Imported from the original MathBlitz dataset.",
                    answer_mode="decimal",
                    correct_answer=answer,
                    context={"legacy": True},
                    created_at=submitted_at - timedelta(milliseconds=duration_ms),
                    expires_at=submitted_at,
                )
                task_repository.add(task)
                legacy_status = row.get("Status", "Incorrect").casefold()
                result_status = (
                    "correct"
                    if legacy_status == "correct"
                    else ("timeout" if legacy_status == "timeout" else "incorrect")
                )
                attempt_repository.add(
                    Attempt(
                        task_id=task.id,
                        user_id=user.id,
                        activity_id=activity_id,
                        difficulty=difficulty,
                        submitted_answer=submitted,
                        result_status=result_status,
                        points=int(float(row.get("Points", 0))),
                        duration_ms=duration_ms,
                        submitted_at=submitted_at,
                    )
                )
                imported_attempts += 1

    session.commit()
    source_users = {name.casefold() for name in users_source}
    unmatched_progress = sum(
        1
        for path in (data_dir / "progress").glob("*.csv")
        if path.stem.casefold() not in source_users
    )
    return {
        "users": imported_users,
        "attempts": imported_attempts,
        "skipped_attempt_files": unmatched_progress,
    }
