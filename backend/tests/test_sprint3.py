"""Sprint 3 integration tests — structure editing, coverage, traceability, strategy update."""
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app

pytestmark = pytest.mark.asyncio

MOCK_TC_RESPONSE = {
    "test_cases": [
        {
            "title": "Valid login with correct credentials",
            "preconditions": "User is registered",
            "input_data": {"username": "alice", "password": "Secure@123"},
            "expected_result": "Login successful",
            "priority": "high",
        },
        {
            "title": "Login fails with invalid password",
            "preconditions": "User exists",
            "input_data": {"username": "alice", "password": "wrong"},
            "expected_result": "HTTP 401 Unauthorized",
            "priority": "high",
        },
    ]
}


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as c:
        yield c


@pytest.fixture
async def req_and_suite(client: AsyncClient):
    """Import a requirement and generate a test suite (mock LLM)."""
    imp = await client.post("/api/v1/requirements/import", json={
        "source_type": "direct",
        "content": "Users can register and log in with username and password.",
    })
    req_id = imp.json()[0]["id"]

    with patch(
        "app.core.llm.LLMClient.complete_json",
        new=AsyncMock(return_value=MOCK_TC_RESPONSE),
    ):
        resp = await client.post("/api/v1/testcases/generate", json={
            "req_ids": [req_id],
            "techniques": ["equivalence_partitioning", "boundary_value_analysis"],
        })
    suite = resp.json()
    return req_id, suite


# ─── US-3.2  Structure editing ─────────────────────────────────────────────

async def test_update_structure_success(client: AsyncClient, req_and_suite):
    req_id, _ = req_and_suite
    payload = {
        "input_fields": ["username", "password"],
        "data_ranges": {"username": "1-50 chars", "password": "8-128 chars"},
        "conditions": ["User is registered", "Password is correct"],
        "expected_actions": ["Return session token", "Redirect to dashboard"],
    }
    resp = await client.put(f"/api/v1/requirements/{req_id}/structure", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["structured"]["input_fields"] == ["username", "password"]
    assert body["structured"]["data_ranges"]["username"] == "1-50 chars"
    assert body["structured"]["conditions"] == ["User is registered", "Password is correct"]


async def test_update_structure_not_found(client: AsyncClient):
    resp = await client.put("/api/v1/requirements/nonexistent-req/structure", json={
        "input_fields": [], "data_ranges": {}, "conditions": [], "expected_actions": []
    })
    assert resp.status_code == 404


async def test_update_structure_persists(client: AsyncClient, req_and_suite):
    """Structure update is persisted and retrievable via GET."""
    req_id, _ = req_and_suite
    payload = {
        "input_fields": ["email"],
        "data_ranges": {"email": "RFC 5321 format"},
        "conditions": ["Email is unique"],
        "expected_actions": ["Create account"],
    }
    await client.put(f"/api/v1/requirements/{req_id}/structure", json=payload)
    get_resp = await client.get(f"/api/v1/requirements/{req_id}")
    assert get_resp.json()["structured"]["input_fields"] == ["email"]


# ─── US-3.4  Traceability matrix ──────────────────────────────────────────

async def test_traceability_returns_matrix(client: AsyncClient, req_and_suite):
    req_id, suite = req_and_suite
    suite_id = suite["id"]
    resp = await client.get(f"/api/v1/coverage/{suite_id}/traceability")
    assert resp.status_code == 200
    body = resp.json()
    assert body["suite_id"] == suite_id
    assert isinstance(body["matrix"], dict)
    # req_id should map to the generated test cases
    assert req_id in body["matrix"]
    assert len(body["matrix"][req_id]) >= 1


async def test_traceability_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/coverage/nonexistent-suite/traceability")
    assert resp.status_code == 404


async def test_traceability_tc_ids_match_generated(client: AsyncClient, req_and_suite):
    req_id, suite = req_and_suite
    suite_id = suite["id"]
    # Get all test cases for this suite
    tc_resp = await client.get("/api/v1/testcases", params={"suite_id": suite_id})
    tc_ids = {tc["id"] for tc in tc_resp.json()}

    # Check traceability
    trace_resp = await client.get(f"/api/v1/coverage/{suite_id}/traceability")
    matrix_ids = set()
    for ids in trace_resp.json()["matrix"].values():
        matrix_ids.update(ids)
    assert matrix_ids == tc_ids


# ─── US-3.5  Coverage strategy update ────────────────────────────────────

async def test_update_strategy_regenerates_cases(client: AsyncClient, req_and_suite):
    req_id, suite = req_and_suite
    suite_id = suite["id"]
    original_count = suite["tc_count"]

    new_mock = {
        "test_cases": [
            {
                "title": "Boundary: max password length",
                "preconditions": "System online",
                "input_data": {"password": "x" * 128},
                "expected_result": "Login successful",
                "priority": "medium",
            }
        ]
    }
    with patch(
        "app.core.llm.LLMClient.complete_json",
        new=AsyncMock(return_value=new_mock),
    ):
        resp = await client.put(f"/api/v1/coverage/{suite_id}/strategy", json={
            "techniques": ["boundary_value_analysis"]
        })
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == suite_id
    assert body["tc_count"] == 1  # new mock returns 1 case
    # Ensure test_cases in response matches
    assert len(body["test_cases"]) == 1
    assert "Boundary" in body["test_cases"][0]["title"]


async def test_update_strategy_not_found(client: AsyncClient):
    resp = await client.put("/api/v1/coverage/nonexistent-suite/strategy", json={
        "techniques": ["equivalence_partitioning"]
    })
    assert resp.status_code == 404


async def test_update_strategy_updates_suite_techniques(client: AsyncClient, req_and_suite):
    _, suite = req_and_suite
    suite_id = suite["id"]
    new_techs = ["decision_table"]
    new_mock = {
        "test_cases": [
            {
                "title": "DT: both inputs valid",
                "preconditions": "None",
                "input_data": {"a": 1, "b": 2},
                "expected_result": "Success",
                "priority": "low",
            }
        ]
    }
    with patch(
        "app.core.llm.LLMClient.complete_json",
        new=AsyncMock(return_value=new_mock),
    ):
        resp = await client.put(f"/api/v1/coverage/{suite_id}/strategy", json={"techniques": new_techs})
    assert resp.status_code == 200
    assert resp.json()["techniques"] == new_techs


# ─── Manual TestCase creation ──────────────────────────────────────────────

async def test_create_manual_testcase(client: AsyncClient, req_and_suite):
    req_id, suite = req_and_suite
    suite_id = suite["id"]
    resp = await client.post("/api/v1/testcases", json={
        "suite_id": suite_id,
        "req_id": req_id,
        "technique": "manual",
        "title": "Manual: check accessibility",
        "expected_result": "All WCAG 2.1 criteria met",
        "priority": "medium",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Manual: check accessibility"
    assert body["technique"] == "manual"
    assert body["status"] == "pending"


async def test_create_manual_testcase_suite_not_found(client: AsyncClient, req_and_suite):
    req_id, _ = req_and_suite
    resp = await client.post("/api/v1/testcases", json={
        "suite_id": "nonexistent-suite",
        "req_id": req_id,
        "technique": "manual",
        "title": "Should fail",
        "expected_result": "N/A",
    })
    assert resp.status_code == 404


# ─── List suites endpoint ─────────────────────────────────────────────────

async def test_list_test_suites(client: AsyncClient, req_and_suite):
    _, suite = req_and_suite
    resp = await client.get("/api/v1/testcases/suites")
    assert resp.status_code == 200
    ids = [s["id"] for s in resp.json()]
    assert suite["id"] in ids
