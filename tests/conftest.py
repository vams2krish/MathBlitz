from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mathblitz.core.cache import MemoryCache
from mathblitz.core.settings import Settings
from mathblitz.main import create_app


@pytest.fixture()
def client(tmp_path: Path):
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        secret_key="test-secret-key",
        access_token_minutes=30,
        cache_ttl_seconds=60,
    )
    with TestClient(create_app(settings, MemoryCache())) as test_client:
        yield test_client


@pytest.fixture()
def authorized_client(client: TestClient):
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "focused_user", "password": "strong-pass-123"},
    )
    assert response.status_code == 201
    client.headers.update(
        {"Authorization": f"Bearer {response.json()['access_token']}"}
    )
    return client
