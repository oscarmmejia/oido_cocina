from datetime import datetime, timedelta, timezone

import pytest

from app.core.passwords import verify_password
from app.core.kernel.permissions import ROLE_SUPERADMIN, ROLE_WAITER
from app.core.security import create_access_token
from app.models import Reservation, Restaurant, Role, User
from tests.modules.users.test_user_routes import (
    PASSWORD, PUBLIC_USER_FIELDS, manager, manager_headers, user_factory,
)

URL = "/api/v1/users"


@pytest.fixture
def worker(db, manager, user_factory):
    role = Role(restaurant_id=manager.restaurant_id, name=ROLE_WAITER)
    db.add(role)
    db.flush()
    return user_factory(manager.restaurant_id, role.id, "target@example.com")


def _login(client, user, password=PASSWORD):
    response = client.post("/api/v1/auth/login", data={
        "username": user.email, "password": password,
    })
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _snapshot(user):
    return (user.name, user.email, user.role_id, user.is_active,
            user.password_hash, user.phone_number, user.token_version)


@pytest.mark.parametrize("changes", [
    {"name": "Updated", "phone_number": None}, {},
    {"email": "RENAMED@example.com"}, {"password": "new-password"},
])
def test_update_data_and_session_revocation(
    db, authenticated_client, manager_headers, worker, changes
):
    old = _snapshot(worker)
    headers = _login(authenticated_client, worker)
    response = authenticated_client.patch(
        f"{URL}/{worker.id}", headers=manager_headers, json=changes
    )
    assert response.status_code == 200
    assert set(response.json()) == PUBLIC_USER_FIELDS
    db.expire_all()
    revokes = "email" in changes or "password" in changes
    assert worker.token_version == int(revokes)
    assert worker.role_id == old[2]
    assert worker.is_active is True
    assert worker.name == changes.get("name", old[0])
    if "email" in changes:
        assert worker.email == "renamed@example.com"
    if "password" in changes:
        assert verify_password(changes["password"], worker.password_hash)
    else:
        assert worker.password_hash == old[4]
    assert authenticated_client.get("/api/v1/auth/me", headers=headers).status_code == (
        401 if revokes else 200
    )
    _login(authenticated_client, worker, changes.get("password", PASSWORD))


def test_duplicate_email_rolls_back_entire_patch(
    db, authenticated_client, manager_headers, manager, worker
):
    before = _snapshot(worker)
    response = authenticated_client.patch(
        f"{URL}/{worker.id}", headers=manager_headers,
        json={"email": manager.email.upper(), "name": "Rejected", "password": "new"},
    )
    assert response.status_code == 409
    db.expire_all()
    assert _snapshot(worker) == before


def test_role_change_replaces_single_role_and_revokes_sessions(
    db, authenticated_client, manager_headers, manager, worker
):
    headers = _login(authenticated_client, worker)
    for _ in range(2):
        response = authenticated_client.patch(
            f"{URL}/{worker.id}/role", headers=manager_headers,
            json={"role_id": manager.role_id},
        )
        assert response.status_code == 200
        db.expire_all()
        assert worker.role_id == manager.role_id
        assert worker.token_version == 1
    assert authenticated_client.get("/api/v1/auth/me", headers=headers).status_code == 401


def test_self_role_change_is_rejected(authenticated_client, manager_headers, manager):
    response = authenticated_client.patch(
        f"{URL}/{manager.id}/role", headers=manager_headers,
        json={"role_id": manager.role_id},
    )
    assert response.status_code == 403


@pytest.mark.parametrize("kind", ["missing", "foreign", "superadmin"])
def test_incompatible_role_preserves_user(
    db, authenticated_client, manager_headers, manager, worker, kind
):
    role_id = 999999
    if kind != "missing":
        restaurant_id = manager.restaurant_id
        if kind == "foreign":
            other = Restaurant(id=restaurant_id + 1, name="Other", time_zone="Europe/Madrid")
            db.add(other)
            db.flush()
            restaurant_id = other.id
        role = Role(restaurant_id=restaurant_id, name=ROLE_SUPERADMIN)
        db.add(role)
        db.commit()
        role_id = role.id
    before = _snapshot(worker)
    response = authenticated_client.patch(
        f"{URL}/{worker.id}/role", headers=manager_headers, json={"role_id": role_id}
    )
    assert response.status_code == (403 if kind == "superadmin" else 404)
    db.expire_all()
    assert _snapshot(worker) == before


def test_inactivation_preserves_history_and_reactivation_does_not_restore_tokens(
    db, authenticated_client, manager_headers, worker
):
    headers = _login(authenticated_client, worker)
    start = datetime.now(timezone.utc)
    reservation = Reservation(
        restaurant_id=worker.restaurant_id, created_by_user_id=worker.id,
        customer_name="Customer", phone="555123456", party_size=2,
        start_at=start, end_at=start + timedelta(hours=1),
    )
    db.add(reservation)
    db.commit()
    reservation_id = reservation.id
    for active, version in ((False, 1), (False, 1), (True, 2)):
        response = authenticated_client.patch(
            f"{URL}/{worker.id}/status", headers=manager_headers, json={"is_active": active}
        )
        assert response.status_code == 200
        db.expire_all()
        assert db.get(User, worker.id).is_active is active
        assert worker.token_version == version
        assert db.get(Reservation, reservation_id).created_by_user_id == worker.id
        assert authenticated_client.get("/api/v1/auth/me", headers=headers).status_code == 401
        login = authenticated_client.post("/api/v1/auth/login", data={
            "username": worker.email, "password": PASSWORD,
        })
        assert login.status_code == (200 if active else 401)


@pytest.mark.parametrize("suffix,payload", [
    ("", {"name": "Changed"}), ("/role", {"role_id": 1}),
    ("/status", {"is_active": False}),
])
@pytest.mark.parametrize("kind", ["foreign", "missing", "superadmin", "no_permission", "anonymous"])
def test_patch_authorization_and_scope(
    db, authenticated_client, manager_headers, manager, worker, user_factory,
    suffix, payload, kind
):
    target_id = worker.id
    headers = manager_headers
    if kind == "anonymous":
        headers = {}
    elif kind == "no_permission":
        manager.role.permissions.clear()
        db.commit()
    elif kind == "missing":
        target_id = 999999
    else:
        restaurant_id = manager.restaurant_id
        if kind == "foreign":
            other = Restaurant(id=restaurant_id + 1, name="Other", time_zone="Europe/Madrid")
            db.add(other)
            db.flush()
            restaurant_id = other.id
        role = Role(restaurant_id=restaurant_id, name=ROLE_SUPERADMIN)
        db.add(role)
        db.flush()
        target_id = user_factory(restaurant_id, role.id, "protected@example.com").id
    response = authenticated_client.patch(
        f"{URL}/{target_id}{suffix}", headers=headers, json=payload
    )
    expected = 401 if kind == "anonymous" else (
        404 if kind in ("foreign", "missing") else 403
    )
    assert response.status_code == expected


@pytest.mark.parametrize("suffix,payload", [
    ("", {"name": None}), ("", {"email": None}), ("", {"password": None}),
    ("", {"password": ""}), ("", {"email": "invalid"}), ("", {"role_id": 1}),
    ("", {"restaurant_id": 2}), ("", {"token_version": 3}), ("", {"is_active": False}),
    ("/role", {"role_id": 0}), ("/role", {"role_id": 1, "is_active": True}),
    ("/status", {"is_active": None}), ("/status", {"is_active": "invalid"}),
])
def test_invalid_patch_is_atomic(db, authenticated_client, manager_headers, worker, suffix, payload):
    before = _snapshot(worker)
    response = authenticated_client.patch(
        f"{URL}/{worker.id}{suffix}", headers=manager_headers, json=payload
    )
    assert response.status_code == 422
    db.expire_all()
    assert _snapshot(worker) == before


@pytest.mark.parametrize("version", [None, -1, "0", True, 1])
def test_token_version_is_required_and_must_match(authenticated_client, manager, version):
    claims = {"sub": manager.email, "user_id": manager.id, "restaurant_id": manager.restaurant_id}
    if version is not None:
        claims["token_version"] = version
    token = create_access_token(claims)
    assert authenticated_client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {token}"
    }).status_code == 401


def test_email_reuse_cannot_transfer_old_identity(
    db, authenticated_client, manager_headers, manager, worker, user_factory
):
    headers = _login(authenticated_client, worker)
    old_email = worker.email
    response = authenticated_client.patch(
        f"{URL}/{worker.id}", headers=manager_headers, json={"email": "new@example.com"}
    )
    assert response.status_code == 200
    user_factory(manager.restaurant_id, worker.role_id, old_email)
    assert authenticated_client.get("/api/v1/auth/me", headers=headers).status_code == 401


def test_signed_token_cannot_mix_user_id_and_subject(authenticated_client, manager, worker):
    token = create_access_token({
        "sub": worker.email, "user_id": manager.id,
        "restaurant_id": manager.restaurant_id, "token_version": manager.token_version,
    })
    assert authenticated_client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {token}"
    }).status_code == 401


def test_update_openapi_contract(authenticated_client):
    paths = authenticated_client.get("/openapi.json").json()["paths"]
    for suffix in ("", "/role", "/status"):
        operation = paths[f"{URL}/{{user_id}}{suffix}"]["patch"]
        assert operation["security"]
        assert "user:manage" in operation["description"]
        assert set(operation["responses"]) >= {"200", "401", "403", "404", "422"}
