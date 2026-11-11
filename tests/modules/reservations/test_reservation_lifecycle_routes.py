"""Pruebas de las acciones del ciclo de vida (ST-RES-03.8)."""

import pytest

pytest.importorskip(
    "app.models.reservation_model",
    reason="Requiere el esquema compartido de HU-AUT-02",
)

from datetime import datetime, timezone

from sqlalchemy import func, select

from app.core.kernel.identity import CurrentUser, get_current_user
from app.main import app
from app.models import (
    AuditLog,
    DiningTable,
    Reservation,
    ReservationStatusHistory,
    ReservationTable,
    Restaurant,
    Role,
    User,
)
from app.models.enums import ReservationStatus, ReservationTableStatus
from app.modules.reservations.repositories import audit as audit_repo
from app.modules.reservations.services.transitions import (
    transition_reservation,
)

START = datetime(2026, 1, 10, 20, 0, tzinfo=timezone.utc)
END = datetime(2026, 1, 10, 21, 0, tzinfo=timezone.utc)


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


def _table(db, restaurant, *, number: int = 1) -> DiningTable:
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
    status: ReservationStatus,
    tables: list[DiningTable],
    phone: str = "600000001",
) -> Reservation:
    reservation = Reservation(
        restaurant_id=restaurant.id,
        customer_name="Cliente",
        phone=phone,
        party_size=2,
        start_at=START,
        end_at=END,
        status=status.value,
    )
    db.add(reservation)
    db.flush()
    db.add_all(
        [
            ReservationTable(
                reservation_id=reservation.id,
                table_id=table.id,
                start_at=START,
                end_at=END,
                status=ReservationTableStatus.ACTIVE.value,
            )
            for table in tables
        ]
    )
    db.commit()
    return reservation


def _occupation_statuses(db, reservation_id: int) -> list[str]:
    return list(
        db.scalars(
            select(ReservationTable.status)
            .where(ReservationTable.reservation_id == reservation_id)
            .order_by(ReservationTable.id)
        )
    )


def test_confirm_route(db, client, restaurant):
    _auth_user(db, restaurant)
    table = _table(db, restaurant)
    reservation = _reservation(
        db,
        restaurant,
        status=ReservationStatus.PENDING,
        tables=[table],
    )

    response = client.post(
        f"/api/v1/reservations/{reservation.id}/confirm",
        json={"reason": "Confirmada por el cliente"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["reservation"]["status"] == ReservationStatus.CONFIRMED.value
    assert body["tables"][0]["status"] == ReservationTableStatus.ACTIVE.value
    assert body["history"][-1]["reason"] == "Confirmada por el cliente"
    assert _occupation_statuses(db, reservation.id) == [
        ReservationTableStatus.ACTIVE.value
    ]


def test_seat_route(db, client, restaurant):
    _auth_user(db, restaurant)
    table = _table(db, restaurant)
    reservation = _reservation(
        db,
        restaurant,
        status=ReservationStatus.CONFIRMED,
        tables=[table],
    )

    response = client.post(f"/api/v1/reservations/{reservation.id}/seat")

    assert response.status_code == 200
    assert response.json()["reservation"]["status"] == ReservationStatus.SEATED.value
    assert _occupation_statuses(db, reservation.id) == [
        ReservationTableStatus.ACTIVE.value
    ]


def test_complete_route_releases_tables(db, client, restaurant):
    _auth_user(db, restaurant)
    table = _table(db, restaurant)
    reservation = _reservation(
        db,
        restaurant,
        status=ReservationStatus.SEATED,
        tables=[table],
    )

    response = client.post(f"/api/v1/reservations/{reservation.id}/complete")

    assert response.status_code == 200
    assert (
        response.json()["reservation"]["status"]
        == ReservationStatus.COMPLETED.value
    )
    assert response.json()["tables"][0]["status"] == ReservationTableStatus.CANCELLED.value
    assert _occupation_statuses(db, reservation.id) == [
        ReservationTableStatus.CANCELLED.value
    ]


def test_cancel_route_releases_all_tables(db, client, restaurant):
    _auth_user(db, restaurant)
    table_a = _table(db, restaurant, number=1)
    table_b = _table(db, restaurant, number=2)
    reservation = _reservation(
        db,
        restaurant,
        status=ReservationStatus.CONFIRMED,
        tables=[table_a, table_b],
    )

    response = client.post(
        f"/api/v1/reservations/{reservation.id}/cancel",
        json={"reason": "Cancelada por el cliente"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["reservation"]["status"] == ReservationStatus.CANCELLED.value
    assert {table["status"] for table in body["tables"]} == {
        ReservationTableStatus.CANCELLED.value
    }
    assert _occupation_statuses(db, reservation.id) == [
        ReservationTableStatus.CANCELLED.value,
        ReservationTableStatus.CANCELLED.value,
    ]


@pytest.mark.parametrize(
    "action",
    ["confirm", "seat", "complete", "cancel"],
)
def test_lifecycle_actions_require_permission(forbidden_client, action):
    response = forbidden_client.post(f"/api/v1/reservations/9999/{action}")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_invalid_transition_returns_409(db, client, restaurant):
    _auth_user(db, restaurant)
    table = _table(db, restaurant)
    reservation = _reservation(
        db,
        restaurant,
        status=ReservationStatus.CONFIRMED,
        tables=[table],
    )

    response = client.post(f"/api/v1/reservations/{reservation.id}/complete")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_RESERVATION_TRANSITION"
    assert (
        db.get(Reservation, reservation.id).status
        == ReservationStatus.CONFIRMED.value
    )


def test_missing_reservation_returns_404(client, restaurant):
    response = client.post("/api/v1/reservations/9999/confirm")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESERVATION_NOT_FOUND"


def test_foreign_reservation_returns_404(db, client, restaurant):
    other = Restaurant(id=2, name="Otro", time_zone="Europe/Madrid")
    db.add(other)
    db.flush()
    table = _table(db, other)
    reservation = _reservation(
        db,
        other,
        status=ReservationStatus.PENDING,
        tables=[table],
    )

    response = client.post(f"/api/v1/reservations/{reservation.id}/confirm")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESERVATION_NOT_FOUND"


def test_no_show_releases_tables_through_service(db, restaurant):
    user = _auth_user(db, restaurant)
    table = _table(db, restaurant)
    reservation = _reservation(
        db,
        restaurant,
        status=ReservationStatus.CONFIRMED,
        tables=[table],
    )

    detail = transition_reservation(
        db,
        restaurant,
        reservation.id,
        ReservationStatus.NO_SHOW,
        changed_by_user_id=user.id,
    )

    assert detail.reservation.status == ReservationStatus.NO_SHOW.value
    assert _occupation_statuses(db, reservation.id) == [
        ReservationTableStatus.CANCELLED.value
    ]


def test_audit_failure_rolls_back_release(db, restaurant, monkeypatch):
    user = _auth_user(db, restaurant)
    table = _table(db, restaurant)
    reservation = _reservation(
        db,
        restaurant,
        status=ReservationStatus.CONFIRMED,
        tables=[table],
    )

    def failing_add_audit_log(db_session, audit_log):
        raise RuntimeError("fallo simulado de auditoría")

    monkeypatch.setattr(audit_repo, "add_audit_log", failing_add_audit_log)

    with pytest.raises(RuntimeError):
        transition_reservation(
            db,
            restaurant,
            reservation.id,
            ReservationStatus.CANCELLED,
            changed_by_user_id=user.id,
        )

    assert (
        db.get(Reservation, reservation.id).status
        == ReservationStatus.CONFIRMED.value
    )
    assert _occupation_statuses(db, reservation.id) == [
        ReservationTableStatus.ACTIVE.value
    ]
    assert (
        db.scalar(
            select(func.count())
            .select_from(ReservationStatusHistory)
            .where(ReservationStatusHistory.reservation_id == reservation.id)
        )
        == 0
    )
    assert (
        db.scalar(
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.entity_id == str(reservation.id))
        )
        == 0
    )
