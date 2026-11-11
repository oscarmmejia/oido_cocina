"""Reglas de horario de apertura aplicadas a las reservas.

El esquema compartido guarda el horario en ``restaurant``. No existe la tabla
``opening_hours``: el horario es una única ventana configurable con un día
opcional, hora de apertura y hora de cierre.
"""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.kernel.errors import AppError
from app.models import Restaurant


def restaurant_timezone(restaurant: Restaurant) -> ZoneInfo:
    """Devuelve la zona horaria del restaurante o un error de validación."""

    try:
        return ZoneInfo(restaurant.time_zone)
    except ZoneInfoNotFoundError as error:
        raise AppError(
            "VALIDATION_ERROR",
            "La zona horaria del restaurante no es válida",
            422,
        ) from error


def to_restaurant_timezone(value: datetime, time_zone: ZoneInfo) -> datetime:
    """Convierte un datetime a la zona del restaurante.

    Un datetime sin zona se interpreta como hora local del restaurante.
    """

    if value.tzinfo is None:
        return value.replace(tzinfo=time_zone)
    return value.astimezone(time_zone)


def calculate_end_at(start_at: datetime, slot_minutes: int) -> datetime:
    """Calcula la hora de fin a partir de la duración configurada."""

    return start_at + timedelta(minutes=slot_minutes)


def list_opening_windows(
    restaurant: Restaurant,
    local_date: date,
) -> list[tuple[datetime, datetime]]:
    """Devuelve las ventanas de apertura que pueden contener ``local_date``.

    Se incluye la ventana del día anterior para validar reservas de madrugada
    cuando el cierre es anterior a la apertura y cruza medianoche.
    """

    if restaurant.open_time is None or restaurant.close_time is None:
        return []

    if restaurant.open_time == restaurant.close_time:
        return []

    time_zone = restaurant_timezone(restaurant)
    windows: list[tuple[datetime, datetime]] = []

    for anchor_date in (local_date - timedelta(days=1), local_date):
        if (
            restaurant.day_of_week is not None
            and restaurant.day_of_week != anchor_date.isoweekday()
        ):
            continue

        window_start = datetime.combine(
            anchor_date,
            restaurant.open_time,
            tzinfo=time_zone,
        )
        close_date = (
            anchor_date + timedelta(days=1)
            if restaurant.close_time < restaurant.open_time
            else anchor_date
        )
        window_end = datetime.combine(
            close_date,
            restaurant.close_time,
            tzinfo=time_zone,
        )
        windows.append((window_start, window_end))

    windows.sort(key=lambda window: window[0])
    return windows


def is_within_opening_hours(
    restaurant: Restaurant,
    start_at: datetime,
    end_at: datetime,
) -> bool:
    """Comprueba que la reserva completa cabe en una ventana activa."""

    time_zone = restaurant_timezone(restaurant)
    local_start = to_restaurant_timezone(start_at, time_zone)
    local_end = to_restaurant_timezone(end_at, time_zone)

    for window_start, window_end in list_opening_windows(
        restaurant,
        local_start.date(),
    ):
        if local_start >= window_start and local_end <= window_end:
            return True

    return False
