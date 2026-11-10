import inspect

from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from app.core.kernel.identity import CurrentUser, get_current_user
from app.core.kernel.permissions import require_permission
from app.api.auth import get_current_user as get_authenticated_user
from app.models.user import User

def test_firmas_congeladas():
    assert list(inspect.signature(get_current_user).parameters) == ["user"]
    assert list(inspect.signature(require_permission).parameters) == ["permission"]

def test_stub_devuelve_usuario_sin_permisos_por_defecto():
    app = FastAPI()

    def mock_user():
        return User(id=1, email="test@test.com", role_id=2, is_active=True)
        
    app.dependency_overrides[get_authenticated_user] = mock_user

    @app.get("/protegido")
    async def protegido(user: CurrentUser = Depends(require_permission("x:y"))):
        return user

    response = TestClient(app).get("/protegido")
    assert response.status_code == 200
    assert response.json()["permissions"] == []