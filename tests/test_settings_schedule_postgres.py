"""Persistencia y rechazo atómico de horarios en PostgreSQL local."""

from datetime import time

import pytest
from sqlalchemy.orm import Session

from app.core.database_connection import engine
from app.core.kernel.errors import AppError
from app.modules.settings.models.restaurant import Restaurant
from app.modules.settings.schemas import RestaurantSettingsUpdate
from app.modules.settings.services.restaurant_service import update_restaurant_settings


@pytest.fixture
def db():
    assert engine.url.host in ("localhost", "127.0.0.1"), (
        "Esta prueba no debe ejecutarse sobre una base remota."
    )
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            with Session(
                bind=connection, join_transaction_mode="create_savepoint"
            ) as session:
                yield session
        finally:
            transaction.rollback()


@pytest.fixture
def restaurant(db):
    restaurant = Restaurant(
        name="Prueba OICO-46",
        time_zone="Europe/Madrid",
        open_time=time(20),
        kitchen_close_time=time(2),
        close_time=time(3),
    )
    db.add(restaurant)
    db.flush()
    return restaurant


@pytest.mark.parametrize(
    "opening,kitchen,closing",
    [(time(9), time(16), time(17)), (time(20), time(2), time(3))],
)
def test_valid_schedule_persists(db, restaurant, opening, kitchen, closing):
    restaurant_id = restaurant.id

    update_restaurant_settings(
        db,
        restaurant_id,
        RestaurantSettingsUpdate(
            open_time=opening,
            kitchen_close_time=kitchen,
            close_time=closing,
            courtesy_minutes=0,
        ),
    )
    db.expire_all()
    stored = db.get(Restaurant, restaurant_id)

    assert stored.open_time == opening
    assert stored.kitchen_close_time == kitchen
    assert stored.close_time == closing
    assert stored.courtesy_minutes == 0


@pytest.mark.parametrize(
    "payload", [{"kitchen_close_time": "04:00"}, {"close_time": "20:00"}]
)
def test_invalid_schedule_never_dirties_or_persists_partial_changes(db, restaurant, payload):
    restaurant_id = restaurant.id

    with pytest.raises(AppError) as error:
        update_restaurant_settings(
            db, restaurant_id, RestaurantSettingsUpdate(**payload, slot_minutes=30)
        )

    assert error.value.code == "VALIDATION_ERROR"
    assert error.value.status_code == 422
    assert restaurant not in db.dirty
    assert restaurant.slot_minutes == 60
    assert restaurant.kitchen_close_time == time(2)
    assert restaurant.close_time == time(3)

    db.commit()
    db.expire_all()
    stored = db.get(Restaurant, restaurant_id)
    assert stored.slot_minutes == 60
    assert stored.kitchen_close_time == time(2)
    assert stored.close_time == time(3)

    update_restaurant_settings(
        db,
        restaurant_id,
        RestaurantSettingsUpdate(close_time="01:00", kitchen_close_time="00:30"),
    )
    db.expire_all()
    stored = db.get(Restaurant, restaurant_id)
    assert stored.close_time == time(1)
    assert stored.kitchen_close_time == time(0, 30)
