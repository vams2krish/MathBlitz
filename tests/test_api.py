from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from mathblitz.db.models import TaskSession


def test_catalog_contains_simplified_levels_and_activities(client: TestClient) -> None:
    response = client.get("/api/v1/activities")
    assert response.status_code == 200
    body = response.json()
    assert [entry["name"] for entry in body["difficulties"]] == [
        "Very Easy",
        "Easy",
        "Medium",
        "Hard",
        "Extreme Hard",
    ]
    assert len(body["activities"]) == 12
    assert {entry["id"] for entry in body["activities"]} >= {
        "shopping-value",
        "budget-planner",
        "office-meetings",
        "health-science",
    }
    assert all(entry["icon"] and entry["accent"] for entry in body["activities"])
    assert all(entry["variant_estimate"] >= 10000 for entry in body["activities"])


def test_task_solution_is_private_until_single_submission(
    authorized_client: TestClient,
) -> None:
    cached_empty_dashboard = authorized_client.get("/api/v1/me/dashboard").json()
    assert cached_empty_dashboard["total_attempts"] == 0
    issue_response = authorized_client.post(
        "/api/v1/tasks",
        json={"activity_id": "shopping-value", "difficulty": "Medium"},
    )
    assert issue_response.status_code == 201
    issued = issue_response.json()
    assert "correct_answer" not in issued
    assert issued["expires_at"].endswith("Z")

    with authorized_client.app.state.container.sessions() as session:
        stored = session.get(TaskSession, issued["id"])
        answer = str(stored.correct_answer)

    submit_response = authorized_client.post(
        f"/api/v1/tasks/{issued['id']}/submissions",
        json={"answer": answer},
    )
    assert submit_response.status_code == 201
    result = submit_response.json()
    assert result["result_status"] == "correct"
    assert Decimal(str(result["correct_answer"])) == Decimal(answer)
    assert result["points"] > 0

    duplicate = authorized_client.post(
        f"/api/v1/tasks/{issued['id']}/submissions",
        json={"answer": answer},
    )
    assert duplicate.status_code == 409

    dashboard = authorized_client.get("/api/v1/me/dashboard").json()
    assert dashboard["total_attempts"] == 1
    assert dashboard["score"] == result["points"]
    assert dashboard["solved_today"] == 1
    leaderboard = authorized_client.get("/api/v1/leaderboard").json()
    assert leaderboard[0]["username"] == "focused_user"


def test_preferences_accept_extreme_hard(authorized_client: TestClient) -> None:
    response = authorized_client.patch(
        "/api/v1/me/preferences",
        json={
            "default_activity_id": "interest-credit",
            "default_difficulty": "Extreme Hard",
            "sound_enabled": False,
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "default_activity_id": "interest-credit",
        "default_difficulty": "Extreme Hard",
        "sound_enabled": False,
    }


def test_expired_task_records_timeout(authorized_client: TestClient) -> None:
    issued = authorized_client.post(
        "/api/v1/tasks",
        json={"activity_id": "office-meetings", "difficulty": "Very Easy"},
    ).json()
    with authorized_client.app.state.container.sessions() as session:
        stored = session.get(TaskSession, issued["id"])
        stored.expires_at = stored.created_at
        session.commit()
    response = authorized_client.post(
        f"/api/v1/tasks/{issued['id']}/submissions", json={"answer": 0}
    )
    assert response.status_code == 201
    assert response.json()["result_status"] == "timeout"
    assert response.json()["points"] == 0


def test_failed_login_is_rate_limited(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"username": "secure_user", "password": "correct-pass-123"},
    )
    for _ in range(5):
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "secure_user", "password": "wrong-pass"},
        )
        assert response.status_code == 401
    limited = client.post(
        "/api/v1/auth/login",
        json={"username": "secure_user", "password": "wrong-pass"},
    )
    assert limited.status_code == 429


def test_security_headers_are_applied(client: TestClient) -> None:
    response = client.get("/")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


@pytest.mark.parametrize("limit", [1, 5, 10, 100])
def test_submission_invalidates_every_leaderboard_limit(
    authorized_client: TestClient, limit: int
) -> None:
    endpoint = f"/api/v1/leaderboard?limit={limit}"
    assert authorized_client.get(endpoint).json() == []
    issued = authorized_client.post(
        "/api/v1/tasks",
        json={"activity_id": "budget-planner", "difficulty": "Very Easy"},
    ).json()
    with authorized_client.app.state.container.sessions() as session:
        answer = str(session.get(TaskSession, issued["id"]).correct_answer)
    result = authorized_client.post(
        f"/api/v1/tasks/{issued['id']}/submissions", json={"answer": answer}
    )
    assert result.status_code == 201
    assert authorized_client.get(endpoint).json()[0]["score"] == result.json()["points"]


def test_unknown_api_routes_return_json(client: TestClient) -> None:
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not found."}
