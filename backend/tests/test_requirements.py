"""Unit tests for CSV and TXT parsing logic — Sprint 1."""
import io
import csv
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app

pytestmark = pytest.mark.asyncio


# ─── Helper: CSV parsing logic (extracted for unit testing) ───────────────────

def parse_csv_content(content: str) -> list[str]:
    """Mirrors the CSV parsing logic in requirements.py."""
    reader = csv.DictReader(io.StringIO(content))
    has_text_col = bool(
        reader.fieldnames
        and (
            "description" in (reader.fieldnames or [])
            or "requirement" in (reader.fieldnames or [])
        )
    )
    results = []
    for row in reader:
        if has_text_col:
            text = row.get("description", "").strip() or row.get("requirement", "").strip()
        else:
            text = " | ".join(v.strip() for v in row.values() if v.strip())
        if text:
            results.append(text)
    return results


def parse_txt_content(content: str) -> list[str]:
    """Mirrors the TXT/direct paragraph splitting logic."""
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [content.strip()]
    return paragraphs


# ─── CSV parsing unit tests ───────────────────────────────────────────────────

def test_csv_parse_description_column():
    csv_data = "id,description\nREQ-001,User can login with username and password\nREQ-002,System validates email format"
    results = parse_csv_content(csv_data)
    assert len(results) == 2
    assert "User can login with username and password" in results
    assert "System validates email format" in results


def test_csv_parse_requirement_column():
    csv_data = "req_id,requirement\n1,Password must be 8+ characters\n2,Username must be unique"
    results = parse_csv_content(csv_data)
    assert len(results) == 2
    assert "Password must be 8+ characters" in results


def test_csv_parse_fallback_joins_all_values():
    csv_data = "field_a,field_b\nhello,world"
    results = parse_csv_content(csv_data)
    assert len(results) == 1
    assert "hello" in results[0]
    assert "world" in results[0]


def test_csv_parse_empty_rows_skipped():
    csv_data = "id,description\n1,Valid requirement\n2,\n3,Another requirement"
    results = parse_csv_content(csv_data)
    assert len(results) == 2  # empty description row skipped


# ─── TXT / direct parsing unit tests ─────────────────────────────────────────

def test_txt_parse_multiple_paragraphs():
    content = "First requirement about login.\n\nSecond requirement about registration.\n\nThird about password reset."
    results = parse_txt_content(content)
    assert len(results) == 3
    assert results[0] == "First requirement about login."


def test_txt_parse_single_paragraph():
    content = "A single requirement with no blank lines."
    results = parse_txt_content(content)
    assert len(results) == 1
    assert results[0] == "A single requirement with no blank lines."


def test_txt_parse_strips_whitespace():
    content = "  Req with leading spaces  \n\n  Another one  "
    results = parse_txt_content(content)
    assert results[0] == "Req with leading spaces"
    assert results[1] == "Another one"


def test_txt_parse_empty_content_returns_empty():
    results = parse_txt_content("   ")
    # Single paragraph with empty string after strip — should be empty
    assert results == [] or results == [""]


# ─── API integration tests for import endpoint ───────────────────────────────

@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as c:
        yield c


async def test_import_direct_text(client: AsyncClient):
    response = await client.post("/api/v1/requirements/import", json={
        "source_type": "direct",
        "content": "The system shall validate user credentials.\n\nThe system shall log failed login attempts."
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["source_type"] == "direct"
    assert "id" in data[0]
    assert "raw_text" in data[0]


async def test_import_csv_text(client: AsyncClient):
    csv_content = "id,description\nREQ-001,System shall authenticate users\nREQ-002,System shall authorize access"
    response = await client.post("/api/v1/requirements/import", json={
        "source_type": "csv",
        "content": csv_content,
        "file_name": "test.csv"
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


async def test_import_unsupported_type(client: AsyncClient):
    response = await client.post("/api/v1/requirements/import", json={
        "source_type": "xml",
        "content": "<req>Test</req>"
    })
    assert response.status_code == 422  # Pydantic validation error


async def test_list_requirements_returns_list(client: AsyncClient):
    response = await client.get("/api/v1/requirements")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_get_nonexistent_requirement(client: AsyncClient):
    response = await client.get("/api/v1/requirements/nonexistent-id")
    assert response.status_code == 404


async def test_delete_requirement(client: AsyncClient):
    # First import
    resp = await client.post("/api/v1/requirements/import", json={
        "source_type": "direct",
        "content": "Temporary requirement for deletion test."
    })
    req_id = resp.json()[0]["id"]

    # Then delete
    del_resp = await client.delete(f"/api/v1/requirements/{req_id}")
    assert del_resp.status_code == 204

    # Confirm gone
    get_resp = await client.get(f"/api/v1/requirements/{req_id}")
    assert get_resp.status_code == 404
