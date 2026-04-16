import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def main_client():
    with TestClient(app) as client:
        yield client


class TestMainApp:
    def test_root_route_returns_200(self, main_client):
        # Arrange / Act
        response = main_client.get("/")

        # Assert
        assert response.status_code == 200

    def test_login_page_route_returns_200(self, main_client):
        # Arrange / Act
        response = main_client.get("/login")

        # Assert
        assert response.status_code == 200
