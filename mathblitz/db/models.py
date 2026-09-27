"""SQLAlchemy models representing durable MathBlitz state."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    Numeric,
    String,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


DIFFICULTY_VALUES = "'Very Easy','Easy','Medium','Hard','Extreme Hard'"


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    username: Mapped[str] = mapped_column(String(40), nullable=False)
    canonical_username: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now
    )

    preference: Mapped["UserPreference"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )


class UserPreference(Base):
    __tablename__ = "user_preferences"
    __table_args__ = (
        CheckConstraint(
            f"default_difficulty IN ({DIFFICULTY_VALUES})",
            name="ck_preferences_difficulty",
        ),
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    default_activity_id: Mapped[str] = mapped_column(
        String(50), nullable=False, default="shopping-value"
    )
    default_difficulty: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Medium"
    )
    sound_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )

    user: Mapped[User] = relationship(back_populates="preference")


class TaskSession(Base):
    __tablename__ = "task_sessions"
    __table_args__ = (
        CheckConstraint(
            f"difficulty IN ({DIFFICULTY_VALUES})", name="ck_task_difficulty"
        ),
        Index("ix_tasks_user_created", "user_id", "created_at"),
        Index("ix_tasks_expires", "expires_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    activity_id: Mapped[str] = mapped_column(String(50), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    prompt: Mapped[str] = mapped_column(String(500), nullable=False)
    hint: Mapped[str] = mapped_column(String(300), nullable=False)
    answer_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    correct_answer: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    context: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class Attempt(Base):
    __tablename__ = "attempts"
    __table_args__ = (
        CheckConstraint(
            f"difficulty IN ({DIFFICULTY_VALUES})", name="ck_attempt_difficulty"
        ),
        CheckConstraint(
            "result_status IN ('correct','incorrect','timeout')",
            name="ck_attempt_status",
        ),
        Index("ix_attempts_user_submitted", "user_id", "submitted_at"),
        Index("ix_attempts_activity_difficulty", "activity_id", "difficulty"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    task_id: Mapped[str] = mapped_column(
        ForeignKey("task_sessions.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    activity_id: Mapped[str] = mapped_column(String(50), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    submitted_answer: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    result_status: Mapped[str] = mapped_column(String(20), nullable=False)
    points: Mapped[int] = mapped_column(nullable=False, default=0)
    duration_ms: Mapped[int] = mapped_column(nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now
    )
