"""Pruebas unitarias del servicio sin conexión a PostgreSQL."""

from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from app.core.errors.codes import ErrorCode
from app.core.kernel.errors import AppError
from app.modules.settings.models.restaurant import Restaurant
from app.modules.settings.services.restaurant_service import get_restaurant_settings


def test_get_restaurant_settings_returns_restaurant():
    db = Mock(spec=Session)
    restaurant = Restaurant(
        id=7,
        name="Restaurante de prueba",
        time_zone="Europe/Madrid",
        is_active=False,
        courtesy_minutes=10,
        slot_minutes=30,
        open_time=None,
    )
    db.get.return_value = restaurant

    result = get_restaurant_settings(db, restaurant_id=7)

    assert result is restaurant
    assert result.name == "Restaurante de prueba"
    assert result.time_zone == "Europe/Madrid"
    assert result.courtesy_minutes == 10
    assert result.slot_minutes == 30
    assert result.is_active is False
    assert result.open_time is None
    db.get.assert_called_once_with(Restaurant, 7)


def test_get_restaurant_settings_raises_when_restaurant_does_not_exist():
    db = Mock(spec=Session)
    db.get.return_value = None

    with pytest.raises(AppError) as error:
        get_restaurant_settings(db, restaurant_id=999)

    assert error.value.code == ErrorCode.NOT_FOUND.value
    assert error.value.status_code == 404
    assert error.value.message == "El restaurante con identificador 999 no existe"
    db.get.assert_called_once_with(Restaurant, 999)
