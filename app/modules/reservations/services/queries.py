"""Consultas de reservas con ámbito por restaurante y cliente."""

from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.kernel.errors import AppError
from app.core.kernel.identity import CurrentUser
from app.models import Reservation, Restaurant
from app.models.enums import ReservationStatus
from app.modules.reservations.repositories import reservation as reservation_repo
from app.modules.reservations.repositories.reservation import ReservationDetail
from app.modules.reservations.services.opening_hours import restaurant_timezone
from app.modules.reservations.services.validation import normalize_email

RESERVATION_PERMISSION = "reservation:assign"


def is_staff(user: CurrentUser) -> bool:
    """Indica si el usuario puede gestionar todas las reservas."""

    return "*" in user.permissions or RESERVATION_PERMISSION in user.permissions


def _client_email(user: CurrentUser) -> str | None:
    return normalize_email(user.email)


def _day_start(day: date, time_zone) -> datetime:
    return datetime.combine(day, time.min, tzinfo=time_zone).astimezone(
        timezone.utc
    )


def list_reservations(
    db: Session,
    restaurant: Restaurant,
    user: CurrentUser,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    reservation_status: ReservationStatus | None = None,
    table_id: int | None = None,
    customer: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Reservation], int]:
    """Lista reservas aplicando filtros, paginación y ámbito."""

    if date_from is not None and date_to is not None and date_from > date_to:
        raise AppError(
            "VALIDATION_ERROR",
            "date_from no puede ser posterior a date_to",
            422,
        )

    time_zone = restaurant_timezone(restaurant)
    start_from = _day_start(date_from, time_zone) if date_from else None
    start_to = (
        _day_start(date_to + timedelta(days=1), time_zone)
        if date_to is not None
        else None
    )

    customer_email = None
    if not is_staff(user):
        customer_email = _client_email(user)
        if customer_email is None:
            return [], 0

    return reservation_repo.list_reservations(
        db,
        restaurant_id=restaurant.id,
        status=(
            reservation_status.value
            if reservation_status is not None
            else None
        ),
        table_id=table_id,
        customer=customer,
        customer_email=customer_email,
        start_from=start_from,
        start_to=start_to,
        offset=(page - 1) * page_size,
        limit=page_size,
    )


def get_reservation_detail_for_user(
    db: Session,
    restaurant: Restaurant,
    user: CurrentUser,
    reservation_id: int,
) -> ReservationDetail:
    """Devuelve el detalle si el usuario puede verlo."""

    detail = reservation_repo.get_reservation_detail(
        db,
        reservation_id,
        restaurant.id,
    )
    if detail is None:
        raise AppError(
            "RESERVATION_NOT_FOUND",
            "No existe la reserva indicada",
            404,
        )

    if not is_staff(user):
        user_email = _client_email(user)
        reservation_email = normalize_email(detail.reservation.email)
        if (
            user_email is None
            or reservation_email is None
            or user_email != reservation_email
        ):
            raise AppError(
                "RESERVATION_NOT_FOUND",
                "No existe la reserva indicada",
                404,
            )

    return detail
