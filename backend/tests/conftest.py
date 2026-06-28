from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

import app.database.base  # noqa: F401 — registers all models with Base.metadata
from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.database.session import get_db
from app.features.users.model import User
from app.main import app
from app.shared.base_model import Base

# Derive the test database URL by appending _test to the configured database name.
# This keeps the test database isolated from the development database while
# reusing all other connection parameters (host, port, credentials).
_base_url = make_url(settings.DATABASE_URL)
_test_db_name = f"{_base_url.database}_test"
# Keep as URL objects — str(URL) masks the password with "***" in SQLAlchemy
# 2.0, which causes every connection to fail authentication.
_TEST_DATABASE_URL = _base_url.set(database=_test_db_name)


@pytest.fixture(scope="session")
def engine():
    """
    Create the test database (if absent) and all tables once per test session.
    Tables are dropped on teardown so the next run starts from a known state.
    """
    # AUTOCOMMIT is required — PostgreSQL cannot run CREATE DATABASE inside
    # a transaction.  We connect to the application database itself (not the
    # 'postgres' maintenance database) because we're only creating/dropping
    # `applytrack_test`, never `applytrack`.
    admin_engine = create_engine(
        _base_url,
        isolation_level="AUTOCOMMIT",
    )
    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": _test_db_name},
        ).fetchone()
        if not exists:
            # _test_db_name is derived from application config, not user input.
            conn.execute(text(f'CREATE DATABASE "{_test_db_name}"'))
    admin_engine.dispose()

    test_engine = create_engine(_TEST_DATABASE_URL)
    Base.metadata.create_all(test_engine)
    yield test_engine
    Base.metadata.drop_all(test_engine)
    test_engine.dispose()


@pytest.fixture
def db(engine) -> Generator[Session, None, None]:
    """
    Provide a database session that rolls back all writes after each test.

    Tests see their own flushed writes within the session, so assertions work
    normally.  Nothing is committed to the database, so no cleanup is needed
    between tests and each test starts with a clean slate.
    """
    TestSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = TestSession()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def test_user(db: Session) -> User:
    user = User(
        email=f"test-user-{uuid4()}@example.com",
        hashed_password=hash_password("StrongPass1"),
        full_name="Test User",
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


@pytest.fixture
def client(db: Session, test_user: User) -> Generator[TestClient, None, None]:
    """
    Provide a FastAPI TestClient wired to the test session.

    The get_db dependency is overridden so every request made through this
    client shares the same session as the test body.  This means data created
    in the test fixture is visible to the request handler without committing,
    and all changes are rolled back when the test ends.
    """

    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        test_client.headers.update(
            {"Authorization": f"Bearer {create_access_token(str(test_user.id))}"}
        )
        test_client.test_user = test_user  # type: ignore[attr-defined]
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def anonymous_client(db: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
