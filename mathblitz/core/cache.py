"""Cache ports and Redis/in-memory implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
import json
import threading
import time
from typing import Any


class Cache(ABC):
    """Minimal cache interface used by application services."""

    backend_name = "unknown"

    @abstractmethod
    def get_json(self, key: str) -> Any | None:
        raise NotImplementedError

    @abstractmethod
    def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, *keys: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def increment(self, key: str, ttl_seconds: int) -> int:
        raise NotImplementedError

    def status(self) -> str:
        return "available"


class MemoryCache(Cache):
    """Thread-safe local fallback for development and test runs."""

    backend_name = "memory"

    def __init__(self) -> None:
        self._entries: dict[str, tuple[float, str]] = {}
        self._lock = threading.Lock()

    def _read(self, key: str) -> str | None:
        item = self._entries.get(key)
        if item is None:
            return None
        expires_at, value = item
        if expires_at <= time.time():
            self._entries.pop(key, None)
            return None
        return value

    def get_json(self, key: str) -> Any | None:
        with self._lock:
            value = self._read(key)
        return json.loads(value) if value is not None else None

    def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        with self._lock:
            self._entries[key] = (
                time.time() + ttl_seconds,
                json.dumps(value, separators=(",", ":")),
            )

    def delete(self, *keys: str) -> None:
        with self._lock:
            for key in keys:
                self._entries.pop(key, None)

    def increment(self, key: str, ttl_seconds: int) -> int:
        with self._lock:
            current = self._read(key)
            count = int(current) + 1 if current is not None else 1
            self._entries[key] = (time.time() + ttl_seconds, str(count))
            return count


class RedisCache(Cache):
    """Redis adapter for cross-instance caching and login throttling."""

    backend_name = "redis"

    def __init__(self, redis_url: str) -> None:
        from redis import Redis

        self._client = Redis.from_url(redis_url, decode_responses=True)

    def get_json(self, key: str) -> Any | None:
        value = self._client.get(key)
        return json.loads(value) if value is not None else None

    def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        self._client.setex(
            key, ttl_seconds, json.dumps(value, separators=(",", ":"))
        )

    def delete(self, *keys: str) -> None:
        if keys:
            self._client.delete(*keys)

    def increment(self, key: str, ttl_seconds: int) -> int:
        pipeline = self._client.pipeline()
        pipeline.incr(key)
        pipeline.expire(key, ttl_seconds)
        count, _ = pipeline.execute()
        return int(count)

    def status(self) -> str:
        try:
            return "available" if self._client.ping() else "unavailable"
        except Exception:
            return "unavailable"


def build_cache(redis_url: str | None) -> Cache:
    """Use Redis when configured and reachable, otherwise remain runnable locally."""

    if redis_url:
        try:
            cache = RedisCache(redis_url)
            if cache.status() == "available":
                return cache
        except Exception:
            pass
    return MemoryCache()
