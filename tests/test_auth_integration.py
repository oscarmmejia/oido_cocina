import asyncio
from datetime import timedelta

import pytest
from sqlalchemy import func, select

from app.core.kernel.errors import AppError
from app.core.kernel.identity import get_current_user
from app.core.passwords import hash_password, verify_password
from app.core.kernel.permissions import ROLE_ADMIN, ROLE_SUPERADMIN, ROLE_WAITER
from app.core.security import create_access_token
from app.models import DiningTable, Permission, Restaurant, Role, RolePermission, User

PASSWORD = "test-password"


def _account(
    db,
    restaurant,
    *,
    role_name=ROLE_ADMIN,
    permissions=(),
    email="admin@example.com",
    is_active=True,
):
    role = Role(restaurant_id=restaurant.id, name=role_name)
    db.add(role)
    db.flush()
    for name in permissions:
        permission = db.scalar(select(Permission).where(Permission.name == name))
        if permission is None:
            permission = Permission(name=name)
            db.add(permission)
            db.flush()
        db.add(RolePermission(role_id=role.id, permission_id=permission.id))
    user = User(
        restaurant_id=restaurant.id,
        role_id=role.id,
        name="Test account",
        email=email,
        password_hash=hash_password(PASSWORD),
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    return user


def _login(client, email="admin@example.com"):
    response = client.post(
        "/api/v1/auth/login", data={"username": email, "password": PASSWORD}
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_real_identity_exposes_database_role_and_permissions(db, restaurant):
    user = _account(
        db, restaurant, permissions={"user:manage", "settings:update"}
    )

    identity = asyncio.run(get_current_user(user=user))

    assert identity.restaurant_id == restaurant.id
    assert identity.role == ROLE_ADMIN
    assert identity.permissions == {"user:manage", "settings:update"}


def test_role_id_one_does_not_grant_permissions(db, restaurant, authenticated_client):
    user = _account(db, restaurant, role_name=ROLE_WAITER)
    assert user.role_id == 1

    headers = _login(authenticated_client)
    response = authenticated_client.get("/api/v1/tables", headers=headers)

    assert response.status_code == 403


def test_real_role_permissions_work_without_role_id_one(
    db, restaurant, authenticated_client
):
    _account(db, restaurant, role_name=ROLE_WAITER, email="waiter@example.com")
    user = _account(db, restaurant, permissions={"table:manage"})
    assert user.role_id != 1

    headers = _login(authenticated_client)
    response = authenticated_client.get("/api/v1/tables", headers=headers)

    assert response.status_code == 200


def test_anonymous_request_is_rejected(authenticated_client):
    response = authenticated_client.get("/api/v1/tables")

    assert response.status_code == 401


def test_invalid_token_is_rejected(authenticated_client):
    response = authenticated_client.get(
        "/api/v1/tables", headers={"Authorization": "Bearer invalid-token"}
    )

    assert response.status_code == 401


def test_expired_token_is_rejected(db, restaurant, authenticated_client):
    user = _account(db, restaurant, permissions={"table:manage"})
    token = create_access_token(
        {"sub": user.email, "user_id": user.id, "restaurant_id": restaurant.id,
         "token_version": user.token_version},
        expires_delta=timedelta(seconds=-1),
    )

    response = authenticated_client.get(
        "/api/v1/tables", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401


def test_inactive_account_cannot_login(db, restaurant, authenticated_client):
    _account(db, restaurant, is_active=False)

    response = authenticated_client.post(
        "/api/v1/auth/login",
        data={"username": "admin@example.com", "password": PASSWORD},
    )

    assert response.status_code == 401


def test_inactive_account_with_existing_token_is_rejected(
    db, restaurant, authenticated_client
):
    user = _account(db, restaurant, permissions={"table:manage"})
    headers = _login(authenticated_client)
    user.is_active = False
    db.commit()

    response = authenticated_client.get("/api/v1/tables", headers=headers)

    assert response.status_code == 401


def test_real_identity_rejects_role_from_another_restaurant(db, restaurant):
    user = _account(db, restaurant)
    other = Restaurant(id=restaurant.id + 1, name="Other", time_zone="Europe/Madrid")
    db.add(other)
    db.flush()
    role = Role(restaurant_id=other.id, name=ROLE_ADMIN)
    db.add(role)
    db.flush()
    user.role_id = role.id
    db.commit()
    db.expire(user, ["role"])

    with pytest.raises(AppError) as error:
        asyncio.run(get_current_user(user=user))

    assert error.value.status_code == 403


def test_real_user_cannot_access_table_in_another_restaurant(
    db, restaurant, authenticated_client
):
    _account(db, restaurant, permissions={"table:manage"})
    other = Restaurant(id=restaurant.id + 1, name="Other", time_zone="Europe/Madrid")
    db.add(other)
    db.flush()
    table = DiningTable(
        restaurant_id=other.id,
        number=1,
        min_capacity=1,
        max_capacity=4,
        location="interior",
    )
    db.add(table)
    db.commit()
    headers = _login(authenticated_client)

    response = authenticated_client.get(f"/api/v1/tables/{table.id}", headers=headers)

    assert response.status_code == 404


def test_create_user_uses_authenticated_restaurant_and_safe_response(
    db, restaurant, authenticated_client
):
    _account(db, restaurant, permissions={"user:manage"})
    role = Role(restaurant_id=restaurant.id, name=ROLE_WAITER)
    db.add(role)
    db.commit()
    headers = _login(authenticated_client)

    response = authenticated_client.post(
        "/api/v1/users",
        headers=headers,
        json={"name": "New user", "email": "new@example.com", "password": PASSWORD, "role_id": role.id},
    )

    assert response.status_code == 201
    assert set(response.json()) == {
        "id", "restaurant_id", "role_id", "name", "email", "phone_number", "is_active"
    }
    assert response.json()["restaurant_id"] == restaurant.id
    stored = db.get(User, response.json()["id"])
    assert verify_password(PASSWORD, stored.password_hash)
    login = authenticated_client.post(
        "/api/v1/auth/login", data={"username": "new@example.com", "password": PASSWORD}
    )
    assert login.status_code == 200


def test_create_user_duplicate_returns_409(db, restaurant, authenticated_client):
    actor = _account(db, restaurant, permissions={"user:manage"})
    headers = _login(authenticated_client)
    before = db.scalar(select(func.count()).select_from(User))

    response = authenticated_client.post(
        "/api/v1/users",
        headers=headers,
        json={"name": "Duplicate", "email": actor.email.upper(), "password": PASSWORD, "role_id": actor.role_id},
    )

    assert response.status_code == 409
    assert db.scalar(select(func.count()).select_from(User)) == before


def test_create_user_without_permission_returns_403(db, restaurant, authenticated_client):
    actor = _account(db, restaurant)
    headers = _login(authenticated_client)

    response = authenticated_client.post(
        "/api/v1/users",
        headers=headers,
        json={"name": "Denied", "email": "new@example.com", "password": PASSWORD, "role_id": actor.role_id},
    )

    assert response.status_code == 403
    assert db.scalar(select(func.count()).select_from(User)) == 1


def test_create_user_rejects_superadministrator(db, restaurant, authenticated_client):
    _account(db, restaurant, permissions={"user:manage"})
    role = Role(restaurant_id=restaurant.id, name=ROLE_SUPERADMIN)
    db.add(role)
    db.commit()
    headers = _login(authenticated_client)

    response = authenticated_client.post(
        "/api/v1/users",
        headers=headers,
        json={"name": "Denied", "email": "new@example.com", "password": PASSWORD, "role_id": role.id},
    )

    assert response.status_code == 403


def test_create_user_rejects_client_restaurant_id(db, restaurant, authenticated_client):
    actor = _account(db, restaurant, permissions={"user:manage"})
    headers = _login(authenticated_client)

    response = authenticated_client.post(
        "/api/v1/users",
        headers=headers,
        json={"name": "Denied", "email": "new@example.com", "password": PASSWORD, "role_id": actor.role_id, "restaurant_id": 2},
    )

    assert response.status_code == 422


def test_create_user_rejects_role_from_another_restaurant(db, restaurant, authenticated_client):
    _account(db, restaurant, permissions={"user:manage"})
    other = Restaurant(id=restaurant.id + 1, name="Other", time_zone="Europe/Madrid")
    db.add(other)
    db.flush()
    role = Role(restaurant_id=other.id, name=ROLE_WAITER)
    db.add(role)
    db.commit()
    headers = _login(authenticated_client)

    response = authenticated_client.post(
        "/api/v1/users",
        headers=headers,
        json={"name": "Denied", "email": "new@example.com", "password": PASSWORD, "role_id": role.id},
    )

    assert response.status_code == 404
