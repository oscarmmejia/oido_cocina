import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.core.database_connection import get_db


class DatabaseUp:
    def execute(self, *args, **kwargs):
        return None


class DatabaseDown:
    def execute(self, *args, **kwargs):
        raise OperationalError("SELECT 1", {}, Exception("connection refused on secret-host"))


@pytest.fixture
def app():
    try:
        from app.main import app
    except SystemExit:
        pytest.skip("DATABASE_URL is not configured.")
    yield app
    app.dependency_overrides.clear()


def test_health_ok(app):
    app.dependency_overrides[get_db] = lambda: DatabaseUp()

    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"app": "ok", "database": "ok"}


def test_health_database_down_uses_the_common_error_format_without_details(app):
    app.dependency_overrides[get_db] = lambda: DatabaseDown()

    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert "secret-host" not in response.text and "SELECT" not in response.text
