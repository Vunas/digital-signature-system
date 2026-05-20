from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import jwt

pytestmark = pytest.mark.asyncio
from fastapi import HTTPException, Request
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
    async def test_get_current_user_missing_token_raises_401(self):
        # Arrange
        request = _build_request({})
        db = SimpleNamespace()

        # Act / Assert
        with pytest.raises(HTTPException) as exc:
            await get_current_user(request=request, db=db)
        assert exc.value.status_code == 401

    async def test_get_current_user_invalid_jwt_raises_401(self, monkeypatch):
        # Arrange
        request = _build_request({"access_token": "Bearer bad"})
        db = SimpleNamespace()
        monkeypatch.setattr(
            "app.core.dependencies.jwt.decode",
            lambda *args, **kwargs: (_ for _ in ()).throw(jwt.PyJWTError("bad")),
        )

        # Act / Assert
        with pytest.raises(HTTPException) as exc:
            await get_current_user(request=request, db=db)
        assert exc.value.status_code == 401

    async def test_get_current_user_payload_without_sub_raises_401(self, monkeypatch):
        # Arrange
        request = _build_request({"access_token": "Bearer ok"})
        db = SimpleNamespace()
        monkeypatch.setattr(
            "app.core.dependencies.jwt.decode",
            lambda *args, **kwargs: {},
        )

        # Act / Assert
        with pytest.raises(HTTPException) as exc:
            await get_current_user(request=request, db=db)
        assert exc.value.status_code == 401

    async def test_get_current_user_inactive_user_raises_401(self, monkeypatch):
        # Arrange
        request = _build_request({"access_token": "Bearer ok"})

        db = SimpleNamespace(
            execute=AsyncMock(
                return_value=SimpleNamespace(
                    scalar_one_or_none=lambda: SimpleNamespace(username="alice", is_active=False)
                )
            )
        )

        monkeypatch.setattr(
            "app.core.dependencies.jwt.decode",
            lambda *args, **kwargs: {"sub": "alice"},
        )

        # Act / Assert
        with pytest.raises(HTTPException) as exc:
            await get_current_user(request=request, db=db)
        assert exc.value.status_code == 401

    async def test_get_current_user_valid_token_returns_user(self, monkeypatch):
        # Arrange
        request = _build_request({"access_token": "Bearer ok"})
        expected_user = SimpleNamespace(username="alice", is_active=True)

        db = SimpleNamespace(
            execute=AsyncMock(
                return_value=SimpleNamespace(scalar_one_or_none=lambda: expected_user)
            )
        )
        monkeypatch.setattr(
            "app.core.dependencies.jwt.decode",
            lambda *args, **kwargs: {"sub": "alice"},
        )

        # Act
        user = await get_current_user(request=request, db=db)

        # Assert
        assert user == expected_user
