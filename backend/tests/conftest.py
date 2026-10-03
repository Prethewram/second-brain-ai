"""Tests use an ephemeral database and never load application credentials."""

import os
from uuid import uuid4

# Settings are cached, so override credentials before application imports.
os.environ.update(
    DATABASE_URL="sqlite://",
    SECRET_KEY="test-only-secret-key",
    ALGORITHM="HS256",
    ACCESS_TOKEN_EXPIRE_MINUTES="30",
    GEMINI_API_KEY="test-only-key",
    AI_PROVIDER="gemini",
    ENABLE_DEV_ENDPOINTS="false",
)

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture
def db_session():
    from app.db.database import Base
    import app.models  # Register tables before creating the schema.

    postgres_url = os.environ.get("TEST_POSTGRES_URL")
    schema = None
    if postgres_url:
        url = make_url(postgres_url)
        if url.get_backend_name() != "postgresql" or not (url.database or "").endswith(
            "_test"
        ):
            pytest.fail(
                "TEST_POSTGRES_URL must be PostgreSQL with a database name ending in _test"
            )
        schema = "test_" + uuid4().hex
        engine = create_engine(url)
        with engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))

        @event.listens_for(engine, "checkout")
        def set_search_path(connection, *_):
            # Avoid placing SET inside a transaction that a later rollback clears.
            previous = connection.autocommit
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute(f'SET search_path TO "{schema}"')
            connection.autocommit = previous

    else:
        engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )

        @event.listens_for(engine, "connect")
        def enable_foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        if schema:
            with engine.begin() as connection:
                connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        engine.dispose()


@pytest.fixture(autouse=True)
def block_live_ai(monkeypatch):
    def blocked_chat(*args, **kwargs):
        raise AssertionError(
            "Live AI calls are forbidden in tests; inject a fake AI client."
        )

    try:
        from google.genai.models import Models
    except ImportError:
        return
    monkeypatch.setattr(Models, "generate_content", blocked_chat)


@pytest.fixture
def client(db_session):
    from fastapi.testclient import TestClient
    from app.db.session import get_db
    from app.main import app

    def override_db():
        yield db_session

    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)
