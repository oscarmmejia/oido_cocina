"""Pruebas de edición de reservas con revalidación (ST-RES-03.9)."""

import pytest

pytest.importorskip(
    "app.models.reservation_model",
    reason="Requiere el esquema compartido de HU-AUT-02",
)

from datetime import datetime, time, timedelta  # noqa: E402
from zoneinfo import ZoneInfo  # noqa: E402

from sqlalchemy import select  # noqa: E402

from app.core.kernel.identity import CurrentUser, get_current_user  # noqa: E402
from app.main import app  # noqa: E402
from app.models import (  # noqa: E402
    DiningTable,
    Reservation,
    ReservationTable,
    Restaurant,
    TableCombination,
    TableCombinationTable,
)
from app.models.enums import ReservationStatus, ReservationTableStatus  # noqa: E402

TZ = ZoneInfo("Europe/Madrid")
START = datetime(2026, 1, 10, 20, 0, tzinfo=TZ)
END = datetime(2026, 1, 10, 21, 0, tzinfo=TZ)


@pytest.fixture
def open_restaurant(db, restaurant):
    restaurant.open_time = time(20, 0)
    restaurant.close_time = time(23, 0)
    restaurant.day_of_week = None
    restaurant.period = "afternoon"
    db.commit()
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


def _combination(
    db,
    restaurant,
    *,
    tables: list[DiningTable],
    capacity: int = 6,
) -> TableCombination:
    combination = TableCombination(
        restaurant_id=restaurant.id,
        name="A+B",
        capacity=capacity,
    )
    db.add(combination)
    db.flush()
    db.add_all(
        [
            TableCombinationTable(
                combination_id=combination.id,
                table_id=table.id,
            )
            for table in tables
        ]
    )
    db.flush()
    return combination


def _reservation(
    db,
    restaurant,
    *,
    status: ReservationStatus = ReservationStatus.CONFIRMED,
    tables: list[DiningTable],
    phone: str = "600000001",
    start_at: datetime = START,
    end_at: datetime = END,
) -> Reservation:
    reservation = Reservation(
        restaurant_id=restaurant.id,
        customer_name="Cliente",
        phone=phone,
        party_size=2,
        start_at=start_at,
        end_at=end_at,
        status=status.value,
    )
    db.add(reservation)
    db.flush()
    db.add_all(
        [
            ReservationTable(
                reservation_id=reservation.id,
                table_id=table.id,
                start_at=start_at,
                end_at=end_at,
                status=ReservationTableStatus.ACTIVE.value,
            )
            for table in tables
        ]
    )
    db.commit()
    return reservation


def _occupation_table_ids(db, reservation_id: int) -> list[int]:
    return list(
        db.scalars(
            select(ReservationTable.table_id)
            .where(ReservationTable.reservation_id == reservation_id)
            .order_by(ReservationTable.table_id)
        )
    )


def _refresh(db, reservation_id: int) -> Reservation:
    db.expire_all()
    return db.get(Reservation, reservation_id)


def test_edit_start_at_recalculates_end_and_interval(db, client, open_restaurant):
    table = _table(db, open_restaurant)
    reservation = _reservation(db, open_restaurant, tables=[table])
    reservation_id = reservation.id
    new_start = "2026-01-10T21:00:00+01:00"

    response = client.patch(
        f"/api/v1/reservations/{reservation_id}",
        json={"start_at": new_start},
    )

    assert response.status_code == 200
    stored = _refresh(db, reservation_id)
    assert stored.end_at - stored.start_at == timedelta(minutes=60)
    occupation = db.scalar(
        select(ReservationTable).where(
            ReservationTable.reservation_id == reservation_id
        )
    )
    assert occupation.start_at == stored.start_at
    assert occupation.end_at == stored.end_at


def test_edit_tables_replaces_occupations(db, client, open_restaurant):
    table_a = _table(db, open_restaurant, number=1)
    table_b = _table(db, open_restaurant, number=2)
    reservation = _reservation(db, open_restaurant, tables=[table_a])
    reservation_id = reservation.id

    response = client.patch(
        f"/api/v1/reservations/{reservation_id}",
        json={"table_ids": [table_b.id]},
    )

    assert response.status_code == 200
    assert [table["table_id"] for table in response.json()["tables"]] == [
        table_b.id
    ]
    assert _occupation_table_ids(db, reservation_id) == [table_b.id]


def test_edit_combination_occupies_all_tables(db, client, open_restaurant):
    table_a = _table(db, open_restaurant, number=1)
    table_b = _table(db, open_restaurant, number=2)
    combination = _combination(db, open_restaurant, tables=[table_a, table_b])
    reservation = _reservation(db, open_restaurant, tables=[table_a])
    reservation_id = reservation.id

    response = client.patch(
        f"/api/v1/reservations/{reservation_id}",
        json={"combination_id": combination.id},
    )

    assert response.status_code == 200
    assert response.json()["reservation"]["combination_id"] == combination.id
    assert _occupation_table_ids(db, reservation_id) == [
        table_a.id,
        table_b.id,
    ]


def test_edit_party_size_revalidates_capacity(db, client, open_restaurant):
    table = _table(db, open_restaurant, max_capacity=4)
    reservation = _reservation(db, open_restaurant, tables=[table])
    reservation_id = reservation.id

    response = client.patch(
        f"/api/v1/reservations/{reservation_id}",
        json={"party_size": 5},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "CAPACITY_EXCEEDED"
    assert _refresh(db, reservation_id).party_size == 2


def test_edit_outside_opening_hours_is_rejected(db, client, open_restaurant):
    table = _table(db, open_restaurant)
    reservation = _reservation(db, open_restaurant, tables=[table])
    reservation_id = reservation.id

    response = client.patch(
        f"/api/v1/reservations/{reservation_id}",
        json={"start_at": "2026-01-10T12:00:00+01:00"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "OUTSIDE_OPENING_HOURS"
    stored = _refresh(db, reservation_id)
    assert stored.start_at == START.astimezone(stored.start_at.tzinfo)


def test_edit_duplicate_contact_is_rejected(db, client, open_restaurant):
    table_a = _table(db, open_restaurant, number=1)
    table_b = _table(db, open_restaurant, number=2)
    reservation = _reservation(db, open_restaurant, tables=[table_a])
    reservation_id = reservation.id
    _reservation(
        db,
        open_restaurant,
        status=ReservationStatus.SEATED,
        tables=[table_b],
        phone="600000099",
    )

    response = client.patch(
        f"/api/v1/reservations/{reservation_id}",
        json={"phone": "600 000 099"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "DUPLICATE_RESERVATION"
    assert _refresh(db, reservation_id).phone == "600000001"


def test_edit_overlap_preserves_old_tables(db, client, open_restaurant):
    table_a = _table(db, open_restaurant, number=1)
    table_b = _table(db, open_restaurant, number=2)
    reservation = _reservation(db, open_restaurant, tables=[table_a])
    reservation_id = reservation.id
    _reservation(
        db,
        open_restaurant,
        tables=[table_b],
        phone="600000099",
    )

    response = client.patch(
        f"/api/v1/reservations/{reservation_id}",
        json={"table_ids": [table_b.id]},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "TABLE_NOT_AVAILABLE"
    assert _occupation_table_ids(db, reservation_id) == [table_a.id]


def test_edit_final_state_is_rejected(db, client, open_restaurant):
    table = _table(db, open_restaurant)
    reservation = _reservation(
        db,
        open_restaurant,
        status=ReservationStatus.COMPLETED,
        tables=[table],
    )
    reservation_id = reservation.id

    response = client.patch(
        f"/api/v1/reservations/{reservation_id}",
        json={"party_size": 3},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "RESERVATION_NOT_EDITABLE"
    assert _refresh(db, reservation_id).party_size == 2


def test_edit_seated_is_rejected(db, client, open_restaurant):
    table = _table(db, open_restaurant)
    reservation = _reservation(
        db,
        open_restaurant,
        status=ReservationStatus.SEATED,
        tables=[table],
    )
    reservation_id = reservation.id

    response = client.patch(
        f"/api/v1/reservations/{reservation_id}",
        json={"party_size": 3},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "RESERVATION_NOT_EDITABLE"


def test_edit_requires_permission(forbidden_client):
    response = forbidden_client.patch(
        "/api/v1/reservations/9999",
        json={"party_size": 2},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_edit_missing_reservation_returns_404(client, open_restaurant):
    response = client.patch(
        "/api/v1/reservations/9999",
        json={"party_size": 2},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESERVATION_NOT_FOUND"


def test_edit_foreign_reservation_returns_404(db, client, open_restaurant):
    other = Restaurant(id=2, name="Otro", time_zone="Europe/Madrid")
    db.add(other)
    db.flush()
    table = _table(db, other)
    reservation = _reservation(db, other, tables=[table])

    response = client.patch(
        f"/api/v1/reservations/{reservation.id}",
        json={"party_size": 3},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESERVATION_NOT_FOUND"


def test_edit_empty_payload_returns_422(db, client, open_restaurant):
    table = _table(db, open_restaurant)
    reservation = _reservation(db, open_restaurant, tables=[table])

    response = client.patch(
        f"/api/v1/reservations/{reservation.id}",
        json={},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_edit_customer_and_notes_keeps_occupations(db, client, open_restaurant):
    table = _table(db, open_restaurant)
    reservation = _reservation(db, open_restaurant, tables=[table])
    reservation_id = reservation.id
    occupation_ids = list(
        db.scalars(
            select(ReservationTable.id).where(
                ReservationTable.reservation_id == reservation_id
            )
        )
    )

    response = client.patch(
        f"/api/v1/reservations/{reservation_id}",
        json={
            "customer_name": "Ana actualizada",
            "notes": "Mesa junto a la ventana",
        },
    )

    assert response.status_code == 200
    assert response.json()["reservation"]["customer_name"] == "Ana actualizada"
    assert response.json()["reservation"]["notes"] == "Mesa junto a la ventana"
    assert list(
        db.scalars(
            select(ReservationTable.id).where(
                ReservationTable.reservation_id == reservation_id
            )
        )
    ) == occupation_ids
