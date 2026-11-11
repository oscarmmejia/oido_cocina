"""Edición atómica de reservas con revalidación."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.kernel.errors import AppError
from app.models import DiningTable, Reservation, Restaurant
from app.models.enums import ReservationStatus
from app.modules.reservations.repositories import reservation as reservation_repo
from app.modules.reservations.repositories.reservation import ReservationDetail
from app.modules.reservations.schemas.reservation import ReservationUpdate
from app.modules.reservations.services.validation import (
    ValidatedReservation,
    contact_lock_keys,
    validate_reservation_update,
)

EDITABLE_STATUSES = frozenset(
    {
        ReservationStatus.PENDING.value,
        ReservationStatus.CONFIRMED.value,
    }
)

OCCUPATION_CHANGING_FIELDS = frozenset(
    {
        "start_at",
        "table_ids",
        "combination_id",
    }
)


def _translate_integrity_error(error: IntegrityError) -> AppError:
    sqlstate = getattr(error.orig, "sqlstate", None)
    diag = getattr(error.orig, "diag", None)
    constraint = getattr(diag, "constraint_name", None)

    if sqlstate == "23P01":
        return AppError(
            "TABLE_NOT_AVAILABLE",
            "Alguna de las mesas ya no está disponible",
            409,
        )

    if constraint == "uq_reservations_active_contact_date":
        return AppError(
            "DUPLICATE_RESERVATION",
            "Ya existe una reserva activa para ese contacto y franja",
            409,
        )

    if constraint == "uq_reservation_tables_reservation_table":
        return AppError(
            "VALIDATION_ERROR",
            "No se puede ocupar dos veces la misma mesa en una reserva",
            422,
        )

    return AppError(
        "INTERNAL_ERROR",
        "No se pudo actualizar la reserva",
        500,
    )


def _ensure_locked_tables(
    restaurant: Restaurant,
    validated: ValidatedReservation,
    locked_tables: list[DiningTable],
    party_size: int,
) -> None:
    """Revalida bajo bloqueo las mesas destino de la edición."""

    locked_by_id = {table.id: table for table in locked_tables}
    for table in validated.tables:
        locked_table = locked_by_id.get(table.id)
        if locked_table is None:
            raise AppError(
                "TABLE_NOT_FOUND",
                "No existe alguna de las mesas indicadas",
                404,
            )
        if locked_table.restaurant_id != restaurant.id:
            raise AppError(
                "TABLE_NOT_FOUND",
                "No existe alguna de las mesas indicadas",
                404,
            )
        if not locked_table.is_active:
            raise AppError(
                "TABLE_NOT_AVAILABLE",
                f"La mesa {locked_table.number} no está habilitada",
                409,
            )

    if validated.combination is not None:
        capacity = validated.combination.capacity
    else:
        capacity = sum(table.max_capacity for table in validated.tables)

    if party_size > capacity:
        raise AppError(
            "CAPACITY_EXCEEDED",
            f"La capacidad máxima de la selección es {capacity}",
            422,
        )


def update_reservation(
    db: Session,
    restaurant: Restaurant,
    reservation_id: int,
    payload: ReservationUpdate,
) -> ReservationDetail:
    """Edita una reserva y reemplaza sus ocupaciones de forma atómica."""

    if not payload.model_fields_set:
        raise AppError(
            "VALIDATION_ERROR",
            "No se ha indicado ningún campo para actualizar",
            422,
        )

    try:
        reservation = reservation_repo.get_reservation(
            db,
            reservation_id,
            restaurant.id,
            for_update=True,
        )
        if reservation is None:
            raise AppError(
                "RESERVATION_NOT_FOUND",
                "No existe la reserva indicada",
                404,
            )

        if reservation.status not in EDITABLE_STATUSES:
            raise AppError(
                "RESERVATION_NOT_EDITABLE",
                "La reserva no puede editarse en su estado actual",
                409,
            )

        fields_set = payload.model_fields_set
        effective_phone = (
            payload.phone if "phone" in fields_set else reservation.phone
        )
        effective_email = (
            payload.email if "email" in fields_set else reservation.email
        )
        reservation_repo.acquire_advisory_locks(
            db,
            restaurant.id,
            contact_lock_keys(reservation.phone, reservation.email)
            + contact_lock_keys(effective_phone, effective_email),
        )

        validated = validate_reservation_update(
            db,
            restaurant,
            reservation,
            payload,
        )
        current_table_ids = reservation_repo.list_active_occupation_table_ids(
            db,
            reservation.id,
        )
        lock_ids = sorted(
            set(current_table_ids) | {table.id for table in validated.tables}
        )
        locked_tables = reservation_repo.lock_tables(db, lock_ids)

        party_size = (
            payload.party_size
            if "party_size" in fields_set
            else reservation.party_size
        )
        _ensure_locked_tables(
            restaurant,
            validated,
            locked_tables,
            party_size,
        )

        conflicts = reservation_repo.list_table_conflicts(
            db,
            [table.id for table in validated.tables],
            validated.start_at,
            validated.end_at,
            exclude_reservation_id=reservation.id,
        )
        if conflicts:
            raise AppError(
                "TABLE_NOT_AVAILABLE",
                "Alguna de las mesas ya está ocupada en esa franja",
                409,
            )

        for field in ("customer_name", "phone", "email", "party_size", "notes"):
            if field in fields_set:
                setattr(reservation, field, getattr(payload, field))

        reservation.start_at = validated.start_at
        reservation.end_at = validated.end_at
        reservation.combination_id = (
            validated.combination.id
            if validated.combination is not None
            else None
        )

        if OCCUPATION_CHANGING_FIELDS & fields_set:
            reservation_repo.replace_occupations(
                db,
                reservation.id,
                [table.id for table in validated.tables],
                validated.start_at,
                validated.end_at,
            )

        committed_reservation_id = reservation.id
        db.commit()
    except AppError:
        db.rollback()
        raise
    except IntegrityError as error:
        db.rollback()
        raise _translate_integrity_error(error) from error
    except Exception:
        db.rollback()
        raise

    detail = reservation_repo.get_reservation_detail(
        db,
        committed_reservation_id,
        restaurant.id,
    )
    if detail is None:
        raise AppError(
            "RESERVATION_NOT_FOUND",
            "No se pudo recuperar la reserva actualizada",
            500,
        )

    return detail
