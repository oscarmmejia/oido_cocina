import inspect

from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from app.core.kernel.identity import CurrentUser, get_current_user
from app.core.kernel.permissions import require_permission


def test_firmas_congeladas():
    assert list(inspect.signature(get_current_user).parameters) == []
    assert list(inspect.signature(require_permission).parameters) == ["permission"]


def test_stub_devuelve_usuario_con_todos_los_permisos():
    app = FastAPI()

    @app.get("/protegido")
    async def protegido(user: CurrentUser = Depends(require_permission("x:y"))):
        return user

    response = TestClient(app).get("/protegido")
    assert response.status_code == 200
    assert response.json()["permissions"] == ["*"]