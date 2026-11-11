"""Pruebas de transiciones con historial y auditoría (ST-RES-03.7)."""

import pytest

pytest.importorskip(
    "app.models.reservation_model",
    reason="Requiere el esquema compartido de HU-AUT-02",
)

from datetime import datetime, timezone  # noqa: E402

from sqlalchemy import func, select  # noqa: E402

from app.core.kernel.errors import AppError  # noqa: E402
from app.models import (  # noqa: E402
    AuditLog,
    Reservation,
    ReservationStatusHistory,
    Restaurant,
    Role,
    User,
)
from app.models.enums import ReservationStatus  # noqa: E402
from app.modules.reservations.repositories import audit as audit_repo  # noqa: E402
from app.modules.reservations.services.transitions import (  # noqa: E402
    transition_reservation,
)

START = datetime(2026, 1, 10, 20, 0, tzinfo=timezone.utc)
END = datetime(2026, 1, 10, 21, 0, tzinfo=timezone.utc)

VALID_TRANSITIONS = [
    (ReservationStatus.PENDING, ReservationStatus.CONFIRMED),
    (ReservationStatus.PENDING, ReservationStatus.CANCELLED),
    (ReservationStatus.CONFIRMED, ReservationStatus.SEATED),
    (ReservationStatus.CONFIRMED, ReservationStatus.CANCELLED),
    (ReservationStatus.CONFIRMED, ReservationStatus.NO_SHOW),
    (ReservationStatus.SEATED, ReservationStatus.COMPLETED),
]


def _user(db, restaurant) -> User:
    role = Role(restaurant_id=restaurant.id, name="Sala")
    db.add(role)
    db.flush()
    user = User(
        restaurant_id=restaurant.id,
        role_id=role.id,
        name="Personal de sala",
        email="sala@example.com",
        password_hash="hash",
    )
    db.add(user)
    db.flush()
    return user


def _reservation(
    db,
    restaurant,
    *,
    status: ReservationStatus,
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
    db.commit()
    return reservation


def _history(db, reservation_id: int) -> list[ReservationStatusHistory]:
    return list(
        db.scalars(
            select(ReservationStatusHistory)
            .where(ReservationStatusHistory.reservation_id == reservation_id)
            .order_by(
                ReservationStatusHistory.changed_at,
                ReservationStatusHistory.id,
            )
        )
    )


def _audit_logs(db, reservation_id: int) -> list[AuditLog]:
    return list(
        db.scalars(
            select(AuditLog).where(
                AuditLog.entity_name == "reservation",
                AuditLog.entity_id == str(reservation_id),
            )
        )
    )


@pytest.mark.parametrize("initial,target", VALID_TRANSITIONS)
def test_valid_transition_persists_history_and_audit(db, restaurant, initial, target):
    user = _user(db, restaurant)
    reservation = _reservation(db, restaurant, status=initial)
    reservation_id = reservation.id
    user_id = user.id

    detail = transition_reservation(
        db,
        restaurant,
        reservation_id,
        target,
        changed_by_user_id=user_id,
        reason="Motivo de prueba",
    )

    assert detail.reservation.status == target.value
    assert len(detail.history) == 1
    history = detail.history[0]
    assert history.previous_status == initial.value
    assert history.new_status == target.value
    assert history.changed_by_user_id == user_id
    assert history.reason == "Motivo de prueba"

    audit_logs = _audit_logs(db, reservation_id)
    assert len(audit_logs) == 1
    audit = audit_logs[0]
    assert audit.restaurant_id == restaurant.id
    assert audit.user_id == user_id
    assert audit.action == "reservation.status_changed"
    assert audit.entity_name == "reservation"
    assert audit.entity_id == str(reservation_id)
    assert audit.old_values == {"status": initial.value}
    assert audit.new_values == {
        "status": target.value,
        "reason": "Motivo de prueba",
    }
    assert audit.result == "success"


def test_invalid_transition_does_not_write_anything(db, restaurant):
    user = _user(db, restaurant)
    reservation = _reservation(db, restaurant, status=ReservationStatus.CONFIRMED)
    reservation_id = reservation.id

    with pytest.raises(AppError) as error:
        transition_reservation(
            db,
            restaurant,
            reservation_id,
            ReservationStatus.PENDING,
            changed_by_user_id=user.id,
        )

    assert error.value.code == "INVALID_RESERVATION_TRANSITION"
    assert error.value.status_code == 409
    assert db.get(Reservation, reservation_id).status == ReservationStatus.CONFIRMED.value
    assert _history(db, reservation_id) == []
    assert _audit_logs(db, reservation_id) == []


@pytest.mark.parametrize(
    "initial",
    [
        ReservationStatus.COMPLETED,
        ReservationStatus.CANCELLED,
        ReservationStatus.NO_SHOW,
    ],
)
def test_final_states_are_immutable(db, restaurant, initial):
    user = _user(db, restaurant)
    reservation = _reservation(db, restaurant, status=initial)
    reservation_id = reservation.id

    with pytest.raises(AppError) as error:
        transition_reservation(
            db,
            restaurant,
            reservation_id,
            ReservationStatus.CONFIRMED,
            changed_by_user_id=user.id,
        )

    assert error.value.code == "INVALID_RESERVATION_TRANSITION"
    assert error.value.status_code == 409
    assert db.get(Reservation, reservation_id).status == initial.value
    assert _history(db, reservation_id) == []
    assert _audit_logs(db, reservation_id) == []


def test_missing_reservation_returns_404(db, restaurant):
    with pytest.raises(AppError) as error:
        transition_reservation(
            db,
            restaurant,
            9999,
            ReservationStatus.CONFIRMED,
        )

    assert error.value.code == "RESERVATION_NOT_FOUND"
    assert error.value.status_code == 404


def test_reservation_from_another_restaurant_returns_404(db, restaurant):
    other = Restaurant(id=2, name="Otro", time_zone="Europe/Madrid")
    db.add(other)
    db.flush()
    reservation = _reservation(db, other, status=ReservationStatus.PENDING)

    with pytest.raises(AppError) as error:
        transition_reservation(
            db,
            restaurant,
            reservation.id,
            ReservationStatus.CONFIRMED,
        )

    assert error.value.code == "RESERVATION_NOT_FOUND"
    assert error.value.status_code == 404


def test_string_target_status_is_accepted(db, restaurant):
    reservation = _reservation(db, restaurant, status=ReservationStatus.PENDING)

    detail = transition_reservation(
        db,
        restaurant,
        reservation.id,
        "confirmed",
    )

    assert detail.reservation.status == ReservationStatus.CONFIRMED.value


def test_audit_failure_rolls_back_status_and_history(db, restaurant, monkeypatch):
    user = _user(db, restaurant)
    reservation = _reservation(db, restaurant, status=ReservationStatus.CONFIRMED)
    reservation_id = reservation.id

    def failing_add_audit_log(db_session, audit_log):
        raise RuntimeError("fallo simulado de auditoría")

    monkeypatch.setattr(audit_repo, "add_audit_log", failing_add_audit_log)

    with pytest.raises(RuntimeError):
        transition_reservation(
            db,
            restaurant,
            reservation_id,
            ReservationStatus.SEATED,
            changed_by_user_id=user.id,
        )

    assert db.get(Reservation, reservation_id).status == ReservationStatus.CONFIRMED.value
    assert _history(db, reservation_id) == []
    assert _audit_logs(db, reservation_id) == []
    assert (
        db.scalar(
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.entity_id == str(reservation_id))
        )
        == 0
    )
