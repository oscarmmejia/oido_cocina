"""Pruebas de integridad del historial de estados (ST-RES-03.5)."""

import pytest

pytest.importorskip(
    "app.models.reservation_model",
    reason="Requiere el esquema compartido de HU-AUT-02",
)

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from app.models import (
    Reservation,
    ReservationStatusHistory,
    Role,
    User,
)
from app.models.enums import ReservationStatus

START = datetime(2026, 1, 10, 20, 0, tzinfo=timezone.utc)
END = datetime(2026, 1, 10, 21, 0, tzinfo=timezone.utc)


def _reservation(db, restaurant) -> Reservation:
    reservation = Reservation(
        restaurant_id=restaurant.id,
        customer_name="Cliente",
        phone="600000001",
        party_size=2,
        start_at=START,
        end_at=END,
        status=ReservationStatus.CONFIRMED.value,
    )
    db.add(reservation)
    db.flush()
    return reservation


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


def test_history_requires_existing_reservation(db, restaurant):
    history = ReservationStatusHistory(
        reservation_id=9999,
        previous_status=None,
        new_status=ReservationStatus.CONFIRMED.value,
        changed_by_user_id=None,
        reason=None,
    )
    db.add(history)

    with pytest.raises(IntegrityError):
        db.flush()

    db.rollback()


def test_history_survives_author_deletion(db, restaurant):
    user = _user(db, restaurant)
    reservation = _reservation(db, restaurant)
    history = ReservationStatusHistory(
        reservation_id=reservation.id,
        previous_status=None,
        new_status=ReservationStatus.CONFIRMED.value,
        changed_by_user_id=user.id,
        reason="Reserva creada",
    )
    db.add(history)
    db.commit()
    history_id = history.id

    assert history.changed_by_user_id == user.id

    db.delete(user)
    db.commit()

    stored = db.get(ReservationStatusHistory, history_id)

    assert stored is not None
    assert stored.changed_by_user_id is None
