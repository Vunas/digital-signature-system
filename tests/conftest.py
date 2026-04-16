from __future__ import annotations

from typing import Generator
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.dependencies import get_current_user, get_db
from app.db.base import Base

# --- DATABASE & APP SETUP ---


@pytest.fixture(scope="session")
def sqlite_engine():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture()
def db_session(sqlite_engine) -> Generator[Session, None, None]:
    connection = sqlite_engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=connection
    )
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def override_get_db(db_session: Session):
    def _override() -> Generator[Session, None, None]:
        yield db_session

    return _override


@pytest.fixture()
def fastapi_app_full(override_get_db) -> FastAPI:
    from app.routers import auth_router, signature_router, verify_router, key_router

    app = FastAPI()
    app.include_router(auth_router.router)
    app.include_router(signature_router.router)
    app.include_router(verify_router.router)
    app.include_router(key_router.router)
    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.fixture()
def client_full(fastapi_app_full: FastAPI):
    # httpx warning is silenced via pytest.ini
    with TestClient(fastapi_app_full) as client:
        yield client


@pytest.fixture()
def override_current_user_full(fastapi_app_full: FastAPI):
    from app.models.user import User

    user = User(
        id=999, username="test_enterprise_user", password_hash="hash", is_active=True
    )

    def _override() -> User:
        return user

    fastapi_app_full.dependency_overrides[get_current_user] = _override
    return user


@pytest.fixture()
def mock_uow():
    """
    Generic Unit of Work test double for services that need commit/rollback checks.
    """

    class MockUnitOfWork:
        def __init__(self):
            self.committed = False
            self.rolled_back = False

        def commit(self):
            self.committed = True

        def rollback(self):
            self.rolled_back = True

    return MockUnitOfWork()


# --- MOCK FACTORIES (ENTERPRISE PATTERN) ---


@pytest.fixture()
def mock_sign_repos(monkeypatch):

    class RepoMocker:
        def __init__(self):
            # Default Dummy Data
            self.doc = SimpleNamespace(
                id=1, file_name="test.pdf", original_file_path="local:/tmp/test.pdf"
            )
            self.key = SimpleNamespace(
                id=1, storage_type="server", private_key_encrypted=b"ENCRYPTED"
            )
            self.cert = SimpleNamespace(id=1, certificate_data=b"DERCERT")

        def set_not_found(self):
            self.doc = None
            self.key = None
            self.cert = None

        def apply(self, target_module: str = "app.services.sign_service"):
            # Tự động apply monkeypatch dựa trên state hiện tại của class
            monkeypatch.setattr(
                f"{target_module}.document_repo.get_by_id", lambda *a, **k: self.doc
            )
            monkeypatch.setattr(
                f"{target_module}.key_repo.get_by_id", lambda *a, **k: self.key
            )
            monkeypatch.setattr(
                f"{target_module}.certificate_repo.get_by_key_id",
                lambda *a, **k: self.cert,
            )

    return RepoMocker()
