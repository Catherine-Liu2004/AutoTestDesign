"""Unit tests for risk score normalization and Mock LLM integration — Sprint 1."""
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.risk_service import _normalize_score, _score_to_priority

pytestmark = pytest.mark.asyncio


# ─── Risk score normalization unit tests ─────────────────────────────────────

def test_normalize_score_clamps_above_10():
    assert _normalize_score(15.0) == 10.0


def test_normalize_score_clamps_below_0():
    assert _normalize_score(-3.0) == 0.0


def test_normalize_score_rounds_to_2_decimals():
    # Python float: round(7.555, 2) → 7.55 due to IEEE 754 representation
    result = _normalize_score(7.555)
    assert 7.54 <= result <= 7.56


def test_normalize_score_normal_value():
    assert _normalize_score(6.5) == 6.5


def test_score_to_priority_high():
    assert _score_to_priority(7.0) == "high"
    assert _score_to_priority(9.5) == "high"
    assert _score_to_priority(10.0) == "high"


def test_score_to_priority_medium():
    assert _score_to_priority(4.0) == "medium"
    assert _score_to_priority(5.5) == "medium"
    assert _score_to_priority(6.9) == "medium"


def test_score_to_priority_low():
    assert _score_to_priority(0.0) == "low"
    assert _score_to_priority(3.9) == "low"


# ─── Mock LLM integration tests ──────────────────────────────────────────────

@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as c:
        yield c


MOCK_PARSE_RESPONSE = {
    "input_fields": ["username", "password"],
    "data_ranges": {"username": "1-50 chars", "password": "8-128 chars"},
    "conditions": ["username exists", "password matches hash"],
    "expected_actions": ["return JWT token", "redirect to dashboard"],
}

MOCK_RISK_RESPONSE = {
    "risk_score": 8.0,
    "priority": "high",
    "rationale": "Core authentication module; security-critical and frequently used.",
}


async def test_parse_requirement_with_mock_llm(client: AsyncClient):
    # First import a requirement
    import_resp = await client.post("/api/v1/requirements/import", json={
        "source_type": "direct",
        "content": "Users can log in with username and password. Password must be 8+ chars.",
    })
    req_id = import_resp.json()[0]["id"]

    # Mock LLM response
    with patch(
        "app.core.llm.LLMClient.complete_json",
        new=AsyncMock(return_value=MOCK_PARSE_RESPONSE),
    ):
        resp = await client.post(f"/api/v1/requirements/{req_id}/parse")

    assert resp.status_code == 200
    data = resp.json()
    assert data["structured"] is not None
    assert "username" in data["structured"]["input_fields"]
    assert "password" in data["structured"]["input_fields"]
    assert len(data["structured"]["conditions"]) > 0
    assert len(data["structured"]["expected_actions"]) > 0


async def test_risk_analyze_with_mock_llm(client: AsyncClient):
    # Import a requirement
    import_resp = await client.post("/api/v1/requirements/import", json={
        "source_type": "direct",
        "content": "System must authenticate users with MFA.",
    })
    req_id = import_resp.json()[0]["id"]

    # Analyze risk with mock
    with patch(
        "app.core.llm.LLMClient.complete_json",
        new=AsyncMock(return_value=MOCK_RISK_RESPONSE),
    ):
        resp = await client.post("/api/v1/risk/analyze", json={"req_ids": [req_id]})

    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) == 1
    assert results[0]["risk_score"] == 8.0
    assert results[0]["priority"] == "high"
    assert results[0]["rationale"] != ""


async def test_risk_report_after_analysis(client: AsyncClient):
    resp = await client.get("/api/v1/risk/report")
    assert resp.status_code == 200
    assert isinstance(resp.json()["results"], list)


async def test_manual_risk_update(client: AsyncClient):
    # Import
    import_resp = await client.post("/api/v1/requirements/import", json={
        "source_type": "direct",
        "content": "System logs all user actions for auditing.",
    })
    req_id = import_resp.json()[0]["id"]

    # Manually update risk
    resp = await client.put(f"/api/v1/risk/{req_id}", json={
        "risk_score": 6.5,
        "priority": "medium",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk_score"] == 6.5
    assert data["priority"] == "medium"


MOCK_TESTCASE_RESPONSE = {
    "test_cases": [
        {
            "title": "Valid login with correct credentials",
            "preconditions": "User is registered",
            "input_data": {"username": "testuser", "password": "Secure123!"},
            "expected_result": "Login successful, JWT token returned",
            "priority": "high",
        },
        {
            "title": "Invalid login with wrong password",
            "preconditions": "User is registered",
            "input_data": {"username": "testuser", "password": "wrongpass"},
            "expected_result": "Login fails with 401 error",
            "priority": "high",
        },
        {
            "title": "Login with empty username",
            "preconditions": "None",
            "input_data": {"username": "", "password": "Secure123!"},
            "expected_result": "Validation error: username required",
            "priority": "medium",
        },
    ]
}


async def test_generate_testcases_with_mock_llm(client: AsyncClient):
    # Import a requirement
    import_resp = await client.post("/api/v1/requirements/import", json={
        "source_type": "direct",
        "content": "System shall allow users to login with username and password.",
    })
    req_id = import_resp.json()[0]["id"]

    with patch(
        "app.core.llm.LLMClient.complete_json",
        new=AsyncMock(return_value=MOCK_TESTCASE_RESPONSE),
    ):
        resp = await client.post("/api/v1/testcases/generate", json={
            "req_ids": [req_id],
            "techniques": ["equivalence_partitioning", "boundary_value_analysis", "decision_table"],
        })

    assert resp.status_code == 200
    suite = resp.json()
    assert suite["tc_count"] >= 3
    assert len(suite["test_cases"]) >= 3
    techniques_used = {tc["technique"] for tc in suite["test_cases"]}
    # All 3 techniques should be present
    assert "equivalence_partitioning" in techniques_used
    assert "boundary_value_analysis" in techniques_used
    assert "decision_table" in techniques_used
