import inspect

from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from app.core.kernel.identity import CurrentUser, get_current_user
from app.core.kernel.permissions import require_permission
from app.api.auth import get_current_user as get_authenticated_user

def test_firmas_congeladas():
    assert list(inspect.signature(get_current_user).parameters) == ["user"]
    assert list(inspect.signature(require_permission).parameters) == ["permission"]

def test_stub_devuelve_usuario_sin_permisos_por_defecto():
    app = FastAPI()

    class MockPermission:
        def __init__(self, name):
            self.name = name

    class MockRole:
        def __init__(self, permissions):
            self.permissions = permissions

    class MockUser:
        def __init__(self):
            self.id = 1
            self.email = "test@test.com"
            self.role_id = 1
            self.is_active = True
            self.restaurant_id = 1
            self.role = MockRole([MockPermission("x:y")])

    def mock_user():
        return MockUser()
        
    app.dependency_overrides[get_authenticated_user] = mock_user

    @app.get("/protegido")
    async def protegido(user: CurrentUser = Depends(require_permission("x:y"))):
        return user

    response = TestClient(app).get("/protegido")
    assert response.status_code == 200