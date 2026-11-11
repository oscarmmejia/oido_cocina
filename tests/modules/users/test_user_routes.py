from datetime import timedelta

import pytest
from sqlalchemy import func, select

from app.core.passwords import hash_password, verify_password
from app.core.kernel.permissions import ROLE_ADMIN, ROLE_SUPERADMIN, ROLE_WAITER
from app.core.security import create_access_token
from app.models import Permission, Restaurant, Role, RolePermission, User
from app.modules.users.routes import router

URL = "/api/v1/users"
PASSWORD = "user-routes-test-password"
PUBLIC_USER_FIELDS = {
    "id", "restaurant_id", "role_id", "name", "email", "phone_number", "is_active"
}


@pytest.fixture
def user_factory(db):
    def create(restaurant_id, role_id, email, *, is_active=True):
        user = User(
            restaurant_id=restaurant_id,
            role_id=role_id,
            name="Test user",
            email=email,
            password_hash=hash_password(PASSWORD),
            is_active=is_active,
        )
        db.add(user)
        db.commit()
        return user

    return create


@pytest.fixture
def manager(db, restaurant, user_factory):
    role = Role(restaurant_id=restaurant.id, name=ROLE_ADMIN)
    permission = Permission(name="user:manage")
    db.add_all([role, permission])
    db.flush()
    db.add(RolePermission(role_id=role.id, permission_id=permission.id))
    return user_factory(restaurant.id, role.id, "manager@example.com")


@pytest.fixture
def manager_headers(authenticated_client, manager):
    response = authenticated_client.post(
        "/api/v1/auth/login",
        data={"username": manager.email, "password": PASSWORD},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _payload(role_id):
    return {
        "name": "New worker", "email": "worker@example.com",
        "password": PASSWORD, "role_id": role_id,
    }


def _assert_error(response, status, code):
    assert response.status_code == status
    assert set(response.json()) == {"error"}
    assert response.json()["error"]["code"] == code
    assert isinstance(response.json()["error"]["message"], str)


def test_get_users_defaults_and_public_fields(
    authenticated_client, manager_headers, manager, user_factory
):
    inactive = user_factory(
        manager.restaurant_id, manager.role_id, "inactive@example.com", is_active=False
    )

    response = authenticated_client.get(URL, headers=manager_headers)

    assert response.status_code == 200
    page = response.json()
    assert set(page) == {"items", "total", "page", "page_size"}
    assert (page["total"], page["page"], page["page_size"]) == (2, 1, 20)
    assert [item["id"] for item in page["items"]] == [manager.id, inactive.id]
    assert page["items"][1]["is_active"] is False
    assert all(set(item) == PUBLIC_USER_FIELDS for item in page["items"])


def test_get_users_paginates_and_counts_only_authenticated_restaurant(
    db, authenticated_client, manager_headers, manager, user_factory
):
    local = [manager] + [
        user_factory(manager.restaurant_id, manager.role_id, f"local{i}@example.com")
        for i in range(3)
    ]
    other = Restaurant(id=manager.restaurant_id + 1, name="Other", time_zone="Europe/Madrid")
    db.add(other)
    db.flush()
    other_role = Role(restaurant_id=other.id, name=ROLE_WAITER)
    db.add(other_role)
    db.flush()
    user_factory(other.id, other_role.id, "other@example.com")

    response = authenticated_client.get(
        URL, headers=manager_headers, params={"page": 2, "page_size": 2}
    )

    assert response.status_code == 200
    page = response.json()
    assert (page["total"], page["page"], page["page_size"]) == (4, 2, 2)
    assert [item["id"] for item in page["items"]] == [user.id for user in local[2:]]
    assert all(item["restaurant_id"] == manager.restaurant_id for item in page["items"])


def test_get_users_beyond_last_page_returns_empty_items(authenticated_client, manager_headers):
    response = authenticated_client.get(
        URL, headers=manager_headers, params={"page": 2, "page_size": 1}
    )

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 1, "page": 2, "page_size": 1}


@pytest.mark.parametrize("params", [
    {"page": 0}, {"page": -1}, {"page": "invalid"},
    {"page_size": 0}, {"page_size": 101}, {"page_size": "invalid"},
    {"restaurant_id": 2}, {"unknown": "value"},
])
def test_get_users_rejects_invalid_pagination(authenticated_client, manager_headers, params):
    response = authenticated_client.get(URL, headers=manager_headers, params=params)

    _assert_error(response, 422, "VALIDATION_ERROR")


def test_get_users_allows_maximum_page_size(authenticated_client, manager_headers):
    response = authenticated_client.get(
        URL, headers=manager_headers, params={"page_size": 100}
    )

    assert response.status_code == 200
    assert response.json()["page_size"] == 100


def test_get_users_uses_persisted_scope_instead_of_token_claim(
    db, authenticated_client, manager, user_factory
):
    other = Restaurant(id=manager.restaurant_id + 1, name="Other", time_zone="Europe/Madrid")
    db.add(other)
    db.flush()
    role = Role(restaurant_id=other.id, name=ROLE_WAITER)
    db.add(role)
    db.flush()
    user_factory(other.id, role.id, "other@example.com")
    token = create_access_token({
        "sub": manager.email, "user_id": manager.id, "restaurant_id": other.id,
        "token_version": manager.token_version,
    })

    response = authenticated_client.get(URL, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == manager.id


def test_post_user_returns_201_and_creates_login_compatible_account(
    db, authenticated_client, manager_headers, manager
):
    role = Role(restaurant_id=manager.restaurant_id, name=ROLE_WAITER)
    db.add(role)
    db.commit()

    response = authenticated_client.post(
        URL, headers=manager_headers, json=_payload(role.id)
    )

    assert response.status_code == 201
    assert set(response.json()) == PUBLIC_USER_FIELDS
    assert response.json()["restaurant_id"] == manager.restaurant_id
    db.expire_all()
    stored = db.get(User, response.json()["id"])
    assert verify_password(PASSWORD, stored.password_hash)
    login = authenticated_client.post(
        "/api/v1/auth/login", data={"username": stored.email, "password": PASSWORD}
    )
    assert login.status_code == 200


def test_post_user_duplicate_email_returns_409_without_insert(
    db, authenticated_client, manager_headers, manager
):
    payload = _payload(manager.role_id)
    payload["email"] = manager.email.upper()
    before = db.scalar(select(func.count()).select_from(User))

    response = authenticated_client.post(URL, headers=manager_headers, json=payload)

    _assert_error(response, 409, "CONFLICT")
    assert response.json()["error"]["message"] == "Ya existe un usuario con ese correo electrónico."
    assert db.scalar(select(func.count()).select_from(User)) == before


@pytest.mark.parametrize("role_name,status,code,message", [
    (None, 404, "NOT_FOUND", "El rol solicitado no existe."),
    (ROLE_SUPERADMIN, 403, "FORBIDDEN",
     "No está permitido asignar el rol de superadministrador."),
])
def test_post_user_role_errors_are_in_spanish(
    db, authenticated_client, manager_headers, manager, role_name, status, code, message
):
    role_id = 999999
    if role_name is not None:
        role = Role(restaurant_id=manager.restaurant_id, name=role_name)
        db.add(role)
        db.commit()
        role_id = role.id

    response = authenticated_client.post(
        URL, headers=manager_headers, json=_payload(role_id)
    )

    _assert_error(response, status, code)
    assert response.json()["error"]["message"] == message
    assert db.scalar(select(func.count()).select_from(User)) == 1


@pytest.mark.parametrize("changes", [
    {"email": "invalid"}, {"password": ""}, {"role_id": 0},
    {"restaurant_id": 2}, {"is_active": False}, {"password_hash": "forbidden"},
])
def test_post_user_rejects_invalid_or_protected_fields(
    db, authenticated_client, manager_headers, manager, changes
):
    payload = {**_payload(manager.role_id), **changes}
    before = db.scalar(select(func.count()).select_from(User))

    response = authenticated_client.post(URL, headers=manager_headers, json=payload)

    _assert_error(response, 422, "VALIDATION_ERROR")
    assert db.scalar(select(func.count()).select_from(User)) == before


@pytest.mark.parametrize("method", ["get", "post"])
def test_user_routes_require_real_permission(
    db, authenticated_client, manager_headers, manager, method
):
    manager.role.permissions.clear()
    db.commit()
    kwargs = {"headers": manager_headers}
    if method == "post":
        kwargs["json"] = _payload(manager.role_id)

    response = getattr(authenticated_client, method)(URL, **kwargs)

    _assert_error(response, 403, "FORBIDDEN")
    assert db.scalar(select(func.count()).select_from(User)) == 1


@pytest.mark.parametrize("method", ["get", "post"])
@pytest.mark.parametrize("authorization", [None, "Bearer invalid-token"])
def test_user_routes_require_authentication(authenticated_client, method, authorization):
    kwargs = {"headers": {"Authorization": authorization}} if authorization else {}
    if method == "post":
        kwargs["json"] = _payload(1)

    response = getattr(authenticated_client, method)(URL, **kwargs)

    _assert_error(response, 401, "UNAUTHORIZED")


@pytest.mark.parametrize("method", ["get", "post"])
@pytest.mark.parametrize("reason", ["expired", "inactive"])
def test_user_routes_reject_expired_or_inactive_identity(
    db, authenticated_client, manager_headers, manager, method, reason
):
    headers = manager_headers
    if reason == "expired":
        token = create_access_token(
            {"sub": manager.email, "user_id": manager.id,
             "restaurant_id": manager.restaurant_id,
             "token_version": manager.token_version},
            expires_delta=timedelta(seconds=-1),
        )
        headers = {"Authorization": f"Bearer {token}"}
    else:
        manager.is_active = False
        db.commit()
    kwargs = {"headers": headers}
    if method == "post":
        kwargs["json"] = _payload(manager.role_id)

    response = getattr(authenticated_client, method)(URL, **kwargs)

    _assert_error(response, 401, "UNAUTHORIZED")


def test_user_routes_openapi_and_single_registration(authenticated_client):
    schema = authenticated_client.get("/openapi.json").json()
    operations = schema["paths"][URL]
    assert set(operations) == {"get", "post"}
    for method, success, model in (("get", "200", "UserPage"), ("post", "201", "UserRead")):
        assert len([
            route for route in router.routes
            if route.path == "/users" and method.upper() in route.methods
        ]) == 1
        operation = operations[method]
        assert operation["description"]
        assert operation["security"]
        assert operation["responses"][success]["content"]["application/json"]["schema"] == {
            "$ref": f"#/components/schemas/{model}"
        }
        for code in ("401", "403", "422", "500"):
            assert operation["responses"][code]["content"]["application/json"]["schema"] == {
                "$ref": "#/components/schemas/ErrorResponse"
            }
    params = {item["name"]: item["schema"] for item in operations["get"]["parameters"]}
    assert set(params) == {"page", "page_size"}
    assert params["page"]["default"] == 1
    assert params["page_size"]["default"] == 20
    assert params["page_size"]["maximum"] == 100
    public = schema["components"]["schemas"]["UserRead"]["properties"]
    assert set(public) == PUBLIC_USER_FIELDS
