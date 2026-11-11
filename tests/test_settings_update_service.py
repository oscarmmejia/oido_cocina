"""Pruebas de actualización parcial sin conexión a PostgreSQL."""

from datetime import time
from unittest.mock import Mock

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.kernel.errors import AppError
from app.modules.settings.models.restaurant import Restaurant
from app.modules.settings.schemas import RestaurantSettingsUpdate
from app.modules.settings.services.restaurant_service import update_restaurant_settings


@pytest.fixture
def restaurant():
    return Restaurant(
        id=7,
        name="Nombre original",
        direction="Dirección original",
        is_active=False,
        time_zone="Europe/Madrid",
        courtesy_minutes=5,
        slot_minutes=60,
        min_break_between_shifts=15,
        day_of_week=1,
        period="comida",
        open_time=time(12),
        close_time=time(17),
        kitchen_close_time=time(16),
    )


def test_update_changes_only_supplied_configuration(restaurant):
    db = Mock(spec=Session)
    db.get.return_value = restaurant

    result = update_restaurant_settings(
        db, 7, RestaurantSettingsUpdate(slot_minutes=30, courtesy_minutes=0)
    )

    assert result is restaurant
    assert result.slot_minutes == 30
    assert result.courtesy_minutes == 0
    assert result.time_zone == "Europe/Madrid"
    assert result.min_break_between_shifts == 15
    assert result.day_of_week == 1
    assert result.period == "comida"
    assert result.open_time == time(12)
    assert result.close_time == time(17)
    assert result.kitchen_close_time == time(16)
    assert result.id == 7
    assert result.name == "Nombre original"
    assert result.direction == "Dirección original"
    assert result.is_active is False
    db.get.assert_called_once_with(
        Restaurant, 7, with_for_update=True, populate_existing=True
    )
    db.commit.assert_called_once_with()
    db.refresh.assert_called_once_with(restaurant)
    db.rollback.assert_not_called()


def test_update_clears_explicit_nullable_field(restaurant):
    db = Mock(spec=Session)
    db.get.return_value = restaurant

    result = update_restaurant_settings(
        db, 7, RestaurantSettingsUpdate(open_time=None)
    )

    assert result.open_time is None
    assert result.close_time == time(17)
    db.commit.assert_called_once_with()


def test_empty_update_returns_existing_configuration_without_commit(restaurant):
    db = Mock(spec=Session)
    db.get.return_value = restaurant

    result = update_restaurant_settings(db, 7, RestaurantSettingsUpdate())

    assert result is restaurant
    assert result.slot_minutes == 60
    db.commit.assert_not_called()
    db.refresh.assert_not_called()


@pytest.mark.parametrize("payload", [{}, {"slot_minutes": 30}])
def test_update_missing_restaurant_reuses_not_found_error(payload):
    db = Mock(spec=Session)
    db.get.return_value = None

    with pytest.raises(AppError) as error:
        update_restaurant_settings(db, 999, RestaurantSettingsUpdate(**payload))

    assert error.value.code == "NOT_FOUND"
    assert error.value.status_code == 404
    assert error.value.message == "El restaurante con identificador 999 no existe"
    db.commit.assert_not_called()
    db.refresh.assert_not_called()


def test_update_rolls_back_and_propagates_database_failure(restaurant):
    db = Mock(spec=Session)
    db.get.return_value = restaurant
    failure = SQLAlchemyError("Fallo de persistencia")
    db.commit.side_effect = failure

    with pytest.raises(SQLAlchemyError) as error:
        update_restaurant_settings(db, 7, RestaurantSettingsUpdate(slot_minutes=30))

    assert error.value is failure
    db.rollback.assert_called_once_with()
    db.refresh.assert_not_called()
