"""Environment-backed application settings."""

from dataclasses import dataclass
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    """Runtime configuration with deployment-friendly defaults."""

    app_name: str = "MathBlitz"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./data/mathblitz.db"
    redis_url: str | None = None
    secret_key: str = "local-development-key-change-before-deploying"
    access_token_minutes: int = 480
    cache_ttl_seconds: int = 30
    frontend_dir: Path = BASE_DIR / "frontend"

    @classmethod
    def from_env(cls) -> "Settings":
        redis_url = os.getenv("MATHBLITZ_REDIS_URL") or None
        return cls(
            database_url=os.getenv(
                "MATHBLITZ_DATABASE_URL", "sqlite:///./data/mathblitz.db"
            ),
            redis_url=redis_url,
            secret_key=os.getenv(
                "MATHBLITZ_SECRET_KEY",
                "local-development-key-change-before-deploying",
            ),
            access_token_minutes=int(
                os.getenv("MATHBLITZ_ACCESS_TOKEN_MINUTES", "480")
            ),
            cache_ttl_seconds=int(os.getenv("MATHBLITZ_CACHE_TTL_SECONDS", "30")),
        )
