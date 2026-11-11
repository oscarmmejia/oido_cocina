"""Pruebas de hora de fin, autoría y campos inmutables (ST-RES-03.4)."""

import pytest

pytest.importorskip(
    "app.models.reservation_model",
    reason="Requiere el esquema compartido de HU-AUT-02",
)

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from pydantic import ValidationError

from app.models import DiningTable, Role, User
from app.modules.reservations.schemas.reservation import (
    ReservationCreate,
    ReservationUpdate,
)
from app.modules.reservations.services.creation import create_reservation

TZ = ZoneInfo("Europe/Madrid")
START = datetime(2026, 1, 5, 20, 0, tzinfo=TZ)

SERVER_MANAGED_FIELDS = {
    "end_at": "2026-01-05T21:00:00+01:00",
    "status": "confirmed",
    "created_by_user_id": 1,
    "created_at": "2026-01-05T20:00:00+01:00",
    "updated_at": "2026-01-05T20:00:00+01:00",
}


@pytest.fixture
def open_restaurant(db, restaurant):
    restaurant.open_time = time(20, 0)
    restaurant.close_time = time(23, 0)
    restaurant.day_of_week = None
    restaurant.period = "afternoon"
    db.commit()
    return restaurant


def _table(db, restaurant) -> DiningTable:
    table = DiningTable(
        restaurant_id=restaurant.id,
        number=1,
        min_capacity=1,
        max_capacity=4,
        location="interior",
        is_active=True,
        adjustable_capacity=False,
    )
    db.add(table)
    db.flush()
    return table


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


def _payload(table_id: int) -> ReservationCreate:
    return ReservationCreate(
        customer_name="Ana",
        phone="600000001",
        party_size=4,
        start_at=START,
        table_ids=[table_id],
    )


@pytest.mark.parametrize("slot_minutes", [30, 60, 90, 120])
def test_end_at_uses_configured_slot_minutes(db, open_restaurant, slot_minutes):
    open_restaurant.slot_minutes = slot_minutes
    db.commit()
    table = _table(db, open_restaurant)
    user = _user(db, open_restaurant)

    detail = create_reservation(
        db,
        open_restaurant,
        _payload(table.id),
        created_by_user_id=user.id,
    )

    assert detail.reservation.end_at - detail.reservation.start_at == timedelta(
        minutes=slot_minutes
    )


def test_changing_slot_minutes_does_not_alter_existing_reservation(
    db, open_restaurant
):
    open_restaurant.slot_minutes = 60
    db.commit()
    table = _table(db, open_restaurant)
    user = _user(db, open_restaurant)
    detail = create_reservation(
        db,
        open_restaurant,
        _payload(table.id),
        created_by_user_id=user.id,
    )
    reservation = detail.reservation
    original_end = reservation.end_at

    open_restaurant.slot_minutes = 30
    db.commit()
    db.refresh(reservation)

    assert reservation.end_at == original_end
    assert reservation.end_at - reservation.start_at == timedelta(minutes=60)


def test_author_and_created_at_are_persisted(db, open_restaurant):
    table = _table(db, open_restaurant)
    user = _user(db, open_restaurant)
    user_id = user.id

    detail = create_reservation(
        db,
        open_restaurant,
        _payload(table.id),
        created_by_user_id=user_id,
    )

    assert detail.reservation.created_by_user_id == user_id
    assert detail.reservation.created_at is not None


@pytest.mark.parametrize("field,value", SERVER_MANAGED_FIELDS.items())
def test_create_schema_rejects_server_managed_fields(field, value):
    payload = {
        "customer_name": "Ana",
        "phone": "600000001",
        "party_size": 2,
        "start_at": START,
        "table_ids": [1],
        field: value,
    }

    with pytest.raises(ValidationError):
        ReservationCreate.model_validate(payload)


@pytest.mark.parametrize("field,value", SERVER_MANAGED_FIELDS.items())
def test_update_schema_rejects_server_managed_fields(field, value):
    with pytest.raises(ValidationError):
        ReservationUpdate.model_validate({field: value})


def test_update_schema_accepts_editable_fields():
    update = ReservationUpdate.model_validate(
        {
            "start_at": START,
            "party_size": 2,
            "table_ids": [1],
        }
    )

    assert update.start_at == START
    assert update.party_size == 2
    assert update.table_ids == [1]
