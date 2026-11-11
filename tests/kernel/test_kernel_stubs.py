import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.kernel.errors import register_error_handlers
from app.core.kernel.identity import CurrentUser, get_current_user
from app.core.kernel.permissions import require_permission


@pytest.mark.parametrize(
    "role_name,permissions,expected",
    [
        ("superadmin", set(), 403),
        ("superadministrador", set(), 403),
        ("administrador", {"settings:update"}, 200),
        ("administrador", {"table:manage"}, 403),
        ("camarero", {"*"}, 200),
    ],
)
def test_permission_checker_uses_permissions_not_role_name(
    role_name, permissions, expected
):
    probe = FastAPI()
    register_error_handlers(probe)
    probe.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=2,
        restaurant_id=1,
        email="user@example.com",
        role=role_name,
        permissions=permissions,
    )

    @probe.get("/protected")
    def protected(user: CurrentUser = Depends(require_permission("settings:update"))):
        return {"id": user.id}

    with TestClient(probe) as client:
        response = client.get("/protected")
    assert response.status_code == expected
