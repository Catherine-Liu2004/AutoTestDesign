"""
Detailed test-design execution suite for TodoApp.

This suite implements the assignment section 4 test cases for the selected
major module: task status finite-state machine (FSM), with supporting cases
for auth, task validation, limits, authorization and export risks.

Techniques covered:
- Black-box: Equivalence Partitioning, Boundary Value Analysis, Decision Table,
  State Transition Testing
- White-box: branch/condition/path-oriented tests against Flask route logic and
  the ALLOWED_TRANSITIONS implementation table
"""

from __future__ import annotations

import csv
import io
import os
import sys
from datetime import date, timedelta

import pytest


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app  # noqa: E402
from config import TestConfig  # noqa: E402
from models import ALLOWED_TRANSITIONS, Task, db  # noqa: E402


class ExecutionTestConfig(TestConfig):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    TESTING = True
    MAX_TASKS_PER_USER = 100


@pytest.fixture()
def client():
    app = create_app(ExecutionTestConfig)
    with app.app_context():
        db.drop_all()
        db.create_all()
    with app.test_client() as c:
        yield c
    with app.app_context():
        db.session.remove()
        db.drop_all()


def register(client, username="testuser", password="ValidPass123"):
    return client.post(
        "/api/auth/register", json={"username": username, "password": password}
    )


def login(client, username="testuser", password="ValidPass123"):
    return client.post("/api/auth/login", json={"username": username, "password": password})


@pytest.fixture()
def auth_headers(client):
    response = register(client)
    assert response.status_code == 201
    token = response.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}


def create_task(client, headers, **overrides):
    payload = {
        "title": "FSM test task",
        "description": "created by pytest",
        "priority": "medium",
        "due_date": (date.today() + timedelta(days=1)).isoformat(),
    }
    payload.update(overrides)
    return client.post("/api/tasks", headers=headers, json=payload)


def set_task_status_directly(app, task_id: int, status: str) -> None:
    """White-box helper: place a task into a specific FSM state."""
    with app.app_context():
        task = db.session.get(Task, task_id)
        task.status = status
        db.session.commit()


def test_health_check_smoke(client):
    response = client.get("/api/health")
    body = response.get_json()

    assert response.status_code == 200
    assert body["status"] == "ok"
    assert "timestamp" in body


@pytest.mark.parametrize(
    "username,password,expected_status,expected_key",
    [
        ("abc", "ValidPass123", 422, "error"),  # BVA: username below min 4
        ("abcd", "ValidPass123", 201, "token"),  # BVA: username min boundary
        ("a" * 20, "ValidPass123", 201, "token"),  # BVA: username max boundary
        ("a" * 21, "ValidPass123", 422, "error"),  # BVA: username above max
        ("bad-name", "ValidPass123", 422, "error"),  # EP: invalid chars
        ("validname", "short7", 422, "error"),  # BVA: password below min 8
        ("validname", "x" * 32, 201, "token"),  # BVA: password max boundary
        ("validname", "x" * 33, 422, "error"),  # BVA: password above max
    ],
)
def test_register_validation_ep_bva(client, username, password, expected_status, expected_key):
    response = register(client, username=username, password=password)
    body = response.get_json()

    assert response.status_code == expected_status
    assert expected_key in body


def test_duplicate_registration_is_rejected(client):
    assert register(client, username="dupeuser").status_code == 201
    response = register(client, username="dupeuser")

    assert response.status_code == 409
    assert response.get_json()["error"] == "Username already taken"


def test_login_lockout_decision_table_on_fifth_failure(client):
    register(client, username="lockuser", password="Correct123")

    for attempt in range(1, 5):
        response = login(client, username="lockuser", password="Wrong123")
        assert response.status_code == 401, f"attempt {attempt} should not lock yet"

    fifth = login(client, username="lockuser", password="Wrong123")
    assert fifth.status_code == 423
    assert fifth.get_json()["locked_minutes"] == 15

    locked_even_with_correct_password = login(
        client, username="lockuser", password="Correct123"
    )
    assert locked_even_with_correct_password.status_code == 423
    assert "locked_minutes_remaining" in locked_even_with_correct_password.get_json()


def test_successful_login_resets_failed_attempt_counter(client):
    register(client, username="resetuser", password="Correct123")

    for _ in range(4):
        assert login(client, username="resetuser", password="Wrong123").status_code == 401

    assert login(client, username="resetuser", password="Correct123").status_code == 200

    # If the counter was not reset, this single failure would lock the account.
    assert login(client, username="resetuser", password="WrongAgain123").status_code == 401


@pytest.mark.parametrize(
    "title,description,priority,due_offset,expected_status",
    [
        ("", "valid", "medium", 1, 422),  # BVA: title length 0
        ("x", "valid", "medium", 1, 201),  # BVA: title length 1
        ("x" * 100, "valid", "medium", 1, 201),  # BVA: title length 100
        ("x" * 101, "valid", "medium", 1, 422),  # BVA: title length 101
        ("valid", "d" * 500, "medium", 1, 201),  # BVA: desc max 500
        ("valid", "d" * 501, "medium", 1, 422),  # BVA: desc above max
        ("valid", "valid", "low", 1, 201),  # EP: valid priority low
        ("valid", "valid", "high", 1, 201),  # EP: valid priority high
        ("valid", "valid", "urgent", 1, 422),  # EP: invalid priority
        ("valid", "valid", "medium", -1, 422),  # BVA: yesterday
        ("valid", "valid", "medium", 0, 201),  # BVA: today accepted
    ],
)
def test_create_task_validation_ep_bva(
    client, auth_headers, title, description, priority, due_offset, expected_status
):
    response = create_task(
        client,
        auth_headers,
        title=title,
        description=description,
        priority=priority,
        due_date=(date.today() + timedelta(days=due_offset)).isoformat(),
    )

    assert response.status_code == expected_status


def test_create_task_rejects_more_than_100_tasks(client, auth_headers):
    for index in range(100):
        response = create_task(client, auth_headers, title=f"task-{index}")
        assert response.status_code == 201

    response = create_task(client, auth_headers, title="task-101")
    assert response.status_code == 422
    assert response.get_json()["error"] == "Task limit reached (100 max)"


@pytest.mark.parametrize(
    "current_status,next_status",
    [
        ("pending", "in_progress"),
        ("pending", "archived"),
        ("in_progress", "completed"),
        ("in_progress", "pending"),
        ("in_progress", "archived"),
        ("completed", "archived"),
    ],
)
def test_all_allowed_state_transitions(client, auth_headers, current_status, next_status):
    response = create_task(client, auth_headers)
    task_id = response.get_json()["task"]["id"]
    set_task_status_directly(client.application, task_id, current_status)

    transition = client.patch(
        f"/api/tasks/{task_id}/status", headers=auth_headers, json={"status": next_status}
    )

    assert transition.status_code == 200
    assert transition.get_json()["task"]["status"] == next_status


@pytest.mark.parametrize(
    "current_status,blocked_status",
    [
        ("pending", "completed"),
        ("completed", "pending"),
        ("completed", "in_progress"),
        ("archived", "pending"),
        ("archived", "in_progress"),
        ("archived", "completed"),
    ],
)
def test_forbidden_state_transitions_return_allowed_transitions(
    client, auth_headers, current_status, blocked_status
):
    response = create_task(client, auth_headers)
    task_id = response.get_json()["task"]["id"]
    set_task_status_directly(client.application, task_id, current_status)

    transition = client.patch(
        f"/api/tasks/{task_id}/status",
        headers=auth_headers,
        json={"status": blocked_status},
    )

    body = transition.get_json()
    assert transition.status_code == 422
    assert body["current_status"] == current_status
    assert body["requested_status"] == blocked_status
    assert body["allowed_transitions"] == sorted(ALLOWED_TRANSITIONS[current_status])


def test_invalid_status_value_is_rejected(client, auth_headers):
    response = create_task(client, auth_headers)
    task_id = response.get_json()["task"]["id"]

    transition = client.patch(
        f"/api/tasks/{task_id}/status", headers=auth_headers, json={"status": "done"}
    )

    assert transition.status_code == 422
    assert "Invalid status" in transition.get_json()["error"]


def test_missing_status_field_is_rejected(client, auth_headers):
    response = create_task(client, auth_headers)
    task_id = response.get_json()["task"]["id"]

    transition = client.patch(f"/api/tasks/{task_id}/status", headers=auth_headers, json={})

    assert transition.status_code == 422
    assert transition.get_json()["error"] == "status field is required"


def test_task_access_is_isolated_between_users(client, auth_headers):
    task = create_task(client, auth_headers).get_json()["task"]
    register(client, username="otheruser", password="ValidPass123")
    other_token = login(client, username="otheruser", password="ValidPass123").get_json()["token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    response = client.get(f"/api/tasks/{task['id']}", headers=other_headers)

    assert response.status_code == 404
    assert response.get_json()["error"] == "Task not found"


def test_list_tasks_filters_and_rejects_invalid_filters(client, auth_headers):
    create_task(client, auth_headers, title="low pending", priority="low")
    high = create_task(client, auth_headers, title="high progress", priority="high").get_json()[
        "task"
    ]
    client.patch(
        f"/api/tasks/{high['id']}/status",
        headers=auth_headers,
        json={"status": "in_progress"},
    )

    filtered = client.get("/api/tasks?status=in_progress&priority=high", headers=auth_headers)
    invalid = client.get("/api/tasks?status=unknown", headers=auth_headers)

    assert filtered.status_code == 200
    assert filtered.get_json()["total"] == 1
    assert filtered.get_json()["tasks"][0]["title"] == "high progress"
    assert invalid.status_code == 422


def test_csv_export_contains_current_user_tasks_only_and_exposes_formula_risk(
    client, auth_headers
):
    dangerous_title = '=HYPERLINK("http://attacker.example","click")'
    create_task(client, auth_headers, title=dangerous_title, description="csv injection probe")

    register(client, username="csvother", password="ValidPass123")
    other_token = login(client, username="csvother", password="ValidPass123").get_json()["token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}
    create_task(client, other_headers, title="other user's task")

    response = client.get("/api/tasks/export?format=csv", headers=auth_headers)
    rows = list(csv.DictReader(io.StringIO(response.data.decode("utf-8"))))

    assert response.status_code == 200
    assert len(rows) == 1
    assert rows[0]["title"] == dangerous_title
    assert rows[0]["title"].startswith("=")  # documents current CSV injection risk
