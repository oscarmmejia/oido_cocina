from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.core.kernel.identity import CurrentUser, get_current_user
from tests.conftest import TEST_RESTAURANT_ID
from app.main import app
from app.models import Restaurant
from app.models.menu_model import Menu, MenuCollection

BASE = "/api/v1/menu-collections"


@pytest.fixture
def forbidden_client(client):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=999,
        restaurant_id=TEST_RESTAURANT_ID,
        email="sin-permisos@example.com",
        role="viewer",
        permissions=set(),
    )
    yield client


def _url(collection_id=None, *, public=False):
    if public:
        path = f"{BASE}/public"
    elif collection_id is None:
        path = f"{BASE}/"
    else:
        path = f"{BASE}/{collection_id}"
    return f"{path}?restaurant_id={TEST_RESTAURANT_ID}"

def _status_url(collection_id):
    return f"{BASE}/{collection_id}/status?restaurant_id={TEST_RESTAURANT_ID}"

def _create(client, name="Mensual", **overrides):
    payload = {"name": name, "type": "seasonal"}
    payload.update(overrides)
    response = client.post(_url(), json=payload)
    assert response.status_code == 201
    return response.json()


def test_create_returns_201(client, restaurant):
    response = client.post(_url(), json={"name": "Mensual", "type": "seasonal"})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Mensual"
    assert body["type"] == "seasonal"
    assert body["is_active"] is True
    assert body["restaurant_id"] == TEST_RESTAURANT_ID


def test_create_duplicate_name_returns_409(client, restaurant):
    payload = {"name": "Mensual", "type": "fixed"}
    assert client.post(_url(), json=payload).status_code == 201

    response = client.post(_url(), json=payload)

    assert response.status_code == 409
    assert "Ya existe una colección" in response.json()["error"]["message"]


def test_create_invalid_range_returns_422(client, restaurant):
    response = client.post(
        _url(),
        json={
            "name": "Mensual",
            "type": "daily",
            "valid_from": "2026-12-31",
            "valid_to": "2026-01-01",
        },
    )

    assert response.status_code == 422


def test_create_requires_permission(forbidden_client):
    response = forbidden_client.post(_url(), json={"name": "Mensual", "type": "daily"})

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_list_returns_200(client, restaurant):
    _create(client, "Entrantes")
    _create(client, "Postres")

    response = client.get(_url())

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["Entrantes", "Postres"]


def test_get_returns_200(client, restaurant):
    created = _create(client, "Mensual")

    response = client.get(_url(created["id"]))

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_missing_returns_404(client, restaurant):
    response = client.get(_url(9999))

    assert response.status_code == 404
    assert response.json()["error"]["message"] == "Colección no encontrada"


def test_update_returns_200(client, restaurant):
    created = _create(client, "Mensual")

    response = client.patch(_url(created["id"]), json={"name": "Mensual de invierno"})

    assert response.status_code == 200
    assert response.json()["name"] == "Mensual de invierno"


def test_update_without_changes_returns_422(client, restaurant):
    created = _create(client, "Mensual")

    response = client.patch(_url(created["id"]), json={})

    assert response.status_code == 422


def test_update_duplicate_name_returns_409(client, restaurant):
    _create(client, "Entrantes")
    created = _create(client, "Postres")

    response = client.patch(_url(created["id"]), json={"name": "Entrantes"})

    assert response.status_code == 409


def test_status_update_returns_200(client, restaurant):
    created = _create(client, "Mensual")

    response = client.patch(_status_url(created["id"]), json={"is_active": False})

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_delete_empty_returns_204(client, restaurant):
    created = _create(client, "Mensual")

    response = client.delete(_url(created["id"]))

    assert response.status_code == 204
    assert response.content == b""


def test_delete_with_menus_returns_409_and_keeps_collection(db, client, restaurant):
    created = _create(client, "Mensual")
    db.add(
        Menu(
            collection_id=created["id"],
            name="Menú 1",
            own_price=Decimal("12.00"),
        )
    )
    db.commit()

    response = client.delete(_url(created["id"]))

    assert response.status_code == 409
    assert client.get(_url(created["id"])).status_code == 200


def test_delete_missing_returns_404(client, restaurant):
    response = client.delete(_url(9999))

    assert response.status_code == 404


def test_delete_from_another_restaurant_returns_404(db, client, restaurant):
    db.add(Restaurant(id=2, name="Otro", time_zone="Europe/Madrid"))
    db.flush()
    db.add(MenuCollection(restaurant_id=2, name="Ajena", type="daily"))
    db.commit()
    foreign_id = db.query(MenuCollection).filter_by(restaurant_id=2).first().id

    response = client.delete(_url(foreign_id))

    assert response.status_code == 404


def test_public_excludes_inactive_and_expired(db, client, restaurant):
    today = date.today()
    visible = _create(client, "Abierta")
    inactive = _create(client, "Cerrada")
    expired = _create(
        client,
        "Vencida",
        valid_to=(today - timedelta(days=1)).isoformat(),
    )
    client.patch(_status_url(inactive["id"]), json={"is_active": False})
    db.add(
        Menu(
            collection_id=visible["id"],
            name="Menú del día",
            own_price=Decimal("10.50"),
        )
    )
    db.commit()

    response = client.get(_url(public=True))

    assert response.status_code == 200
    body = response.json()
    assert [item["name"] for item in body] == ["Abierta"]
    assert body[0]["menus"][0]["name"] == "Menú del día"
    assert expired["name"] == "Vencida"