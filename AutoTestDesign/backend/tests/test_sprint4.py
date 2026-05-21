"""Sprint 4 integration tests — whitebox, oracle, optimize."""
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app

pytestmark = pytest.mark.asyncio

MOCK_TC_RESPONSE = {
    "test_cases": [
        {
            "title": "Valid registration with correct data",
            "preconditions": "System online",
            "input_data": {"username": "alice", "email": "alice@example.com"},
            "expected_result": "Account created, HTTP 201",
            "priority": "high",
        },
        {
            "title": "Registration fails with duplicate email",
            "preconditions": "alice@example.com already registered",
            "input_data": {"username": "bob", "email": "alice@example.com"},
            "expected_result": "HTTP 409 Conflict",
            "priority": "high",
        },
        {
            "title": "Registration with empty username",
            "preconditions": "None",
            "input_data": {"username": "", "email": "c@c.com"},
            "expected_result": "HTTP 422 Validation Error",
            "priority": "low",
        },
    ]
}

MOCK_MERMAID_RESPONSE = {
    "mermaid": (
        "stateDiagram-v2\n"
        "    [*] --> Unregistered\n"
        "    Unregistered --> Registered : submit valid form\n"
        "    Registered --> Active : verify email\n"
        "    Active --> [*] : account deleted"
    )
}

MOCK_ORACLE_RESPONSE = {
    "oracle": "HTTP 201 Created with body {id: uuid, username: 'alice'} and Location header"
}


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as c:
        yield c


@pytest.fixture
async def suite_and_req(client: AsyncClient):
    imp = await client.post("/api/v1/requirements/import", json={
        "source_type": "direct",
        "content": "Users can register and log in with username and email.",
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
    return req_id, resp.json()


# ─── FR 4.0  State Diagram ─────────────────────────────────────────────────

async def test_generate_state_diagram(client: AsyncClient, suite_and_req):
    req_id, _ = suite_and_req
    with patch(
        "app.core.llm.LLMClient.complete_json",
        new=AsyncMock(return_value=MOCK_MERMAID_RESPONSE),
    ):
        resp = await client.post(f"/api/v1/whitebox/requirements/{req_id}/state-diagram")
    assert resp.status_code == 200
    body = resp.json()
    assert body["req_id"] == req_id
    assert "stateDiagram-v2" in body["mermaid"]
    assert "Unregistered" in body["mermaid"]


async def test_get_state_diagram_after_generation(client: AsyncClient, suite_and_req):
    req_id, _ = suite_and_req
    with patch(
        "app.core.llm.LLMClient.complete_json",
        new=AsyncMock(return_value=MOCK_MERMAID_RESPONSE),
    ):
        await client.post(f"/api/v1/whitebox/requirements/{req_id}/state-diagram")

    get_resp = await client.get(f"/api/v1/whitebox/requirements/{req_id}/state-diagram")
    assert get_resp.status_code == 200
    assert "stateDiagram-v2" in get_resp.json()["mermaid"]


async def test_get_state_diagram_not_generated(client: AsyncClient, suite_and_req):
    req_id, _ = suite_and_req
    resp = await client.get(f"/api/v1/whitebox/requirements/{req_id}/state-diagram")
    assert resp.status_code == 404


async def test_generate_state_diagram_req_not_found(client: AsyncClient):
    resp = await client.post("/api/v1/whitebox/requirements/nonexistent/state-diagram")
    assert resp.status_code == 404


async def test_state_diagram_persisted_in_requirement(client: AsyncClient, suite_and_req):
    req_id, _ = suite_and_req
    with patch(
        "app.core.llm.LLMClient.complete_json",
        new=AsyncMock(return_value=MOCK_MERMAID_RESPONSE),
    ):
        await client.post(f"/api/v1/whitebox/requirements/{req_id}/state-diagram")

    req_resp = await client.get(f"/api/v1/requirements/{req_id}")
    assert "stateDiagram-v2" in req_resp.json()["state_diagram"]


# ─── FR 5.0  Test Oracle ──────────────────────────────────────────────────

async def test_generate_oracle_success(client: AsyncClient, suite_and_req):
    req_id, suite = suite_and_req
    suite_id = suite["id"]
    tc_ids = [tc["id"] for tc in suite["test_cases"]]

    with patch(
        "app.core.llm.LLMClient.complete_json",
        new=AsyncMock(return_value=MOCK_ORACLE_RESPONSE),
    ):
        resp = await client.post("/api/v1/testcases/generate-oracle", json={"tc_ids": tc_ids})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["results"]) == len(tc_ids)
    for result in body["results"]:
        assert "ai_oracle" in result
        assert result["ai_oracle"]
        assert "original_expected" in result


async def test_oracle_stored_on_testcase(client: AsyncClient, suite_and_req):
    _, suite = suite_and_req
    tc_id = suite["test_cases"][0]["id"]
    with patch(
        "app.core.llm.LLMClient.complete_json",
        new=AsyncMock(return_value=MOCK_ORACLE_RESPONSE),
    ):
        await client.post("/api/v1/testcases/generate-oracle", json={"tc_ids": [tc_id]})

    tc_resp = await client.get(f"/api/v1/testcases/{tc_id}")
    assert tc_resp.json()["ai_oracle"] is not None


async def test_oracle_not_found(client: AsyncClient):
    resp = await client.post("/api/v1/testcases/generate-oracle", json={"tc_ids": ["nonexistent-tc"]})
    assert resp.status_code == 404


# ─── FR 7.0  Suite Optimization ──────────────────────────────────────────

async def test_optimize_risk_based_returns_response(client: AsyncClient, suite_and_req):
    _, suite = suite_and_req
    suite_id = suite["id"]
    resp = await client.post("/api/v1/optimize", json={
        "suite_id": suite_id,
        "strategy": "risk_based",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["suite_id"] == suite_id
    assert body["strategy"] == "risk_based"
    assert isinstance(body["candidates"], list)
    assert body["total_cases"] >= 1
    assert body["removable_count"] == len(body["candidates"])


async def test_optimize_coverage_efficiency(client: AsyncClient, suite_and_req):
    _, suite = suite_and_req
    suite_id = suite["id"]
    resp = await client.post("/api/v1/optimize", json={
        "suite_id": suite_id,
        "strategy": "coverage_efficiency",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["strategy"] == "coverage_efficiency"
    assert isinstance(body["candidates"], list)


async def test_optimize_suite_not_found(client: AsyncClient):
    resp = await client.post("/api/v1/optimize", json={
        "suite_id": "nonexistent-suite",
        "strategy": "risk_based",
    })
    assert resp.status_code == 404


async def test_optimize_invalid_strategy(client: AsyncClient, suite_and_req):
    _, suite = suite_and_req
    resp = await client.post("/api/v1/optimize", json={
        "suite_id": suite["id"],
        "strategy": "invalid_strategy",
    })
    assert resp.status_code == 422
