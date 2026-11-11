"""Creación transaccional de reservas y sus ocupaciones."""

from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.kernel.errors import AppError
from app.models import (
    DiningTable,
    Reservation,
    ReservationStatusHistory,
    ReservationTable,
    Restaurant,
)
from app.models.enums import ReservationStatus, ReservationTableStatus
from app.modules.reservations.repositories import reservation as reservation_repo
from app.modules.reservations.repositories.reservation import ReservationDetail
from app.modules.reservations.schemas.reservation import ReservationCreate
from app.modules.reservations.services.validation import (
    ValidatedReservation,
    lock_contact,
    validate_reservation,
)


def _translate_integrity_error(error: IntegrityError) -> AppError:
    """Traduce las violaciones de integridad relevantes a errores de negocio."""

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
        "No se pudo guardar la reserva",
        500,
    )


def _ensure_locked_selection(
    restaurant: Restaurant,
    validated: ValidatedReservation,
    locked_tables: list[DiningTable],
    party_size: int,
) -> None:
    """Revalida bajo bloqueo que la selección sigue siendo válida."""

    expected_ids = {table.id for table in validated.tables}
    locked_ids = {table.id for table in locked_tables}
    if expected_ids != locked_ids:
        raise AppError(
            "TABLE_NOT_FOUND",
            "No existe alguna de las mesas indicadas",
            404,
        )

    for table in locked_tables:
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

    if validated.combination is not None:
        capacity = validated.combination.capacity
    else:
        capacity = sum(table.max_capacity for table in locked_tables)

    if party_size > capacity:
        raise AppError(
            "CAPACITY_EXCEEDED",
            f"La capacidad máxima de la selección es {capacity}",
            422,
        )


def _ensure_tables_available(
    db: Session,
    table_ids: list[int],
    start_at: datetime,
    end_at: datetime,
) -> None:
    conflicts = reservation_repo.list_table_conflicts(
        db,
        table_ids,
        start_at,
        end_at,
    )
    if conflicts:
        raise AppError(
            "TABLE_NOT_AVAILABLE",
            "Alguna de las mesas ya está ocupada en esa franja",
            409,
        )


def create_reservation(
    db: Session,
    restaurant: Restaurant,
    payload: ReservationCreate,
    *,
    created_by_user_id: int | None = None,
) -> ReservationDetail:
    """Crea reserva, ocupaciones e historial inicial en una sola transacción.

    ``end_at`` procede de la validación y se calcula con ``slot_minutes``.
    ``created_at`` lo fija la base de datos y ``created_by_user_id`` solo se
    escribe en esta operación; el esquema de actualización rechaza ambos
    campos para que no puedan modificarse posteriormente.
    """

    try:
        lock_contact(db, restaurant, payload.phone, payload.email)
        validated = validate_reservation(db, restaurant, payload)
        table_ids = [table.id for table in validated.tables]

        locked_tables = reservation_repo.lock_tables(db, table_ids)
        _ensure_locked_selection(
            restaurant,
            validated,
            locked_tables,
            payload.party_size,
        )
        _ensure_tables_available(
            db,
            table_ids,
            validated.start_at,
            validated.end_at,
        )

        reservation = Reservation(
            restaurant_id=restaurant.id,
            created_by_user_id=created_by_user_id,
            combination_id=(
                validated.combination.id
                if validated.combination is not None
                else None
            ),
            customer_name=payload.customer_name,
            phone=payload.phone,
            email=payload.email,
            party_size=payload.party_size,
            start_at=validated.start_at,
            end_at=validated.end_at,
            status=ReservationStatus.CONFIRMED.value,
            notes=payload.notes,
        )
        reservation_repo.add_reservation(db, reservation)

        for table in validated.tables:
            reservation_repo.add_occupation(
                db,
                ReservationTable(
                    reservation_id=reservation.id,
                    table_id=table.id,
                    start_at=validated.start_at,
                    end_at=validated.end_at,
                    status=ReservationTableStatus.ACTIVE.value,
                ),
            )

        reservation_repo.add_history(
            db,
            ReservationStatusHistory(
                reservation_id=reservation.id,
                previous_status=None,
                new_status=ReservationStatus.CONFIRMED.value,
                changed_by_user_id=created_by_user_id,
                reason="Reserva creada",
            ),
        )

        reservation_id = reservation.id
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
        reservation_id,
        restaurant.id,
    )
    if detail is None:
        raise AppError(
            "RESERVATION_NOT_FOUND",
            "No se pudo recuperar la reserva creada",
            500,
        )

    return detail
