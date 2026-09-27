"""Repository adapters isolating application services from SQL queries."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import case, desc, func, select
from sqlalchemy.orm import Session

from .models import Attempt, TaskSession, User, UserPreference, utc_now
from ..domain.activities import DEFAULT_ACTIVITY_ID


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def by_id(self, user_id: str) -> User | None:
        return self.session.get(User, user_id)

    def by_username(self, username: str) -> User | None:
        statement = select(User).where(User.canonical_username == username.casefold())
        return self.session.scalar(statement)

    def create(self, username: str, password_hash: str) -> User:
        user = User(
            username=username.strip(),
            canonical_username=username.strip().casefold(),
            password_hash=password_hash,
        )
        user.preference = UserPreference(default_activity_id=DEFAULT_ACTIVITY_ID)
        self.session.add(user)
        self.session.flush()
        return user

    def update_password(self, user: User, password_hash: str) -> None:
        user.password_hash = password_hash
        self.session.add(user)

    def update_preferences(
        self,
        user: User,
        default_activity_id: str,
        default_difficulty: str,
        sound_enabled: bool,
    ) -> UserPreference:
        preference = user.preference or UserPreference(user_id=user.id)
        preference.default_activity_id = default_activity_id
        preference.default_difficulty = default_difficulty
        preference.sound_enabled = sound_enabled
        self.session.add(preference)
        return preference


class TaskRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, task: TaskSession) -> TaskSession:
        self.session.add(task)
        self.session.flush()
        return task

    def owned_task(self, task_id: str, user_id: str) -> TaskSession | None:
        statement = select(TaskSession).where(
            TaskSession.id == task_id, TaskSession.user_id == user_id
        )
        return self.session.scalar(statement)

    def has_attempt(self, task_id: str) -> bool:
        statement = select(Attempt.id).where(Attempt.task_id == task_id)
        return self.session.scalar(statement) is not None


class AttemptRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, attempt: Attempt) -> Attempt:
        self.session.add(attempt)
        self.session.flush()
        return attempt

    def recent(self, user_id: str, limit: int = 8) -> list[Attempt]:
        statement = (
            select(Attempt)
            .where(Attempt.user_id == user_id)
            .order_by(desc(Attempt.submitted_at))
            .limit(limit)
        )
        return list(self.session.scalars(statement))

    def dashboard(self, user_id: str) -> dict[str, Any]:
        statement = select(
            func.count(Attempt.id),
            func.coalesce(func.sum(Attempt.points), 0),
            func.coalesce(
                func.sum(case((Attempt.result_status == "correct", 1), else_=0)), 0
            ),
            func.coalesce(func.avg(Attempt.duration_ms), 0),
        ).where(Attempt.user_id == user_id)
        total, score, correct, average_ms = self.session.execute(statement).one()
        today_start = utc_now().replace(hour=0, minute=0, second=0, microsecond=0)
        solved_today = self.session.scalar(
            select(func.count(Attempt.id)).where(
                Attempt.user_id == user_id,
                Attempt.result_status == "correct",
                Attempt.submitted_at >= today_start,
            )
        )
        attempts = self.recent(user_id, 40)
        streak = 0
        for attempt in attempts:
            if attempt.result_status != "correct":
                break
            streak += 1
        accuracy = round((int(correct) / int(total) * 100), 1) if total else 0.0
        return {
            "total_attempts": int(total),
            "score": int(score),
            "correct_attempts": int(correct),
            "accuracy": accuracy,
            "average_seconds": round(float(average_ms) / 1000, 1),
            "streak": streak,
            "solved_today": int(solved_today or 0),
        }

    def leaderboard(self, limit: int) -> list[dict[str, Any]]:
        correct_count = func.coalesce(
            func.sum(case((Attempt.result_status == "correct", 1), else_=0)), 0
        )
        attempts_count = func.count(Attempt.id)
        total_score = func.coalesce(func.sum(Attempt.points), 0)
        statement = (
            select(User.username, total_score, attempts_count, correct_count)
            .join(Attempt, Attempt.user_id == User.id)
            .group_by(User.id, User.username)
            .order_by(desc(total_score), User.username)
            .limit(limit)
        )
        entries = []
        for rank, (username, score, attempts, correct) in enumerate(
            self.session.execute(statement), start=1
        ):
            entries.append(
                {
                    "rank": rank,
                    "username": username,
                    "score": int(score),
                    "attempts": int(attempts),
                    "accuracy": round(int(correct) / int(attempts) * 100, 1),
                }
            )
        return entries
