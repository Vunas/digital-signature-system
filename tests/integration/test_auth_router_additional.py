from unittest.mock import AsyncMock

import pytest

pytestmark = pytest.mark.asyncio

class TestAuthRouterAdditional:
    async def test_refresh_without_cookie_returns_401(self, client_full):
        # Arrange / Act
        res = await client_full.post("/auth/refresh")

        # Assert
        assert res.status_code == 401

    async def test_refresh_with_valid_cookie_returns_200_and_sets_access_cookie(
        self, client_full, monkeypatch
    ):
        # Arrange
        monkeypatch.setattr(
            "app.routers.auth_router.auth_service.refresh_access_token",
            AsyncMock(return_value="new-access-token"),
        )

        # Act
        res = await client_full.post(
            "/auth/refresh", cookies={"refresh_token": "refresh-token"}
        )

        # Assert
        assert res.status_code == 200
        assert "set-cookie" in {k.lower() for k in res.headers.keys()}

    async def test_logout_returns_200(self, client_full):
        # Arrange / Act
        res = await client_full.post("/auth/logout")

        # Assert
        assert res.status_code == 200
