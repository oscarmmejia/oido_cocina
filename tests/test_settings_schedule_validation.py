"""Coherencia de horarios aplicada a la configuración completa de un PATCH."""

from datetime import time
from unittest.mock import Mock

import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.kernel.errors import AppError
from app.modules.settings.models.restaurant import Restaurant
from app.modules.settings.schemas import RestaurantSettingsUpdate
from app.modules.settings.services.restaurant_service import update_restaurant_settings


@pytest.fixture
def restaurant():
    return Restaurant(
        id=7,
        name="Prueba OICO-46",
        time_zone="Europe/Madrid",
        courtesy_minutes=5,
        slot_minutes=60,
        open_time=time(20),
        kitchen_close_time=time(2),
        close_time=time(3),
    )


@pytest.mark.parametrize(
    "opening,kitchen,closing",
    [
        (time(9), time(16), time(17)),
        (time(20), time(2), time(3)),
        (time(20), time(23), time(3)),
        (time(20), time(3), time(3)),
        (time(20), time(2, 59), time(3)),
        (time(20), time(0), time(0)),
        (time(9), time(17), time(17)),
        (time(9, 0, 0, 1), time(9, 0, 0, 2), time(9, 0, 0, 2)),
        (time(23, 59, 59, 999999), time(0, 0, 0, 1), time(0, 0, 0, 2)),
        (None, time(2), time(3)),
        (None, time(3), time(3)),
        (time(20), None, time(3)),
        (time(20), time(2), None),
        (None, None, None),
    ],
)
def test_valid_normal_overnight_and_nullable_schedules(
    restaurant, opening, kitchen, closing
):
    db = Mock(spec=Session)
    db.get.return_value = restaurant

    result = update_restaurant_settings(
        db,
        7,
        RestaurantSettingsUpdate(
            open_time=opening, kitchen_close_time=kitchen, close_time=closing
        ),
    )

    assert result.open_time == opening
    assert result.kitchen_close_time == kitchen
    assert result.close_time == closing
    db.commit.assert_called_once_with()


@pytest.mark.parametrize(
    "payload",
    [
        {"open_time": "09:00", "kitchen_close_time": "18:00", "close_time": "17:00"},
        {"kitchen_close_time": "04:00"},
        {"kitchen_close_time": "19:00"},
        {"close_time": "20:00"},
        {"open_time": "03:00"},
        {"close_time": "01:00"},
        {"open_time": None, "kitchen_close_time": "23:00", "close_time": "03:00"},
        {"open_time": "09:00", "kitchen_close_time": "09:00:00.000002", "close_time": "09:00:00.000001"},
        {"open_time": "20:00:00.000001", "close_time": "20:00:00.000001"},
    ],
)
def test_invalid_candidate_leaves_all_attributes_untouched(restaurant, payload):
    db = Mock(spec=Session)
    db.get.return_value = restaurant
    before = {
        field: getattr(restaurant, field)
        for field in RestaurantSettingsUpdate.model_fields
    }

    with pytest.raises(AppError) as error:
        update_restaurant_settings(
            db, 7, RestaurantSettingsUpdate(**payload, slot_minutes=30)
        )

    assert error.value.code == "VALIDATION_ERROR"
    assert error.value.status_code == 422
    assert error.value.message
    assert {
        field: getattr(restaurant, field)
        for field in RestaurantSettingsUpdate.model_fields
    } == before
    db.commit.assert_not_called()
    db.flush.assert_not_called()
    db.refresh.assert_not_called()
    db.rollback.assert_not_called()


def test_partial_opening_update_uses_stored_closing_times(restaurant):
    db = Mock(spec=Session)
    db.get.return_value = restaurant

    result = update_restaurant_settings(
        db, 7, RestaurantSettingsUpdate(open_time="21:00")
    )

    assert result.open_time == time(21)
    assert result.kitchen_close_time == time(2)
    assert result.close_time == time(3)
    db.commit.assert_called_once_with()


def test_simultaneous_update_validates_final_combination(restaurant):
    db = Mock(spec=Session)
    db.get.return_value = restaurant

    result = update_restaurant_settings(
        db,
        7,
        RestaurantSettingsUpdate(close_time="01:00", kitchen_close_time="00:30"),
    )

    assert result.close_time == time(1)
    assert result.kitchen_close_time == time(0, 30)
    db.commit.assert_called_once_with()


@pytest.mark.parametrize("payload", [{}, {"slot_minutes": 30}])
def test_existing_invalid_schedule_is_checked_even_without_hour_changes(restaurant, payload):
    restaurant.close_time = restaurant.open_time
    db = Mock(spec=Session)
    db.get.return_value = restaurant

    with pytest.raises(AppError) as error:
        update_restaurant_settings(db, 7, RestaurantSettingsUpdate(**payload))

    assert error.value.code == "VALIDATION_ERROR"
    assert restaurant.slot_minutes == 60
    db.commit.assert_not_called()


def test_valid_empty_patch_does_not_commit(restaurant):
    db = Mock(spec=Session)
    db.get.return_value = restaurant

    assert update_restaurant_settings(db, 7, RestaurantSettingsUpdate()) is restaurant
    db.commit.assert_not_called()


def test_negative_courtesy_is_rejected_by_existing_schema():
    with pytest.raises(ValidationError):
        RestaurantSettingsUpdate(courtesy_minutes=-1)


def test_complete_candidate_revalidates_stored_courtesy(restaurant):
    restaurant.courtesy_minutes = -1
    db = Mock(spec=Session)
    db.get.return_value = restaurant

    with pytest.raises(AppError) as error:
        update_restaurant_settings(db, 7, RestaurantSettingsUpdate(slot_minutes=30))

    assert error.value.code == "VALIDATION_ERROR"
    assert error.value.status_code == 422
    assert "courtesy_minutes" in error.value.message
    assert restaurant.slot_minutes == 60
    db.commit.assert_not_called()


def test_zero_courtesy_is_valid(restaurant):
    db = Mock(spec=Session)
    db.get.return_value = restaurant

    result = update_restaurant_settings(
        db, 7, RestaurantSettingsUpdate(courtesy_minutes=0)
    )

    assert result.courtesy_minutes == 0
    db.commit.assert_called_once_with()
