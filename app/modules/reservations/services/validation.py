"""Validaciones previas a la escritura de una reserva.

Este módulo no escribe ni bloquea filas. Resuelve la selección de mesas,
valida capacidad, horario y duplicados, y devuelve los datos que la creación
transaccional necesitará para persistir el agregado.
"""

from dataclasses import dataclass
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.kernel.errors import AppError
from app.models import DiningTable, Reservation, Restaurant, TableCombination
from app.models.enums import ReservationStatus
from app.modules.reservations.repositories import reservation as reservation_repo
from app.modules.reservations.schemas.reservation import (
    ReservationCreate,
    ReservationUpdate,
)
from app.modules.reservations.services.opening_hours import (
    calculate_end_at,
    is_within_opening_hours,
    restaurant_timezone,
    to_restaurant_timezone,
)

ACTIVE_RESERVATION_STATUSES = (
    ReservationStatus.PENDING.value,
    ReservationStatus.CONFIRMED.value,
    ReservationStatus.SEATED.value,
)

# TODO(HU-RES-05): una reserva pending debe dejar de bloquear en
# start_at + courtesy_minutes. La liberación y la caducidad se implementarán
# en esa historia; aquí solo se contempla como estado activo.


@dataclass(frozen=True)
class ValidatedReservation:
    """Reserva validada, todavía sin persistir."""

    start_at: datetime
    end_at: datetime
    tables: list[DiningTable]
    combination: TableCombination | None


def _validation_error(message: str) -> AppError:
    return AppError("VALIDATION_ERROR", message, 422)


def normalize_phone(phone: str) -> str:
    """Normaliza un teléfono dejando solo sus dígitos."""

    return "".join(character for character in phone if character.isdigit())


def normalize_email(email: str | None) -> str | None:
    """Normaliza un email para compararlo sin espacios ni mayúsculas."""

    if email is None:
        return None

    normalized = email.strip().lower()
    return normalized or None


def contact_lock_keys(phone: str | None, email: str | None) -> list[str]:
    """Claves de bloqueo por contacto normalizado (teléfono y/o email)."""

    keys: list[str] = []
    normalized_phone = normalize_phone(phone or "")
    normalized_email = normalize_email(email)
    if normalized_phone:
        keys.append(f"reservation:phone:{normalized_phone}")
    if normalized_email is not None:
        keys.append(f"reservation:email:{normalized_email}")
    return keys


def lock_contact(
    db: Session,
    restaurant: Restaurant,
    phone: str | None,
    email: str | None,
) -> None:
    """Serializa las reservas concurrentes del mismo contacto.

    Dos peticiones con el mismo teléfono y mesas distintas no comparten ningún
    bloqueo de mesa, así que sin esto ambas podrían superar la comprobación de
    duplicados. El lock se libera al terminar la transacción.
    """

    reservation_repo.acquire_advisory_locks(
        db,
        restaurant.id,
        contact_lock_keys(phone, email),
    )


def _load_tables(
    db: Session,
    restaurant: Restaurant,
    table_ids: list[int],
) -> list[DiningTable]:
    if not table_ids:
        raise _validation_error("Debes indicar al menos una mesa")

    if len(table_ids) != len(set(table_ids)):
        raise _validation_error("No se puede repetir una mesa")

    tables = reservation_repo.get_tables_by_ids(db, table_ids)
    if len(tables) != len(set(table_ids)):
        raise AppError(
            "TABLE_NOT_FOUND",
            "No existe alguna de las mesas indicadas",
            404,
        )

    for table in tables:
        if table.restaurant_id != restaurant.id:
            raise AppError(
                "TABLE_NOT_FOUND",
                "No existe alguna de las mesas indicadas",
                404,
            )
        if not table.is_active:
            raise AppError(
                "TABLE_NOT_AVAILABLE",
                f"La mesa {table.number} no está habilitada",
                409,
            )

    return tables


def _resolve_selection(
    db: Session,
    restaurant: Restaurant,
    table_ids: list[int],
    combination_id: int | None,
    reservation_date: date,
) -> tuple[TableCombination | None, list[DiningTable]]:
    if combination_id is not None:
        combination = reservation_repo.get_combination(
            db,
            combination_id,
            restaurant.id,
        )
        if combination is None:
            raise AppError(
                "TABLE_COMBINATION_NOT_FOUND",
                "No existe la combinación indicada",
                404,
            )

        if not combination.is_enabled:
            raise AppError(
                "COMBINATION_NOT_AVAILABLE",
                "La combinación no está habilitada",
                409,
            )

        if (
            combination.valid_from is not None
            and reservation_date < combination.valid_from
        ) or (
            combination.valid_to is not None
            and reservation_date > combination.valid_to
        ):
            raise AppError(
                "COMBINATION_NOT_AVAILABLE",
                "La combinación no está vigente para esa fecha",
                409,
            )

        combination_table_ids = reservation_repo.get_combination_table_ids(
            db,
            combination.id,
        )
        if len(combination_table_ids) < 2:
            raise AppError(
                "COMBINATION_NOT_AVAILABLE",
                "La combinación no tiene mesas suficientes",
                409,
            )

        if table_ids:
            if len(table_ids) != len(set(table_ids)):
                raise _validation_error("No se puede repetir una mesa")
            if set(table_ids) != set(combination_table_ids):
                raise _validation_error(
                    "Las mesas indicadas no coinciden con la combinación"
                )

        tables = _load_tables(db, restaurant, combination_table_ids)
        return combination, tables

    if not table_ids:
        raise _validation_error("Debes indicar mesas o una combinación")

    return None, _load_tables(db, restaurant, table_ids)


def _validate_capacity(
    party_size: int,
    tables: list[DiningTable],
    combination: TableCombination | None,
) -> None:
    if party_size < 1:
        raise _validation_error("El número de comensales debe ser positivo")

    if combination is not None:
        capacity = combination.capacity
    else:
        capacity = sum(table.max_capacity for table in tables)

    if party_size > capacity:
        raise AppError(
            "CAPACITY_EXCEEDED",
            f"La capacidad máxima de la selección es {capacity}",
            422,
        )


def _find_duplicate(
    db: Session,
    restaurant: Restaurant,
    phone: str,
    email: str | None,
    start_at: datetime,
    end_at: datetime,
    exclude_reservation_id: int | None,
) -> Reservation | None:
    normalized_phone = normalize_phone(phone)
    normalized_email = normalize_email(email)

    if not normalized_phone and normalized_email is None:
        return None

    statement = select(Reservation).where(
        Reservation.restaurant_id == restaurant.id,
        Reservation.status.in_(ACTIVE_RESERVATION_STATUSES),
        Reservation.start_at < end_at,
        Reservation.end_at > start_at,
    )
    if exclude_reservation_id is not None:
        statement = statement.where(Reservation.id != exclude_reservation_id)

    for candidate in db.scalars(statement.order_by(Reservation.id)):
        candidate_phone = normalize_phone(candidate.phone)
        candidate_email = normalize_email(candidate.email)

        phone_matches = bool(normalized_phone) and (
            normalized_phone == candidate_phone
        )
        email_matches = (
            normalized_email is not None
            and candidate_email is not None
            and normalized_email == candidate_email
        )
        if phone_matches or email_matches:
            return candidate

    return None


def validate_reservation(
    db: Session,
    restaurant: Restaurant,
    payload: ReservationCreate,
    exclude_reservation_id: int | None = None,
) -> ValidatedReservation:
    """Valida una reserva antes de escribirla.

    Devuelve las mesas resueltas y el intervalo definitivo en UTC. No hace
    ``commit``, ``flush`` ni modifica ninguna fila.
    """

    if payload.party_size is None or payload.party_size < 1:
        raise _validation_error("El número de comensales debe ser positivo")

    if payload.start_at is None:
        raise _validation_error("La fecha de inicio es obligatoria")

    time_zone = restaurant_timezone(restaurant)
    local_start = to_restaurant_timezone(payload.start_at, time_zone)
    local_end = calculate_end_at(local_start, restaurant.slot_minutes)

    table_ids = list(payload.table_ids or [])
    combination, tables = _resolve_selection(
        db,
        restaurant,
        table_ids,
        payload.combination_id,
        local_start.date(),
    )
    _validate_capacity(payload.party_size, tables, combination)

    if not is_within_opening_hours(restaurant, local_start, local_end):
        raise AppError(
            "OUTSIDE_OPENING_HOURS",
            "La reserva está fuera del horario de apertura",
            422,
        )

    start_utc = local_start.astimezone(timezone.utc)
    end_utc = local_end.astimezone(timezone.utc)

    duplicate = _find_duplicate(
        db,
        restaurant,
        payload.phone or "",
        payload.email,
        start_utc,
        end_utc,
        exclude_reservation_id,
    )
    if duplicate is not None:
        raise AppError(
            "DUPLICATE_RESERVATION",
            "Ya existe una reserva activa para ese contacto y franja",
            409,
        )

    return ValidatedReservation(
        start_at=start_utc,
        end_at=end_utc,
        tables=tables,
        combination=combination,
    )


def validate_reservation_update(
    db: Session,
    restaurant: Restaurant,
    reservation: Reservation,
    payload: ReservationUpdate,
) -> ValidatedReservation:
    """Valida el estado efectivo de una reserva antes de editarla.

    Los campos no enviados se toman de la reserva actual. Si cambia
    ``start_at`` se recalcula ``end_at``; si no cambia, se conserva el
    intervalo existente.
    """

    fields_set = payload.model_fields_set
    time_zone = restaurant_timezone(restaurant)

    if "start_at" in fields_set:
        local_start = to_restaurant_timezone(payload.start_at, time_zone)
        local_end = calculate_end_at(local_start, restaurant.slot_minutes)
    else:
        local_start = to_restaurant_timezone(reservation.start_at, time_zone)
        local_end = to_restaurant_timezone(reservation.end_at, time_zone)

    current_table_ids = reservation_repo.list_active_occupation_table_ids(
        db,
        reservation.id,
    )
    if "table_ids" in fields_set:
        table_ids = list(payload.table_ids or [])
    elif "combination_id" in fields_set and payload.combination_id is not None:
        table_ids = []
    else:
        table_ids = current_table_ids

    combination_id = (
        payload.combination_id
        if "combination_id" in fields_set
        else reservation.combination_id
    )
    combination, tables = _resolve_selection(
        db,
        restaurant,
        table_ids,
        combination_id,
        local_start.date(),
    )

    party_size = (
        payload.party_size
        if "party_size" in fields_set
        else reservation.party_size
    )
    _validate_capacity(party_size, tables, combination)

    if not is_within_opening_hours(restaurant, local_start, local_end):
        raise AppError(
            "OUTSIDE_OPENING_HOURS",
            "La reserva está fuera del horario de apertura",
            422,
        )

    start_utc = local_start.astimezone(timezone.utc)
    end_utc = local_end.astimezone(timezone.utc)

    phone = payload.phone if "phone" in fields_set else reservation.phone
    email = payload.email if "email" in fields_set else reservation.email
    duplicate = _find_duplicate(
        db,
        restaurant,
        phone or "",
        email,
        start_utc,
        end_utc,
        reservation.id,
    )
    if duplicate is not None:
        raise AppError(
            "DUPLICATE_RESERVATION",
            "Ya existe una reserva activa para ese contacto y franja",
            409,
        )

    return ValidatedReservation(
        start_at=start_utc,
        end_at=end_utc,
        tables=tables,
        combination=combination,
    )
