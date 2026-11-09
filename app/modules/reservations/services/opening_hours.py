"""Reglas de horario de apertura aplicadas a las reservas.

La configuración vive en ``opening_hours`` (esquema compartido de HU-AUT-02).
Cada fila representa una franja de un día concreto; un día puede tener varias
franjas y una franja puede cruzar medianoche.
"""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.kernel.errors import AppError
from app.models import OpeningHours, Restaurant


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
    db: Session,
    restaurant: Restaurant,
    local_date: date,
) -> list[tuple[datetime, datetime]]:
    """Devuelve las ventanas de apertura que pueden contener ``local_date``.

    Se incluyen las franjas del día anterior para poder validar reservas de
    madrugada que pertenecen a una franja nocturna que cruza medianoche.
    """

    time_zone = restaurant_timezone(restaurant)
    previous_date = local_date - timedelta(days=1)

    rows = list(
        db.scalars(
            select(OpeningHours).where(
                OpeningHours.restaurant_id == restaurant.id,
                OpeningHours.is_active.is_(True),
                OpeningHours.day_of_week.in_(
                    (local_date.isoweekday(), previous_date.isoweekday())
                ),
            )
        )
    )

    windows: list[tuple[datetime, datetime]] = []
    for row in rows:
        anchor_date = (
            local_date
            if row.day_of_week == local_date.isoweekday()
            else previous_date
        )
        window_start = datetime.combine(
            anchor_date,
            row.open_time,
            tzinfo=time_zone,
        )
        close_date = (
            anchor_date + timedelta(days=1)
            if row.close_time <= row.open_time
            else anchor_date
        )
        window_end = datetime.combine(
            close_date,
            row.close_time,
            tzinfo=time_zone,
        )
        windows.append((window_start, window_end))

    windows.sort(key=lambda window: window[0])
    return windows


def is_within_opening_hours(
    db: Session,
    restaurant: Restaurant,
    start_at: datetime,
    end_at: datetime,
) -> bool:
    """Comprueba que la reserva completa cabe en una sola ventana activa."""

    time_zone = restaurant_timezone(restaurant)
    local_start = to_restaurant_timezone(start_at, time_zone)
    local_end = to_restaurant_timezone(end_at, time_zone)

    for window_start, window_end in list_opening_windows(
        db,
        restaurant,
        local_start.date(),
    ):
        if local_start >= window_start and local_end <= window_end:
            return True

    return False
