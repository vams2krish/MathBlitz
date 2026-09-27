"""Application composition root."""

from dataclasses import dataclass

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from ..db.session import build_engine, build_session_factory
from ..services import AuthenticationService, PracticeService, PreferenceService
from .cache import Cache, build_cache
from .security import PasswordHasher, TokenService
from .settings import Settings


@dataclass
class Container:
    settings: Settings
    engine: Engine
    sessions: sessionmaker[Session]
    cache: Cache
    authentication: AuthenticationService
    practice: PracticeService
    preferences: PreferenceService

    @classmethod
    def build(cls, settings: Settings, cache: Cache | None = None) -> "Container":
        engine = build_engine(settings.database_url)
        cache_backend = cache or build_cache(settings.redis_url)
        return cls(
            settings=settings,
            engine=engine,
            sessions=build_session_factory(engine),
            cache=cache_backend,
            authentication=AuthenticationService(
                PasswordHasher(),
                TokenService(settings.secret_key, settings.access_token_minutes),
            ),
            practice=PracticeService(cache_backend, settings.cache_ttl_seconds),
            preferences=PreferenceService(cache_backend),
        )
