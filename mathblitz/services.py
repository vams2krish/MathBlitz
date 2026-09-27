"""Application use cases orchestrating domain rules and repositories."""

from __future__ import annotations

from datetime import timedelta, timezone
from decimal import Decimal
import random
import re

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .core.cache import Cache
from .core.security import PasswordHasher, TokenService
from .db.models import Attempt, TaskSession, User, utc_now
from .db.repositories import AttemptRepository, TaskRepository, UserRepository
from .domain.activities import DEFAULT_ACTIVITY_ID, get_activity, list_activities, normalize_activity_id
from .domain.difficulty import Difficulty, PROFILES, profile_for
from .domain.scoring import answers_match, points_for_correct_answer


class ServiceError(Exception):
    status_code = 400


class NotFoundError(ServiceError):
    status_code = 404


class ConflictError(ServiceError):
    status_code = 409


class AuthenticationError(ServiceError):
    status_code = 401


class RateLimitError(ServiceError):
    status_code = 429


class ValidationError(ServiceError):
    status_code = 422


class AuthenticationService:
    def __init__(self, password_hasher: PasswordHasher, tokens: TokenService) -> None:
        self.password_hasher = password_hasher
        self.tokens = tokens

    def register(self, session: Session, username: str, password: str) -> User:
        cleaned = username.strip()
        if not re.fullmatch(r"[A-Za-z0-9_-]{3,40}", cleaned):
            raise ValidationError(
                "Username must use 3-40 letters, numbers, underscores, or hyphens."
            )
        if len(password) < 8:
            raise ValidationError("Password must contain at least 8 characters.")
        users = UserRepository(session)
        if users.by_username(cleaned):
            raise ConflictError("That username is already registered.")
        user = users.create(cleaned, self.password_hasher.hash(password))
        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            raise ConflictError("That username is already registered.") from exc
        return user

    def authenticate(self, session: Session, username: str, password: str) -> User:
        users = UserRepository(session)
        user = users.by_username(username.strip())
        if user is None:
            raise AuthenticationError("Invalid username or password.")
        verification = self.password_hasher.verify(password, user.password_hash)
        if not verification.valid:
            raise AuthenticationError("Invalid username or password.")
        if verification.requires_upgrade:
            users.update_password(user, self.password_hasher.hash(password))
            session.commit()
        return user

    def credentials(self, user: User) -> dict:
        access_token, expires_at = self.tokens.issue(user.id)
        return {
            "access_token": access_token,
            "expires_at": expires_at,
            "user": user,
        }


class CatalogService:
    @staticmethod
    def catalog() -> dict:
        return {
            "difficulties": [
                {
                    "name": profile.difficulty,
                    "time_limit_seconds": profile.time_limit_seconds,
                    "points_multiplier": profile.points_multiplier,
                    "description": profile.description,
                }
                for profile in PROFILES.values()
            ],
            "activities": [
                {
                    "id": activity.id,
                    "name": activity.name,
                    "description": activity.description,
                    "skill": activity.skill,
                    "icon": activity.icon,
                    "accent": activity.accent,
                    "variant_estimate": activity.variant_estimate,
                }
                for activity in list_activities()
            ],
        }


class PracticeService:
    def __init__(self, cache: Cache, cache_ttl_seconds: int) -> None:
        self.cache = cache
        self.cache_ttl_seconds = cache_ttl_seconds

    def issue_task(
        self,
        session: Session,
        user: User,
        activity_id: str,
        difficulty: Difficulty,
        rng: random.Random | None = None,
    ) -> dict:
        activity = get_activity(activity_id)
        if activity is None:
            raise NotFoundError("Activity not found.")
        profile = profile_for(difficulty)
        generated = activity.generator.generate(difficulty, rng or random.Random())
        now = utc_now()
        task = TaskSession(
            user_id=user.id,
            activity_id=activity.id,
            difficulty=difficulty.value,
            prompt=generated.prompt,
            hint=generated.hint,
            answer_mode=generated.answer_mode,
            correct_answer=generated.correct_answer,
            context=generated.context,
            created_at=now,
            expires_at=now + timedelta(seconds=profile.time_limit_seconds),
        )
        TaskRepository(session).add(task)
        session.commit()
        return {
            "id": task.id,
            "activity_id": activity.id,
            "activity_name": activity.name,
            "difficulty": difficulty,
            "prompt": task.prompt,
            "hint": task.hint,
            "answer_mode": task.answer_mode,
            "time_limit_seconds": profile.time_limit_seconds,
            "expires_at": task.expires_at.replace(tzinfo=timezone.utc),
        }

    def submit_answer(
        self, session: Session, user: User, task_id: str, submitted_answer: Decimal
    ) -> dict:
        tasks = TaskRepository(session)
        task = tasks.owned_task(task_id, user.id)
        if task is None:
            raise NotFoundError("Task not found.")
        if tasks.has_attempt(task.id):
            raise ConflictError("This task has already been submitted.")
        now = utc_now()
        elapsed_seconds = max(0.0, (now - task.created_at).total_seconds())
        timed_out = now >= task.expires_at
        is_correct = not timed_out and answers_match(
            Decimal(task.correct_answer), submitted_answer, task.answer_mode
        )
        status = "timeout" if timed_out else ("correct" if is_correct else "incorrect")
        difficulty = Difficulty(task.difficulty)
        points = points_for_correct_answer(difficulty, elapsed_seconds) if is_correct else 0
        attempt = Attempt(
            task_id=task.id,
            user_id=user.id,
            activity_id=task.activity_id,
            difficulty=task.difficulty,
            submitted_answer=submitted_answer,
            result_status=status,
            points=points,
            duration_ms=int(elapsed_seconds * 1000),
            submitted_at=now,
        )
        AttemptRepository(session).add(attempt)
        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            raise ConflictError("This task has already been submitted.") from exc
        self.cache.delete(f"dashboard:{user.id}", "leaderboard:10")
        return {
            "id": attempt.id,
            "task_id": task.id,
            "activity_id": task.activity_id,
            "difficulty": difficulty,
            "result_status": status,
            "submitted_answer": submitted_answer,
            "correct_answer": Decimal(task.correct_answer),
            "points": points,
            "duration_ms": attempt.duration_ms,
            "submitted_at": attempt.submitted_at.replace(tzinfo=timezone.utc),
        }

    def dashboard(self, session: Session, user: User) -> dict:
        cache_key = f"dashboard:{user.id}"
        cached = self.cache.get_json(cache_key)
        if cached is not None:
            return cached
        attempts = AttemptRepository(session)
        result = attempts.dashboard(user.id)
        result["recent_attempts"] = [
            {
                "activity_id": attempt.activity_id,
                "difficulty": attempt.difficulty,
                "result_status": attempt.result_status,
                "points": attempt.points,
                "submitted_at": attempt.submitted_at.replace(tzinfo=timezone.utc).isoformat(),
            }
            for attempt in attempts.recent(user.id)
        ]
        self.cache.set_json(cache_key, result, self.cache_ttl_seconds)
        return result

    def leaderboard(self, session: Session, limit: int = 10) -> list[dict]:
        key = f"leaderboard:{limit}"
        cached = self.cache.get_json(key)
        if cached is not None:
            return cached
        result = AttemptRepository(session).leaderboard(limit)
        self.cache.set_json(key, result, self.cache_ttl_seconds)
        return result


class PreferenceService:
    def __init__(self, cache: Cache) -> None:
        self.cache = cache

    def read(self, user: User) -> dict:
        preference = user.preference
        activity_id = normalize_activity_id(preference.default_activity_id) or DEFAULT_ACTIVITY_ID
        return {
            "default_activity_id": activity_id,
            "default_difficulty": preference.default_difficulty,
            "sound_enabled": preference.sound_enabled,
        }

    def update(
        self,
        session: Session,
        user: User,
        default_activity_id: str,
        default_difficulty: Difficulty,
        sound_enabled: bool,
    ) -> dict:
        if get_activity(default_activity_id) is None:
            raise NotFoundError("Activity not found.")
        preference = UserRepository(session).update_preferences(
            user, default_activity_id, default_difficulty.value, sound_enabled
        )
        session.commit()
        self.cache.delete(f"dashboard:{user.id}")
        return {
            "default_activity_id": preference.default_activity_id,
            "default_difficulty": preference.default_difficulty,
            "sound_enabled": preference.sound_enabled,
        }
