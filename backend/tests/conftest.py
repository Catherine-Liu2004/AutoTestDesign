"""
Pytest configuration for backend tests.

Uses an in-memory SQLite database so tests are isolated from the production DB,
and calls create_tables() so the schema exists before any request is made.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app as fastapi_app


# ─── In-memory database setup ────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite://"  # pure in-memory

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # all connections share one in-memory db
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True, scope="session")
def setup_test_db():
    """Create all tables once for the entire test session."""
    # Import models so metadata is populated before create_all
    import app.models.models  # noqa: F401
    Base.metadata.create_all(bind=test_engine)
    fastapi_app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=test_engine)
    fastapi_app.dependency_overrides.clear()
