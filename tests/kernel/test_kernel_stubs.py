import inspect

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.errors.handlers import register_exception_handlers
from app.core.kernel.identity import CurrentUser, get_current_user
from app.core.kernel.permissions import require_permission


@pytest.fixture(autouse=True)
def enable_dev_stubs(monkeypatch):
    """The stubs are disabled by default, so each test opts in explicitly."""
    monkeypatch.setenv("AUTH_STUBS_ENABLED", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def build_protected_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/protegido")
    async def protegido(user: CurrentUser = Depends(require_permission("x:y"))):
        return user

    return app


def test_firmas_congeladas():
    assert list(inspect.signature(get_current_user).parameters) == []
    assert list(inspect.signature(require_permission).parameters) == ["permission"]


def test_stub_devuelve_usuario_con_todos_los_permisos():
    response = TestClient(build_protected_app()).get("/protegido")

    assert response.status_code == 200
    assert response.json()["permissions"] == ["*"]


def test_stubs_disabled_reject_the_request(monkeypatch):
    monkeypatch.setenv("AUTH_STUBS_ENABLED", "false")
    get_settings.cache_clear()

    response = TestClient(build_protected_app()).get("/protegido")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
