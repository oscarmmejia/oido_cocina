"""Validación de configuración conforme a los campos actuales de Restaurant."""

from datetime import time

import pytest
from pydantic import ValidationError

from app.modules.settings.models.restaurant import Restaurant
from app.modules.settings.schemas import (
    RestaurantSettingsResponse,
    RestaurantSettingsUpdate,
)


def test_update_accepts_configuration_and_preserves_omitted_fields():
    settings = RestaurantSettingsUpdate(
        time_zone="Europe/Madrid",
        courtesy_minutes=0,
        slot_minutes=1,
        min_break_between_shifts=0,
        day_of_week=7,
        period="x" * 16,
        open_time="09:00:00",
        close_time="23:00:00",
        kitchen_close_time="22:00:00",
    )

    assert settings.model_dump(exclude_unset=True) == {
        "time_zone": "Europe/Madrid",
        "courtesy_minutes": 0,
        "slot_minutes": 1,
        "min_break_between_shifts": 0,
        "day_of_week": 7,
        "period": "x" * 16,
        "open_time": time(9),
        "close_time": time(23),
        "kitchen_close_time": time(22),
    }
    assert RestaurantSettingsUpdate(slot_minutes=30).model_dump(
        exclude_unset=True
    ) == {"slot_minutes": 30}
    assert RestaurantSettingsUpdate().model_dump(exclude_unset=True) == {}


@pytest.mark.parametrize(
    "payload",
    [
        {"time_zone": "x" * 65},
        {"courtesy_minutes": -1},
        {"slot_minutes": 0},
        {"min_break_between_shifts": -1},
        {"day_of_week": 0},
        {"day_of_week": 8},
        {"period": "x" * 17},
        {"open_time": "hora inválida"},
        {"close_time": "25:00:00"},
        {"kitchen_close_time": "22:99:00"},
        {"slot_minutes": "no es un número"},
    ],
)
def test_update_rejects_values_incompatible_with_model(payload):
    with pytest.raises(ValidationError):
        RestaurantSettingsUpdate.model_validate(payload)


@pytest.mark.parametrize("field", ["time_zone", "courtesy_minutes", "slot_minutes"])
def test_update_rejects_explicit_null_for_non_nullable_fields(field):
    with pytest.raises(ValidationError):
        RestaurantSettingsUpdate.model_validate({field: None})


@pytest.mark.parametrize(
    "field",
    [
        "min_break_between_shifts",
        "day_of_week",
        "period",
        "open_time",
        "close_time",
        "kitchen_close_time",
    ],
)
def test_update_accepts_explicit_null_for_nullable_fields(field):
    settings = RestaurantSettingsUpdate.model_validate({field: None})
    assert settings.model_dump(exclude_unset=True) == {field: None}


@pytest.mark.parametrize(
    "field",
    ["name", "is_active", "direction", "id", "restaurant_id", "curtesy_minutes", "unknown"],
)
def test_update_rejects_protected_identifiers_and_unknown_fields(field):
    with pytest.raises(ValidationError) as error:
        RestaurantSettingsUpdate.model_validate({field: 1})
    assert error.value.errors()[0]["type"] == "extra_forbidden"


def test_update_does_not_add_timezone_period_or_hour_order_restrictions():
    settings = RestaurantSettingsUpdate(
        time_zone="x" * 64,
        day_of_week=1,
        period="personalizado",
        open_time="23:00:00",
        close_time="02:00:00",
    )
    assert settings.time_zone == "x" * 64
    assert settings.close_time == time(2)


def test_response_reads_existing_restaurant_attributes():
    restaurant = Restaurant(
        id=7,
        name="Restaurante de prueba",
        time_zone="Europe/Madrid",
        is_active=True,
        courtesy_minutes=5,
        slot_minutes=60,
        open_time=time(9),
        direction="Calle de prueba",
    )

    response = RestaurantSettingsResponse.model_validate(restaurant)

    assert response.id == 7
    assert response.name == "Restaurante de prueba"
    assert response.direction == "Calle de prueba"
    assert response.courtesy_minutes == 5
    assert response.open_time == time(9)
    assert response.period is None
    assert response.model_dump(mode="json")["open_time"] == "09:00:00"
