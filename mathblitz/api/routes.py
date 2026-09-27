"""Versioned REST API routes."""

from typing import Annotated

from fastapi import APIRouter, Query, Request, status
from sqlalchemy import text

from ..schemas import (
    AttemptResponse,
    AuthResponse,
    CatalogResponse,
    DashboardResponse,
    HealthResponse,
    IssuedTaskResponse,
    IssueTaskRequest,
    LeaderboardEntryResponse,
    LoginRequest,
    PreferencesResponse,
    PreferencesUpdateRequest,
    RegisterRequest,
    SubmitAnswerRequest,
)
from ..services import AuthenticationError, CatalogService, RateLimitError
from .dependencies import ContainerDependency, CurrentUser, SessionDependency


router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["operations"])
def health(container: ContainerDependency, session: SessionDependency) -> dict:
    session.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "cache_backend": container.cache.backend_name,
        "cache_status": container.cache.status(),
    }


@router.post(
    "/auth/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["authentication"],
)
def register(
    payload: RegisterRequest,
    container: ContainerDependency,
    session: SessionDependency,
) -> dict:
    user = container.authentication.register(session, payload.username, payload.password)
    return container.authentication.credentials(user)


@router.post("/auth/login", response_model=AuthResponse, tags=["authentication"])
def login(
    payload: LoginRequest,
    request: Request,
    container: ContainerDependency,
    session: SessionDependency,
) -> dict:
    ip_address = request.client.host if request.client else "unknown"
    throttle_key = f"login:{ip_address}:{payload.username.casefold()}"
    failures = container.cache.get_json(throttle_key) or 0
    if failures >= 5:
        raise RateLimitError("Too many login attempts. Retry in five minutes.")
    try:
        user = container.authentication.authenticate(
            session, payload.username, payload.password
        )
    except AuthenticationError:
        container.cache.increment(throttle_key, 300)
        raise
    container.cache.delete(throttle_key)
    return container.authentication.credentials(user)


@router.get("/activities", response_model=CatalogResponse, tags=["practice"])
def activities() -> dict:
    return CatalogService.catalog()


@router.post(
    "/tasks",
    response_model=IssuedTaskResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["practice"],
)
def issue_task(
    payload: IssueTaskRequest,
    user: CurrentUser,
    container: ContainerDependency,
    session: SessionDependency,
) -> dict:
    return container.practice.issue_task(
        session, user, payload.activity_id, payload.difficulty
    )


@router.post(
    "/tasks/{task_id}/submissions",
    response_model=AttemptResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["practice"],
)
def submit_answer(
    task_id: str,
    payload: SubmitAnswerRequest,
    user: CurrentUser,
    container: ContainerDependency,
    session: SessionDependency,
) -> dict:
    return container.practice.submit_answer(session, user, task_id, payload.answer)


@router.get("/me/dashboard", response_model=DashboardResponse, tags=["progress"])
def dashboard(
    user: CurrentUser, container: ContainerDependency, session: SessionDependency
) -> dict:
    return container.practice.dashboard(session, user)


@router.get("/me/preferences", response_model=PreferencesResponse, tags=["profile"])
def preferences(user: CurrentUser, container: ContainerDependency) -> dict:
    return container.preferences.read(user)


@router.patch("/me/preferences", response_model=PreferencesResponse, tags=["profile"])
def update_preferences(
    payload: PreferencesUpdateRequest,
    user: CurrentUser,
    container: ContainerDependency,
    session: SessionDependency,
) -> dict:
    return container.preferences.update(
        session,
        user,
        payload.default_activity_id,
        payload.default_difficulty,
        payload.sound_enabled,
    )


@router.get(
    "/leaderboard", response_model=list[LeaderboardEntryResponse], tags=["progress"]
)
def leaderboard(
    container: ContainerDependency,
    session: SessionDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> list[dict]:
    return container.practice.leaderboard(session, limit)
