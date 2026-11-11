"""Pruebas de listado, filtros y detalle de reservas (ST-RES-03.10)."""

import pytest

pytest.importorskip(
    "app.models.reservation_model",
    reason="Requiere el esquema compartido de HU-AUT-02",
)

from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.kernel.identity import CurrentUser, get_current_user
from app.main import app
from app.models import (
    DiningTable,
    Reservation,
    ReservationStatusHistory,
    ReservationTable,
    Restaurant,
)
from app.models.enums import ReservationStatus, ReservationTableStatus

TZ = ZoneInfo("Europe/Madrid")
DAY_10 = datetime(2026, 1, 10, 20, 0, tzinfo=TZ)
DAY_11 = datetime(2026, 1, 11, 20, 0, tzinfo=TZ)
DAY_12 = datetime(2026, 1, 12, 20, 0, tzinfo=TZ)


@pytest.fixture
def client_user(client):
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=2,
        restaurant_id=1,
        email="cliente@example.com",
        role="cliente",
        permissions=set(),
    )
    yield client


@pytest.fixture
def seeded_reservations(db, restaurant):
    table_a = _table(db, restaurant, number=1)
    table_b = _table(db, restaurant, number=2)
    table_c = _table(db, restaurant, number=3)

    reservation_a = _reservation(
        db,
        restaurant,
        customer_name="Ana",
        phone="600000001",
        email="cliente@example.com",
        status=ReservationStatus.CONFIRMED,
        start_at=DAY_10,
        tables=[table_a],
    )
    reservation_b = _reservation(
        db,
        restaurant,
        customer_name="Luis",
        phone="600000002",
        email="otro@example.com",
        status=ReservationStatus.PENDING,
        start_at=DAY_11,
        tables=[table_b],
    )
    reservation_c = _reservation(
        db,
        restaurant,
        customer_name="Carmen",
        phone="600000003",
        email="tercero@example.com",
        status=ReservationStatus.CANCELLED,
        start_at=DAY_12,
        tables=[table_c],
    )
    _add_history(
        db,
        reservation_a,
        previous_status=None,
        new_status=ReservationStatus.PENDING,
        reason="Reserva creada",
    )
    _add_history(
        db,
        reservation_a,
        previous_status=ReservationStatus.PENDING,
        new_status=ReservationStatus.CONFIRMED,
        reason="Confirmada",
    )
    db.commit()

    return {
        "a": reservation_a,
        "b": reservation_b,
        "c": reservation_c,
        "table_a": table_a,
    }


def _table(db, restaurant, *, number: int) -> DiningTable:
    table = DiningTable(
        restaurant_id=restaurant.id,
        number=number,
        min_capacity=1,
        max_capacity=4,
        location="interior",
        is_active=True,
        adjustable_capacity=False,
    )
    db.add(table)
    db.flush()
    return table


def _reservation(
    db,
    restaurant,
    *,
    customer_name: str,
    phone: str,
    email: str | None,
    status: ReservationStatus,
    start_at: datetime,
    tables: list[DiningTable],
) -> Reservation:
    end_at = start_at.replace(hour=start_at.hour + 1)
    reservation = Reservation(
        restaurant_id=restaurant.id,
        customer_name=customer_name,
        phone=phone,
        email=email,
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
    db.flush()
    return reservation


def _add_history(
    db,
    reservation: Reservation,
    *,
    previous_status: ReservationStatus | None,
    new_status: ReservationStatus,
    reason: str,
) -> None:
    db.add(
        ReservationStatusHistory(
            reservation_id=reservation.id,
            previous_status=(
                previous_status.value
                if previous_status is not None
                else None
            ),
            new_status=new_status.value,
            changed_by_user_id=None,
            reason=reason,
        )
    )


def _phones(response) -> list[str]:
    return [item["phone"] for item in response.json()["items"]]


def test_list_returns_all_restaurant_reservations(client, seeded_reservations):
    response = client.get("/api/v1/reservations")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert _phones(response) == ["600000001", "600000002", "600000003"]


def test_list_filters_by_date_range(client, seeded_reservations):
    response = client.get(
        "/api/v1/reservations",
        params={
            "date_from": "2026-01-10",
            "date_to": "2026-01-11",
        },
    )

    assert response.status_code == 200
    assert _phones(response) == ["600000001", "600000002"]


def test_list_filters_by_date_from_only(client, seeded_reservations):
    response = client.get(
        "/api/v1/reservations",
        params={"date_from": "2026-01-11"},
    )

    assert response.status_code == 200
    assert _phones(response) == ["600000002", "600000003"]


def test_list_filters_by_date_to_only(client, seeded_reservations):
    response = client.get(
        "/api/v1/reservations",
        params={"date_to": "2026-01-10"},
    )

    assert response.status_code == 200
    assert _phones(response) == ["600000001"]


def test_list_invalid_date_range_returns_422(client, seeded_reservations):
    response = client.get(
        "/api/v1/reservations",
        params={
            "date_from": "2026-01-12",
            "date_to": "2026-01-10",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_list_filters_by_status(client, seeded_reservations):
    response = client.get(
        "/api/v1/reservations",
        params={"status": "confirmed"},
    )

    assert response.status_code == 200
    assert _phones(response) == ["600000001"]


def test_list_filters_by_table(client, seeded_reservations):
    response = client.get(
        "/api/v1/reservations",
        params={"table_id": seeded_reservations["table_a"].id},
    )

    assert response.status_code == 200
    assert _phones(response) == ["600000001"]


def test_list_filters_by_customer(client, seeded_reservations):
    response = client.get(
        "/api/v1/reservations",
        params={"customer": "Luis"},
    )

    assert response.status_code == 200
    assert _phones(response) == ["600000002"]


def test_list_paginates(client, seeded_reservations):
    first = client.get(
        "/api/v1/reservations",
        params={"page": 1, "page_size": 2},
    )
    second = client.get(
        "/api/v1/reservations",
        params={"page": 2, "page_size": 2},
    )

    assert first.status_code == 200
    assert first.json()["total"] == 3
    assert _phones(first) == ["600000001", "600000002"]
    assert second.status_code == 200
    assert _phones(second) == ["600000003"]


def test_detail_returns_tables_and_history(client, seeded_reservations):
    reservation_id = seeded_reservations["a"].id

    response = client.get(f"/api/v1/reservations/{reservation_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["reservation"]["phone"] == "600000001"
    assert len(body["tables"]) == 1
    assert body["tables"][0]["table_id"] == seeded_reservations["table_a"].id
    assert len(body["history"]) == 2
    assert body["history"][0]["reason"] == "Reserva creada"


def test_detail_missing_returns_404(client, seeded_reservations):
    response = client.get("/api/v1/reservations/9999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESERVATION_NOT_FOUND"


def test_detail_foreign_restaurant_returns_404(db, client, seeded_reservations):
    other = Restaurant(id=2, name="Otro", time_zone="Europe/Madrid")
    db.add(other)
    db.flush()
    table = _table(db, other, number=1)
    reservation = _reservation(
        db,
        other,
        customer_name="Externo",
        phone="600000099",
        email="cliente@example.com",
        status=ReservationStatus.CONFIRMED,
        start_at=DAY_10,
        tables=[table],
    )
    db.commit()

    response = client.get(f"/api/v1/reservations/{reservation.id}")

    assert response.status_code == 404


def test_client_only_lists_own_reservations(client_user, seeded_reservations):
    response = client_user.get("/api/v1/reservations")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert _phones(response) == ["600000001"]


def test_client_can_read_own_reservation(client_user, seeded_reservations):
    reservation_id = seeded_reservations["a"].id

    response = client_user.get(f"/api/v1/reservations/{reservation_id}")

    assert response.status_code == 200
    assert response.json()["reservation"]["phone"] == "600000001"


def test_client_cannot_read_other_reservation(client_user, seeded_reservations):
    reservation_id = seeded_reservations["b"].id

    response = client_user.get(f"/api/v1/reservations/{reservation_id}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESERVATION_NOT_FOUND"


def test_client_cannot_read_foreign_restaurant(
    db,
    client_user,
    seeded_reservations,
):
    other = Restaurant(id=2, name="Otro", time_zone="Europe/Madrid")
    db.add(other)
    db.flush()
    table = _table(db, other, number=1)
    reservation = _reservation(
        db,
        other,
        customer_name="Externo",
        phone="600000099",
        email="cliente@example.com",
        status=ReservationStatus.CONFIRMED,
        start_at=DAY_10,
        tables=[table],
    )
    db.commit()

    response = client_user.get(f"/api/v1/reservations/{reservation.id}")

    assert response.status_code == 404


def test_list_validates_page(client, seeded_reservations):
    response = client.get("/api/v1/reservations", params={"page": 0})

    assert response.status_code == 422


def test_list_validates_page_size(client, seeded_reservations):
    response = client.get("/api/v1/reservations", params={"page_size": 101})

    assert response.status_code == 422
