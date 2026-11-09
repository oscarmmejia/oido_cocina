"""Transiciones de estado con historial y auditoría atómicos."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.kernel.errors import AppError
from app.models import AuditLog, ReservationStatusHistory, Restaurant
from app.models.enums import ReservationStatus
from app.modules.reservations.repositories import audit as audit_repo
from app.modules.reservations.repositories import reservation as reservation_repo
from app.modules.reservations.repositories.reservation import ReservationDetail
from app.modules.reservations.services.state_machine import (
    coerce_status,
    ensure_transition_allowed,
)

AUDIT_ACTION = "reservation.status_changed"
AUDIT_ENTITY = "reservation"


def transition_reservation(
    db: Session,
    restaurant: Restaurant,
    reservation_id: int,
    target_status: ReservationStatus | str,
    *,
    changed_by_user_id: int | None = None,
    reason: str | None = None,
) -> ReservationDetail:
    """Aplica una transición y guarda estado, historial y auditoría juntos."""

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

        previous_status = reservation.status
        target = coerce_status(target_status)
        ensure_transition_allowed(previous_status, target)

        reservation.status = target.value
        reservation_repo.add_history(
            db,
            ReservationStatusHistory(
                reservation_id=reservation.id,
                previous_status=previous_status,
                new_status=target.value,
                changed_by_user_id=changed_by_user_id,
                reason=reason,
            ),
        )
        audit_repo.add_audit_log(
            db,
            AuditLog(
                restaurant_id=restaurant.id,
                user_id=changed_by_user_id,
                action=AUDIT_ACTION,
                entity_name=AUDIT_ENTITY,
                entity_id=str(reservation.id),
                old_values={"status": previous_status},
                new_values={"status": target.value, "reason": reason},
                result="success",
            ),
        )

        committed_reservation_id = reservation.id
        db.commit()
    except AppError:
        db.rollback()
        raise
    except IntegrityError as error:
        db.rollback()
        raise AppError(
            "INTERNAL_ERROR",
            "No se pudo registrar la transición de la reserva",
            500,
        ) from error
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
