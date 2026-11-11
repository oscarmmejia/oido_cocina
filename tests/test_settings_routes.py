import json
import re
from datetime import time, timedelta
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.core.kernel.identity import CurrentUser, get_current_user
from app.core.passwords import hash_password
from app.core.kernel.permissions import ROLE_ADMIN
from app.core.scope import get_restaurant_scope
from app.core.security import create_access_token
from app.main import app
from app.models import Permission, Restaurant, Role, RolePermission, User
from app.modules.settings.schemas import RestaurantSettingsResponse

PASSWORD = "settings-test-password"
URL = "/api/v1/settings"
DOCUMENTED_SETTINGS_EXAMPLES = [
    ("read", "Read settings"),
    ("complete", "Complete update"),
    ("partial", "Partial update"),
    ("overnight", "Overnight update"),
    ("negative_courtesy", "Negative courtesy"),
    ("equal_hours", "Equal opening and closing"),
    ("kitchen_after_closing", "Kitchen closes too late"),
]


@pytest.fixture
def settings_account(db, restaurant):
    restaurant.open_time = time(12)
    restaurant.close_time = time(23)
    restaurant.kitchen_close_time = time(22)
    role = Role(restaurant_id=restaurant.id, name=ROLE_ADMIN)
    permission = Permission(name="settings:update")
    db.add_all([role, permission])
    db.flush()
    db.add(RolePermission(role_id=role.id, permission_id=permission.id))
    user = User(
        restaurant_id=restaurant.id,
        role_id=role.id,
        name="Settings manager",
        email="settings@example.com",
        password_hash=hash_password(PASSWORD),
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def settings_headers(authenticated_client, settings_account):
    response = authenticated_client.post(
        "/api/v1/auth/login",
        data={"username": settings_account.email, "password": PASSWORD},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _assert_error(response, status_code, code):
    assert response.status_code == status_code
    assert set(response.json()) == {"error"}
    assert response.json()["error"]["code"] == code
    assert isinstance(response.json()["error"]["message"], str)


def test_get_settings_returns_authenticated_restaurant(
    authenticated_client, settings_headers, restaurant
):
    response = authenticated_client.get(URL, headers=settings_headers)

    assert response.status_code == 200
    assert response.json()["id"] == restaurant.id
    assert response.json()["open_time"] == "12:00:00"
    assert set(response.json()) == {
        "id", "name", "time_zone", "is_active", "courtesy_minutes", "slot_minutes",
        "min_break_between_shifts", "day_of_week", "period", "open_time",
        "close_time", "kitchen_close_time", "direction",
    }


def test_get_does_not_require_update_permission(
    db, authenticated_client, settings_headers, settings_account
):
    settings_account.role.permissions.clear()
    db.commit()

    response = authenticated_client.get(URL, headers=settings_headers)

    assert response.status_code == 200


def test_patch_partially_updates_and_persists_settings(
    db, authenticated_client, settings_headers, restaurant
):
    before = (restaurant.slot_minutes, restaurant.open_time, restaurant.name)

    response = authenticated_client.patch(
        URL, headers=settings_headers, json={"courtesy_minutes": 10}
    )

    assert response.status_code == 200
    db.expire_all()
    stored = db.get(Restaurant, restaurant.id)
    assert stored.courtesy_minutes == 10
    assert (stored.slot_minutes, stored.open_time, stored.name) == before
    assert authenticated_client.get(URL, headers=settings_headers).json()["courtesy_minutes"] == 10


def test_patch_accepts_overnight_schedule(authenticated_client, settings_headers):
    response = authenticated_client.patch(
        URL,
        headers=settings_headers,
        json={"open_time": "20:00", "kitchen_close_time": "02:00", "close_time": "03:00"},
    )

    assert response.status_code == 200
    assert response.json()["close_time"] == "03:00:00"
    assert response.json()["kitchen_close_time"] == "02:00:00"


@pytest.mark.parametrize("payload", [
    {"courtesy_minutes": -1},
    {"slot_minutes": 0},
    {"time_zone": None},
    {"courtesy_minutes": None},
    {"slot_minutes": None},
    {"day_of_week": 8},
    {"open_time": "invalid"},
    {"restaurant_id": 2},
    {"id": 2},
    {"name": "Forbidden"},
    {"direction": "Forbidden"},
    {"is_active": False},
    {"unknown": "value"},
])
def test_patch_rejects_invalid_fields_without_changes(
    db, authenticated_client, settings_headers, restaurant, payload
):
    before = (restaurant.courtesy_minutes, restaurant.open_time, restaurant.close_time)
    response = authenticated_client.patch(URL, headers=settings_headers, json=payload)

    _assert_error(response, 422, "VALIDATION_ERROR")
    db.expire_all()
    stored = db.get(Restaurant, restaurant.id)
    assert (stored.courtesy_minutes, stored.open_time, stored.close_time) == before


@pytest.mark.parametrize("payload", [
    {"close_time": "12:00", "courtesy_minutes": 10},
    {"close_time": "21:00", "courtesy_minutes": 10},
    {"open_time": "20:00", "close_time": "03:00", "kitchen_close_time": "04:00"},
])
def test_patch_validates_complete_schedule_before_saving(
    db, authenticated_client, settings_headers, restaurant, payload
):
    before = (
        restaurant.courtesy_minutes, restaurant.open_time,
        restaurant.close_time, restaurant.kitchen_close_time,
    )

    response = authenticated_client.patch(URL, headers=settings_headers, json=payload)

    _assert_error(response, 422, "VALIDATION_ERROR")
    db.expire_all()
    stored = db.get(Restaurant, restaurant.id)
    assert (
        stored.courtesy_minutes, stored.open_time,
        stored.close_time, stored.kitchen_close_time,
    ) == before


def test_patch_allows_nullable_hours_and_empty_payload(
    authenticated_client, settings_headers
):
    response = authenticated_client.patch(
        URL, headers=settings_headers, json={"kitchen_close_time": None}
    )
    assert response.status_code == 200
    assert response.json()["kitchen_close_time"] is None

    unchanged = authenticated_client.patch(URL, headers=settings_headers, json={})
    assert unchanged.status_code == 200
    assert unchanged.json() == response.json()


def test_patch_requires_real_database_permission(
    db, authenticated_client, settings_headers, settings_account, restaurant
):
    before = restaurant.courtesy_minutes
    settings_account.role.permissions.clear()
    db.commit()

    response = authenticated_client.patch(
        URL, headers=settings_headers, json={"courtesy_minutes": 10}
    )

    _assert_error(response, 403, "FORBIDDEN")
    db.expire_all()
    assert db.get(Restaurant, restaurant.id).courtesy_minutes == before


@pytest.mark.parametrize("method", ["get", "patch"])
@pytest.mark.parametrize("authorization", [None, "Bearer invalid-token"])
def test_settings_requires_valid_authentication(authenticated_client, method, authorization):
    kwargs = {"headers": {"Authorization": authorization}} if authorization else {}
    if method == "patch":
        kwargs["json"] = {"courtesy_minutes": 10}

    response = getattr(authenticated_client, method)(URL, **kwargs)

    _assert_error(response, 401, "UNAUTHORIZED")


@pytest.mark.parametrize("method", ["get", "patch"])
@pytest.mark.parametrize("reason", ["expired", "inactive"])
def test_settings_rejects_expired_or_inactive_identity(
    db, authenticated_client, settings_account, settings_headers, method, reason
):
    headers = settings_headers
    if reason == "expired":
        token = create_access_token(
            {"sub": settings_account.email, "user_id": settings_account.id,
             "restaurant_id": settings_account.restaurant_id,
             "token_version": settings_account.token_version},
            expires_delta=timedelta(seconds=-1),
        )
        headers = {"Authorization": f"Bearer {token}"}
    else:
        settings_account.is_active = False
        db.commit()
    kwargs = {"headers": headers}
    if method == "patch":
        kwargs["json"] = {"courtesy_minutes": 10}

    response = getattr(authenticated_client, method)(URL, **kwargs)

    _assert_error(response, 401, "UNAUTHORIZED")


@pytest.mark.parametrize("method", ["get", "patch"])
def test_settings_missing_restaurant_with_overridden_scope_returns_404(
    authenticated_client, settings_headers, method
):
    app.dependency_overrides[get_restaurant_scope] = lambda: 999999
    kwargs = {"headers": settings_headers}
    if method == "patch":
        kwargs["json"] = {"courtesy_minutes": 10}
    try:
        response = getattr(authenticated_client, method)(URL, **kwargs)
    finally:
        app.dependency_overrides.pop(get_restaurant_scope, None)

    _assert_error(response, 404, "NOT_FOUND")


@pytest.mark.parametrize("method", ["get", "patch"])
def test_settings_missing_association_with_overridden_identity_returns_403(
    authenticated_client, method
):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=1, restaurant_id=None, email="unscoped@example.com",
        role=ROLE_ADMIN, permissions={"settings:update"},
    )
    kwargs = {"json": {"courtesy_minutes": 10}} if method == "patch" else {}
    try:
        response = getattr(authenticated_client, method)(URL, **kwargs)
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    _assert_error(response, 403, "FORBIDDEN")


def test_client_identifiers_cannot_select_another_restaurant(
    db, authenticated_client, settings_headers, settings_account, restaurant
):
    other = Restaurant(id=restaurant.id + 1, name="Other", time_zone="Europe/Madrid")
    db.add(other)
    db.commit()
    other_courtesy = other.courtesy_minutes
    token = create_access_token({
        "sub": settings_account.email, "user_id": settings_account.id,
        "restaurant_id": other.id,
        "token_version": settings_account.token_version,
    })
    forged_scope_headers = {"Authorization": f"Bearer {token}"}

    response = authenticated_client.get(
        URL, headers=forged_scope_headers, params={"restaurant_id": other.id}
    )
    assert response.status_code == 200
    assert response.json()["id"] == restaurant.id
    response = authenticated_client.patch(
        URL, headers=settings_headers, params={"restaurant_id": other.id},
        json={"courtesy_minutes": 10},
    )
    assert response.status_code == 200
    assert response.json()["id"] == restaurant.id
    db.expire_all()
    assert db.get(Restaurant, restaurant.id).courtesy_minutes == 10
    assert db.get(Restaurant, other.id).courtesy_minutes == other_courtesy


def test_settings_openapi_contract(authenticated_client):
    schema = authenticated_client.get("/openapi.json").json()
    operations = schema["paths"][URL]
    for method in ("get", "patch"):
        operation = operations[method]
        assert operation["description"]
        assert operation["security"]
        assert operation.get("parameters", []) == []
        for status in ("200", "401", "403", "404", "500"):
            assert status in operation["responses"]
        assert operation["responses"]["200"]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/RestaurantSettingsResponse"
        }
    assert operations["patch"]["responses"]["422"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ErrorResponse"
    }
    assert "settings:update" in operations["patch"]["description"]
    update = schema["components"]["schemas"]["RestaurantSettingsUpdate"]
    assert update["additionalProperties"] is False
    assert "restaurant_id" not in update["properties"]


def _read_documented_example(heading):
    path = Path(__file__).resolve().parents[1] / "docs" / "settings" / "README.md"
    section = re.search(
        rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)",
        path.read_text(encoding="utf-8"),
        re.MULTILINE | re.DOTALL,
    )
    assert section is not None, f"Missing README section: {heading}"
    content = section.group(1)
    blocks = [
        json.loads(value)
        for value in re.findall(r"```json\n(.*?)\n```", content, re.DOTALL)
    ]
    status = re.search(r"^### Response: (\d{3})$", content, re.MULTILINE)
    assert status is not None
    method = "get" if heading == "Read settings" else "patch"
    assert f"{method.upper()} `{URL}`" in content
    assert len(blocks) == (1 if method == "get" else 2)
    return method, int(status.group(1)), blocks


@pytest.fixture
def documented_restaurant(db, restaurant, settings_headers):
    restaurant.min_break_between_shifts = 30
    restaurant.day_of_week = 5
    restaurant.period = "evening"
    restaurant.direction = "Example address"
    db.commit()
    return restaurant


@pytest.mark.parametrize("example_name,heading", DOCUMENTED_SETTINGS_EXAMPLES)
def test_readme_examples_match_api_and_persisted_settings(
    db, authenticated_client, settings_headers, documented_restaurant,
    example_name, heading,
):
    method, status_code, blocks = _read_documented_example(heading)
    before = authenticated_client.get(URL, headers=settings_headers)
    assert before.status_code == 200
    kwargs = {"headers": settings_headers}
    if method == "patch":
        kwargs["json"] = blocks[0]

    response = getattr(authenticated_client, method)(URL, **kwargs)

    assert response.status_code == status_code
    assert response.json() == blocks[-1]
    with Session(bind=db.get_bind()) as verification_db:
        stored = verification_db.get(Restaurant, documented_restaurant.id)
        actual = RestaurantSettingsResponse.model_validate(stored).model_dump(
            mode="json"
        )
    assert actual == (blocks[-1] if status_code == 200 else before.json())


@pytest.mark.parametrize("example_name,heading", DOCUMENTED_SETTINGS_EXAMPLES)
def test_openapi_examples_match_readme(authenticated_client, example_name, heading):
    method, status_code, blocks = _read_documented_example(heading)
    operation = authenticated_client.get("/openapi.json").json()["paths"][URL][method]
    content = operation["responses"][str(status_code)]["content"]["application/json"]
    if method == "get":
        assert content["example"] == blocks[-1]
    else:
        request = operation["requestBody"]["content"]["application/json"]
        assert request["examples"][example_name]["value"] == blocks[0]
        assert content["examples"][example_name]["value"] == blocks[-1]
