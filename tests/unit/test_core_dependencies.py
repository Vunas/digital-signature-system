from types import SimpleNamespace

import pytest
from fastapi import HTTPException, Request
from jose import JWTError

from app.core.dependencies import get_current_user


def _build_request(cookies: dict):
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [],
    }
    req = Request(scope)
    req._cookies = cookies
    return req


class TestCoreDependencies:
    def test_get_current_user_missing_token_raises_401(self):
        # Arrange
        request = _build_request({})
        db = SimpleNamespace()

        # Act / Assert
        with pytest.raises(HTTPException) as exc:
            get_current_user(request=request, db=db)
        assert exc.value.status_code == 401

    def test_get_current_user_invalid_jwt_raises_401(self, monkeypatch):
        # Arrange
        request = _build_request({"access_token": "Bearer bad"})
        db = SimpleNamespace()
        monkeypatch.setattr(
            "app.core.dependencies.jwt.decode",
            lambda *args, **kwargs: (_ for _ in ()).throw(JWTError("bad")),
        )

        # Act / Assert
        with pytest.raises(HTTPException) as exc:
            get_current_user(request=request, db=db)
        assert exc.value.status_code == 401

    def test_get_current_user_payload_without_sub_raises_401(self, monkeypatch):
        # Arrange
        request = _build_request({"access_token": "Bearer ok"})
        db = SimpleNamespace()
        monkeypatch.setattr(
            "app.core.dependencies.jwt.decode",
            lambda *args, **kwargs: {},
        )

        # Act / Assert
        with pytest.raises(HTTPException) as exc:
            get_current_user(request=request, db=db)
        assert exc.value.status_code == 401

    def test_get_current_user_inactive_user_raises_401(self, monkeypatch):
        # Arrange
        request = _build_request({"access_token": "Bearer ok"})

        class DummyQuery:
            def filter(self, *args, **kwargs):
                return self

            def first(self):
                return SimpleNamespace(username="alice", is_active=False)

        db = SimpleNamespace(query=lambda model: DummyQuery())

        monkeypatch.setattr(
            "app.core.dependencies.jwt.decode",
            lambda *args, **kwargs: {"sub": "alice"},
        )

        # Act / Assert
        with pytest.raises(HTTPException) as exc:
            get_current_user(request=request, db=db)
        assert exc.value.status_code == 401

    def test_get_current_user_valid_token_returns_user(self, monkeypatch):
        # Arrange
        request = _build_request({"access_token": "Bearer ok"})
        expected_user = SimpleNamespace(username="alice", is_active=True)

        class DummyQuery:
            def filter(self, *args, **kwargs):
                return self

            def first(self):
                return expected_user

        db = SimpleNamespace(query=lambda model: DummyQuery())
        monkeypatch.setattr(
            "app.core.dependencies.jwt.decode",
            lambda *args, **kwargs: {"sub": "alice"},
        )

        # Act
        user = get_current_user(request=request, db=db)

        # Assert
        assert user == expected_user
