"""Exercise the actual Uvicorn process over HTTP with an isolated database."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
import os
import secrets
import socket
import sqlite3
import subprocess
import sys
import time

import httpx
import pytest


ROOT = Path(__file__).resolve().parents[1]


class LiveServer:
    def __init__(self, directory: Path) -> None:
        self.database = directory / "live.db"
        self.log_path = directory / "server.log"
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            self.port = listener.getsockname()[1]
        self.url = f"http://127.0.0.1:{self.port}"
        self.environment = {
            **os.environ,
            "MATHBLITZ_DATABASE_URL": f"sqlite:///{self.database.as_posix()}",
            "MATHBLITZ_SECRET_KEY": secrets.token_urlsafe(48),
            "MATHBLITZ_REDIS_URL": "",
        }
        self.process = None
        self.log = None

    def start(self) -> None:
        self.log = self.log_path.open("a", encoding="utf-8")
        self.process = subprocess.Popen(
            [
                sys.executable, "-m", "uvicorn", "app:app",
                "--host", "127.0.0.1", "--port", str(self.port),
            ],
            cwd=ROOT,
            env=self.environment,
            stdout=self.log,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        deadline = time.monotonic() + 30
        with httpx.Client(base_url=self.url, timeout=0.5, trust_env=False) as probe:
            while time.monotonic() < deadline and self.process.poll() is None:
                try:
                    if probe.get("/api/v1/health").status_code == 200:
                        return
                except httpx.TransportError:
                    pass
                time.sleep(0.05)
        self.stop()
        raise AssertionError(self.log_path.read_text(encoding="utf-8"))

    def stop(self) -> None:
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=10)
        if self.log is not None:
            self.log.close()

    def answer_for(self, task_id: str) -> str:
        # This oracle is confined to the temporary test database, never a public API.
        with closing(sqlite3.connect(self.database)) as database:
            row = database.execute(
                "SELECT printf('%.2f', correct_answer) FROM task_sessions WHERE id = ?",
                (task_id,),
            ).fetchone()
        assert row is not None
        return row[0]


@pytest.fixture()
def live_server(tmp_path: Path):
    server = LiveServer(tmp_path)
    try:
        server.start()
        yield server
    finally:
        server.stop()


def test_live_journey_all_categories_levels_and_restart(live_server: LiveServer) -> None:
    with httpx.Client(base_url=live_server.url, timeout=10, trust_env=False) as client:
        health = client.get("/api/v1/health")
        assert health.json() == {
            "status": "ok", "cache_backend": "memory", "cache_status": "available"
        }
        for path, content_type in [
            ("/", "text/html"),
            ("/assets/app.js", "javascript"),
            ("/assets/styles.css", "text/css"),
            ("/openapi.json", "application/json"),
        ]:
            response = client.get(path)
            assert response.status_code == 200
            assert content_type in response.headers["content-type"]

        password = secrets.token_urlsafe(24)
        account = {"username": "LiveDemo", "password": password}
        registration = client.post("/api/v1/auth/register", json=account)
        assert registration.status_code == 201
        assert client.post("/api/v1/auth/register", json=account).status_code == 409
        assert client.post(
            "/api/v1/auth/login", json={**account, "password": "incorrect-password"}
        ).status_code == 401
        login = client.post(
            "/api/v1/auth/login", json={**account, "username": "livedemo"}
        )
        assert login.status_code == 200
        client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"
        for limit in [1, 5, 10, 100]:
            assert client.get(f"/api/v1/leaderboard?limit={limit}").json() == []

        catalog = client.get("/api/v1/activities").json()
        score = 0
        for activity in catalog["activities"]:
            for level in catalog["difficulties"]:
                response = client.post(
                    "/api/v1/tasks",
                    json={"activity_id": activity["id"], "difficulty": level["name"]},
                )
                assert response.status_code == 201
                task = response.json()
                assert "correct_answer" not in task and "context" not in task
                submitted = client.post(
                    f"/api/v1/tasks/{task['id']}/submissions",
                    json={"answer": live_server.answer_for(task["id"])},
                )
                assert submitted.status_code == 201
                assert submitted.json()["result_status"] == "correct"
                score += submitted.json()["points"]
                assert client.post(
                    f"/api/v1/tasks/{task['id']}/submissions", json={"answer": 0}
                ).status_code == 409

        dashboard = client.get("/api/v1/me/dashboard").json()
        assert dashboard["total_attempts"] == 60
        assert dashboard["correct_attempts"] == 60
        assert dashboard["score"] == score
        for limit in [1, 5, 10, 100]:
            assert client.get(f"/api/v1/leaderboard?limit={limit}").json()[0]["score"] == score

        preferences = {
            "default_activity_id": "health-science",
            "default_difficulty": "Very Easy",
            "sound_enabled": False,
        }
        assert client.patch("/api/v1/me/preferences", json=preferences).status_code == 200
        live_server.stop()
        live_server.start()
        assert client.get("/api/v1/me/preferences").json() == preferences
        assert client.get("/api/v1/me/dashboard").json()["score"] == score


def test_live_ownership_validation_and_concurrent_submission(live_server: LiveServer) -> None:
    with httpx.Client(base_url=live_server.url, timeout=15, trust_env=False) as client:
        password = secrets.token_urlsafe(24)
        owner = client.post(
            "/api/v1/auth/register", json={"username": "TaskOwner", "password": password}
        ).json()
        other = client.post(
            "/api/v1/auth/register", json={"username": "OtherUser", "password": password}
        ).json()
        headers = {"Authorization": f"Bearer {owner['access_token']}"}
        body = {"activity_id": "budget-planner", "difficulty": "Very Easy"}
        assert client.post("/api/v1/tasks", json=body).status_code == 401
        assert client.post(
            "/api/v1/tasks", json={**body, "difficulty": "Impossible"}, headers=headers
        ).status_code == 422
        assert client.post(
            "/api/v1/tasks", json={**body, "activity_id": "unknown"}, headers=headers
        ).status_code == 404
        task = client.post("/api/v1/tasks", json=body, headers=headers).json()
        endpoint = f"/api/v1/tasks/{task['id']}/submissions"
        assert client.post(
            endpoint, json={"answer": 0},
            headers={"Authorization": f"Bearer {other['access_token']}"},
        ).status_code == 404
        answer = live_server.answer_for(task["id"])

        def submit(_index: int) -> int:
            return client.post(endpoint, json={"answer": answer}, headers=headers).status_code

        with ThreadPoolExecutor(max_workers=8) as pool:
            statuses = list(pool.map(submit, range(8)))
        assert sorted(statuses) == [201] + [409] * 7
        dashboard = client.get("/api/v1/me/dashboard", headers=headers).json()
        assert dashboard["total_attempts"] == 1
