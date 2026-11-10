"""Pruebas de la ruta de creación de reservas (ST-RES-03.10)."""

import pytest

pytest.importorskip(
    "app.models.reservation_model",
    reason="Requiere el esquema compartido de HU-AUT-02",
)

from datetime import datetime, time  # noqa: E402
from zoneinfo import ZoneInfo  # noqa: E402

from app.core.kernel.identity import CurrentUser, get_current_user  # noqa: E402
from app.main import app  # noqa: E402
from app.models import (  # noqa: E402
    DiningTable,
    OpeningHours,
    Reservation,
    ReservationTable,
    Role,
    User,
)
from app.models.enums import ReservationStatus, ReservationTableStatus  # noqa: E402

TZ = ZoneInfo("Europe/Madrid")
START = datetime(2026, 1, 10, 20, 0, tzinfo=TZ)
END = datetime(2026, 1, 10, 21, 0, tzinfo=TZ)


@pytest.fixture
def open_restaurant(db, restaurant):
    for day in range(1, 8):
        db.add_all(
            [
                OpeningHours(
                    restaurant_id=restaurant.id,
                    day_of_week=day,
                    period="morning",
                    open_time=time(13, 0),
                    close_time=time(16, 0),
                ),
                OpeningHours(
                    restaurant_id=restaurant.id,
                    day_of_week=day,
                    period="afternoon",
                    open_time=time(20, 0),
                    close_time=time(23, 0),
                ),
            ]
        )
    db.flush()
    return restaurant


@pytest.fixture
def forbidden_client(client):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=999,
        restaurant_id=1,
        email="sin-permisos@example.com",
        role="viewer",
        permissions=set(),
    )
    yield client


def _auth_user(db, restaurant) -> User:
    role = Role(id=1, restaurant_id=restaurant.id, name="Sala")
    user = User(
        id=1,
        restaurant_id=restaurant.id,
        role_id=1,
        name="Personal de sala",
        email="sala@example.com",
        password_hash="hash",
    )
    db.add_all([role, user])
    db.commit()
    return user


def _table(db, restaurant, *, number: int = 1, max_capacity: int = 4) -> DiningTable:
    table = DiningTable(
        restaurant_id=restaurant.id,
        number=number,
        min_capacity=1,
        max_capacity=max_capacity,
        location="interior",
        is_active=True,
        adjustable_capacity=False,
    )
    db.add(table)
    db.flush()
    return table


def _existing_reservation(
    db,
    restaurant,
    table: DiningTable,
    *,
    phone: str = "600000099",
    status: ReservationStatus = ReservationStatus.CONFIRMED,
) -> Reservation:
    reservation = Reservation(
        restaurant_id=restaurant.id,
        customer_name="Cliente existente",
        phone=phone,
        party_size=2,
        start_at=START,
        end_at=END,
        status=status.value,
    )
    db.add(reservation)
    db.flush()
    db.add(
        ReservationTable(
            reservation_id=reservation.id,
            table_id=table.id,
            start_at=START,
            end_at=END,
            status=ReservationTableStatus.ACTIVE.value,
        )
    )
    db.commit()
    return reservation


def _payload(table_id: int, **overrides) -> dict:
    payload = {
        "customer_name": "Ana",
        "phone": "600000001",
        "party_size": 2,
        "start_at": START.isoformat(),
        "table_ids": [table_id],
    }
    payload.update(overrides)
    return payload


def test_create_route_returns_201(db, client, open_restaurant):
    _auth_user(db, open_restaurant)
    table = _table(db, open_restaurant)

    response = client.post(
        "/api/v1/reservations",
        json=_payload(table.id),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["reservation"]["status"] == ReservationStatus.CONFIRMED.value
    assert body["reservation"]["created_by_user_id"] == 1
    assert [item["table_id"] for item in body["tables"]] == [table.id]
    assert body["history"][0]["new_status"] == ReservationStatus.CONFIRMED.value
    assert body["history"][0]["reason"] == "Reserva creada"


def test_create_route_requires_permission(forbidden_client):
    response = forbidden_client.post(
        "/api/v1/reservations",
        json={
            "customer_name": "Ana",
            "phone": "600000001",
            "party_size": 2,
            "start_at": START.isoformat(),
            "table_ids": [1],
        },
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_create_route_capacity_exceeded(db, client, open_restaurant):
    _auth_user(db, open_restaurant)
    table = _table(db, open_restaurant, max_capacity=2)

    response = client.post(
        "/api/v1/reservations",
        json=_payload(table.id, party_size=4),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "CAPACITY_EXCEEDED"


def test_create_route_outside_opening_hours(db, client, open_restaurant):
    _auth_user(db, open_restaurant)
    table = _table(db, open_restaurant)

    response = client.post(
        "/api/v1/reservations",
        json=_payload(
            table.id,
            start_at=datetime(2026, 1, 10, 12, 0, tzinfo=TZ).isoformat(),
        ),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "OUTSIDE_OPENING_HOURS"


def test_create_route_overlap_returns_409(db, client, open_restaurant):
    _auth_user(db, open_restaurant)
    table = _table(db, open_restaurant)
    _existing_reservation(db, open_restaurant, table)

    response = client.post(
        "/api/v1/reservations",
        json=_payload(table.id),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "TABLE_NOT_AVAILABLE"


def test_create_route_duplicate_returns_409(db, client, open_restaurant):
    _auth_user(db, open_restaurant)
    table = _table(db, open_restaurant)
    _existing_reservation(
        db,
        open_restaurant,
        table,
        phone="600000001",
        status=ReservationStatus.SEATED,
    )

    response = client.post(
        "/api/v1/reservations",
        json=_payload(table.id),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "DUPLICATE_RESERVATION"
