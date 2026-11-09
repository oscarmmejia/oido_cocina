"""Pruebas de las ventanas de apertura usadas por las reservas."""

import pytest

pytest.importorskip(
    "app.models.reservation_model",
    reason="Requiere el esquema compartido de HU-AUT-02",
)

from datetime import date, datetime, time, timezone  # noqa: E402
from zoneinfo import ZoneInfo  # noqa: E402

from app.models import OpeningHours  # noqa: E402
from app.modules.reservations.services.opening_hours import (  # noqa: E402
    calculate_end_at,
    is_within_opening_hours,
    list_opening_windows,
    restaurant_timezone,
    to_restaurant_timezone,
)

TZ = ZoneInfo("Europe/Madrid")
MONDAY = date(2026, 1, 5)
TUESDAY = date(2026, 1, 6)


def _add_hours(
    db,
    restaurant,
    *,
    day_of_week: int,
    period: str,
    open_time: time,
    close_time: time,
    is_active: bool = True,
) -> OpeningHours:
    row = OpeningHours(
        restaurant_id=restaurant.id,
        day_of_week=day_of_week,
        period=period,
        open_time=open_time,
        close_time=close_time,
        is_active=is_active,
    )
    db.add(row)
    db.flush()
    return row


def _at(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute), tzinfo=TZ)


def test_valid_reservation_inside_morning_window(db, restaurant):
    _add_hours(
        db,
        restaurant,
        day_of_week=1,
        period="morning",
        open_time=time(13, 0),
        close_time=time(16, 0),
    )

    assert is_within_opening_hours(
        db,
        restaurant,
        _at(MONDAY, 14, 0),
        _at(MONDAY, 15, 0),
    )


def test_reservation_before_opening_is_rejected(db, restaurant):
    _add_hours(
        db,
        restaurant,
        day_of_week=1,
        period="morning",
        open_time=time(13, 0),
        close_time=time(16, 0),
    )

    assert not is_within_opening_hours(
        db,
        restaurant,
        _at(MONDAY, 12, 30),
        _at(MONDAY, 13, 30),
    )


def test_reservation_ending_after_close_is_rejected(db, restaurant):
    _add_hours(
        db,
        restaurant,
        day_of_week=1,
        period="morning",
        open_time=time(13, 0),
        close_time=time(16, 0),
    )

    assert not is_within_opening_hours(
        db,
        restaurant,
        _at(MONDAY, 15, 30),
        _at(MONDAY, 16, 30),
    )


def test_inactive_window_is_ignored(db, restaurant):
    _add_hours(
        db,
        restaurant,
        day_of_week=1,
        period="morning",
        open_time=time(13, 0),
        close_time=time(16, 0),
        is_active=False,
    )

    assert not is_within_opening_hours(
        db,
        restaurant,
        _at(MONDAY, 14, 0),
        _at(MONDAY, 15, 0),
    )


def test_day_without_windows_is_rejected(db, restaurant):
    assert not is_within_opening_hours(
        db,
        restaurant,
        _at(MONDAY, 14, 0),
        _at(MONDAY, 15, 0),
    )


def test_second_window_is_considered(db, restaurant):
    _add_hours(
        db,
        restaurant,
        day_of_week=1,
        period="morning",
        open_time=time(13, 0),
        close_time=time(16, 0),
    )
    _add_hours(
        db,
        restaurant,
        day_of_week=1,
        period="afternoon",
        open_time=time(20, 0),
        close_time=time(23, 0),
    )

    assert is_within_opening_hours(
        db,
        restaurant,
        _at(MONDAY, 21, 0),
        _at(MONDAY, 22, 0),
    )


def test_overnight_window_contains_reservation_after_midnight(db, restaurant):
    _add_hours(
        db,
        restaurant,
        day_of_week=1,
        period="afternoon",
        open_time=time(20, 0),
        close_time=time(2, 0),
    )

    assert is_within_opening_hours(
        db,
        restaurant,
        _at(TUESDAY, 1, 0),
        _at(TUESDAY, 2, 0),
    )


def test_overnight_window_does_not_contain_reservation_after_close(db, restaurant):
    _add_hours(
        db,
        restaurant,
        day_of_week=1,
        period="afternoon",
        open_time=time(20, 0),
        close_time=time(2, 0),
    )

    assert not is_within_opening_hours(
        db,
        restaurant,
        _at(TUESDAY, 2, 30),
        _at(TUESDAY, 3, 0),
    )


def test_reservation_crossing_midnight_inside_overnight_window(db, restaurant):
    _add_hours(
        db,
        restaurant,
        day_of_week=1,
        period="afternoon",
        open_time=time(20, 0),
        close_time=time(2, 0),
    )

    assert is_within_opening_hours(
        db,
        restaurant,
        _at(MONDAY, 23, 30),
        _at(TUESDAY, 0, 30),
    )


def test_aware_start_is_converted_to_restaurant_timezone(db, restaurant):
    _add_hours(
        db,
        restaurant,
        day_of_week=1,
        period="morning",
        open_time=time(13, 0),
        close_time=time(16, 0),
    )

    utc_start = datetime(2026, 1, 5, 13, 0, tzinfo=timezone.utc)
    utc_end = datetime(2026, 1, 5, 14, 0, tzinfo=timezone.utc)

    assert is_within_opening_hours(db, restaurant, utc_start, utc_end)


def test_naive_start_is_interpreted_as_restaurant_time(db, restaurant):
    _add_hours(
        db,
        restaurant,
        day_of_week=1,
        period="morning",
        open_time=time(13, 0),
        close_time=time(16, 0),
    )

    assert is_within_opening_hours(
        db,
        restaurant,
        datetime(2026, 1, 5, 14, 0),
        datetime(2026, 1, 5, 15, 0),
    )


def test_calculate_end_at_uses_slot_minutes():
    start = _at(MONDAY, 20, 0)

    assert calculate_end_at(start, 60) == _at(MONDAY, 21, 0)
    assert calculate_end_at(start, 90) == _at(MONDAY, 21, 30)


def test_list_opening_windows_includes_previous_overnight_window(db, restaurant):
    _add_hours(
        db,
        restaurant,
        day_of_week=1,
        period="afternoon",
        open_time=time(20, 0),
        close_time=time(2, 0),
    )

    windows = list_opening_windows(db, restaurant, TUESDAY)

    assert windows == [(_at(MONDAY, 20, 0), _at(TUESDAY, 2, 0))]


def test_restaurant_timezone_and_localization(db, restaurant):
    time_zone = restaurant_timezone(restaurant)
    utc_value = datetime(2026, 1, 5, 13, 0, tzinfo=timezone.utc)

    localized = to_restaurant_timezone(utc_value, time_zone)

    assert time_zone.key == "Europe/Madrid"
    assert localized.hour == 14
    assert localized.tzinfo == time_zone
