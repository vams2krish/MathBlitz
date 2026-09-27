"""Pydantic contracts exposed through the HTTP API."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from .domain.difficulty import Difficulty


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=40)
    password: str = Field(min_length=1, max_length=128)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: int
    user: "UserResponse"


class UserResponse(BaseModel):
    id: str
    username: str

    model_config = ConfigDict(from_attributes=True)


class DifficultyResponse(BaseModel):
    name: Difficulty
    time_limit_seconds: int
    points_multiplier: int
    description: str


class ActivityResponse(BaseModel):
    id: str
    name: str
    description: str
    skill: str
    icon: str
    accent: str
    variant_estimate: int


class CatalogResponse(BaseModel):
    difficulties: list[DifficultyResponse]
    activities: list[ActivityResponse]


class IssueTaskRequest(BaseModel):
    activity_id: str = Field(min_length=1, max_length=50)
    difficulty: Difficulty


class IssuedTaskResponse(BaseModel):
    id: str
    activity_id: str
    activity_name: str
    difficulty: Difficulty
    prompt: str
    hint: str
    answer_mode: str
    time_limit_seconds: int
    expires_at: datetime


class SubmitAnswerRequest(BaseModel):
    answer: Decimal


class AttemptResponse(BaseModel):
    id: str
    task_id: str
    activity_id: str
    difficulty: Difficulty
    result_status: str
    submitted_answer: Decimal
    correct_answer: Decimal
    points: int
    duration_ms: int
    submitted_at: datetime


class RecentAttemptResponse(BaseModel):
    activity_id: str
    difficulty: Difficulty
    result_status: str
    points: int
    submitted_at: datetime


class DashboardResponse(BaseModel):
    total_attempts: int
    score: int
    correct_attempts: int
    accuracy: float
    average_seconds: float
    streak: int
    solved_today: int
    recent_attempts: list[RecentAttemptResponse]


class PreferencesUpdateRequest(BaseModel):
    default_activity_id: str = Field(min_length=1, max_length=50)
    default_difficulty: Difficulty
    sound_enabled: bool = True


class PreferencesResponse(PreferencesUpdateRequest):
    pass


class LeaderboardEntryResponse(BaseModel):
    rank: int
    username: str
    score: int
    attempts: int
    accuracy: float


class HealthResponse(BaseModel):
    status: str
    cache_backend: str
    cache_status: str
