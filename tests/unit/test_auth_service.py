from types import SimpleNamespace

import pytest

from app.services.auth_service import AuthService


@pytest.fixture()
def auth_service():
    return AuthService()


class TestAuthService:
    def test_register_user_new_username_creates_user(self, auth_service, monkeypatch):
        # Arrange
        user_in = SimpleNamespace(username="alice")
        created_user = SimpleNamespace(id=1, username="alice")
        monkeypatch.setattr(
            "app.services.auth_service.user_repo.get_by_username",
            lambda db, username: None,
        )
        monkeypatch.setattr(
            "app.services.auth_service.user_repo.create",
            lambda db, obj_in: created_user,
        )

        # Act
        result = auth_service.register_user(db=object(), user_in=user_in)

        # Assert
        assert result == created_user

    def test_register_user_existing_username_raises_value_error(
        self, auth_service, monkeypatch
    ):
        # Arrange
        user_in = SimpleNamespace(username="alice")
        monkeypatch.setattr(
            "app.services.auth_service.user_repo.get_by_username",
            lambda db, username: SimpleNamespace(id=1, username=username),
        )

        # Act / Assert
        with pytest.raises(ValueError, match="đã tồn tại"):
            auth_service.register_user(db=object(), user_in=user_in)

    def test_authenticate_and_generate_tokens_valid_credentials_returns_tokens(
        self, auth_service, monkeypatch
    ):
        # Arrange
        user = SimpleNamespace(username="alice", password_hash="hashed")
        monkeypatch.setattr(
            "app.services.auth_service.user_repo.get_by_username",
            lambda db, username: user,
        )
        monkeypatch.setattr(
            "app.services.auth_service.verify_password",
            lambda plain, hashed: True,
        )
        monkeypatch.setattr(
            "app.services.auth_service.create_access_token",
            lambda data, expires_delta: "access-token",
        )
        monkeypatch.setattr(
            "app.services.auth_service.create_refresh_token",
            lambda data, expires_delta: "refresh-token",
        )

        # Act
        out_user, access, refresh = auth_service.authenticate_and_generate_tokens(
            db=object(), username="alice", password="secret"
        )

        # Assert
        assert out_user == user
        assert access == "access-token"
        assert refresh == "refresh-token"

    def test_authenticate_and_generate_tokens_wrong_password_raises_value_error(
        self, auth_service, monkeypatch
    ):
        # Arrange
        user = SimpleNamespace(username="alice", password_hash="hashed")
        monkeypatch.setattr(
            "app.services.auth_service.user_repo.get_by_username",
            lambda db, username: user,
        )
        monkeypatch.setattr(
            "app.services.auth_service.verify_password",
            lambda plain, hashed: False,
        )

        # Act / Assert
        with pytest.raises(ValueError, match="Sai tên đăng nhập hoặc mật khẩu"):
            auth_service.authenticate_and_generate_tokens(
                db=object(), username="alice", password="wrong"
            )

    def test_refresh_access_token_empty_token_raises_value_error(self, auth_service):
        # Arrange / Act / Assert
        with pytest.raises(ValueError, match="không tồn tại"):
            auth_service.refresh_access_token(db=object(), refresh_token_str="")

    def test_refresh_access_token_invalid_token_raises_value_error(
        self, auth_service, monkeypatch
    ):
        # Arrange
        monkeypatch.setattr(
            "app.services.auth_service.decode_token",
            lambda token: (_ for _ in ()).throw(Exception("invalid")),
        )

        # Act / Assert
        with pytest.raises(ValueError, match="hết hạn hoặc không hợp lệ"):
            auth_service.refresh_access_token(db=object(), refresh_token_str="bad")

    def test_refresh_access_token_inactive_user_raises_value_error(
        self, auth_service, monkeypatch
    ):
        # Arrange
        monkeypatch.setattr(
            "app.services.auth_service.decode_token",
            lambda token: {"sub": "alice"},
        )
        monkeypatch.setattr(
            "app.services.auth_service.user_repo.get_by_username",
            lambda db, username: SimpleNamespace(username=username, is_active=False),
        )

        # Act / Assert
        with pytest.raises(ValueError, match="Tài khoản bị khóa"):
            auth_service.refresh_access_token(db=object(), refresh_token_str="ok")
