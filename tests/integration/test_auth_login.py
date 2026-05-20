import pytest
from app.core.security import get_password_hash
from app.models.user import User

pytestmark = pytest.mark.asyncio



@pytest.mark.integration
async def test_login_sets_http_only_cookies(client_full, db_session):
    # Validates: /auth/login authenticates and sets access/refresh cookies.
    u = User(
        username="alice", password_hash=get_password_hash("secret"), is_active=True
    )
    db_session.add(u)
    await db_session.commit()

    res = await client_full.post(
        "/auth/login",
        data={"username": "alice", "password": "secret"},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 200, res.text

    # FastAPI/Starlette exposes cookies via Set-Cookie headers.
    set_cookie = "\n".join(res.headers.get_list("set-cookie"))
    assert "access_token=" in set_cookie
    assert "refresh_token=" in set_cookie
    assert "HttpOnly" in set_cookie


@pytest.mark.integration
async def test_login_wrong_password_returns_401(client_full, db_session):
    # Validates: wrong password is rejected deterministically.
    u = User(username="bob", password_hash=get_password_hash("secret"), is_active=True)
    db_session.add(u)
    await db_session.commit()

    res = await client_full.post(
        "/auth/login",
        data={"username": "bob", "password": "wrong"},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 401
