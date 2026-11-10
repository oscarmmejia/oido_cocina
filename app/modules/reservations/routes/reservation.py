from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database_connection import get_db
from app.core.kernel.errors import AppError
from app.core.kernel.identity import CurrentUser
from app.core.kernel.permissions import require_permission
from app.models import Restaurant
from app.models.enums import ReservationStatus
from app.modules.reservations.repositories.reservation import ReservationDetail
from app.modules.reservations.schemas.reservation import (
    ReservationDetailRead,
    ReservationTransition,
    ReservationUpdate,
)
from app.modules.reservations.services import editing as editing_service
from app.modules.reservations.services import transitions as transition_service

router = APIRouter(prefix="/reservations", tags=["reservations"])

RESERVATION_PERMISSION = "reservation:assign"

_TRANSITION_RESPONSES = {
    403: {"description": "No tienes permisos para gestionar reservas."},
    404: {"description": "No existe la reserva o pertenece a otro restaurante."},
    409: {"description": "La transición de estado no está permitida."},
}

_EDIT_RESPONSES = {
    403: {"description": "No tienes permisos para gestionar reservas."},
    404: {"description": "No existe la reserva o pertenece a otro restaurante."},
    409: {
        "description": (
            "La reserva no es editable, hay solapamiento o duplicado."
        )
    },
    422: {
        "description": (
            "Los datos no son válidos, la capacidad se excede o la reserva "
            "queda fuera de horario."
        )
    },
}


def _get_restaurant(db: Session, user: CurrentUser) -> Restaurant:
    restaurant = db.get(Restaurant, user.restaurant_id)
    if restaurant is None:
        raise AppError(
            "RESTAURANT_NOT_FOUND",
            "No existe el restaurante de la sesión",
            404,
        )
    return restaurant


def _transition(
    db: Session,
    user: CurrentUser,
    reservation_id: int,
    target: ReservationStatus,
    payload: ReservationTransition | None,
) -> ReservationDetail:
    restaurant = _get_restaurant(db, user)
    return transition_service.transition_reservation(
        db,
        restaurant,
        reservation_id,
        target,
        changed_by_user_id=user.id,
        reason=payload.reason if payload is not None else None,
    )


@router.post(
    "/{reservation_id}/confirm",
    response_model=ReservationDetailRead,
    status_code=status.HTTP_200_OK,
    summary="Confirmar una reserva",
    description="Confirma una reserva pendiente y registra la transición.",
    responses=_TRANSITION_RESPONSES,
)
def confirm_reservation(
    reservation_id: int,
    payload: ReservationTransition | None = None,
    user: CurrentUser = Depends(require_permission(RESERVATION_PERMISSION)),
    db: Session = Depends(get_db),
) -> ReservationDetailRead:
    return _transition(
        db,
        user,
        reservation_id,
        ReservationStatus.CONFIRMED,
        payload,
    )


@router.post(
    "/{reservation_id}/seat",
    response_model=ReservationDetailRead,
    status_code=status.HTTP_200_OK,
    summary="Sentar una reserva",
    description="Marca como sentada una reserva confirmada.",
    responses=_TRANSITION_RESPONSES,
)
def seat_reservation(
    reservation_id: int,
    payload: ReservationTransition | None = None,
    user: CurrentUser = Depends(require_permission(RESERVATION_PERMISSION)),
    db: Session = Depends(get_db),
) -> ReservationDetailRead:
    return _transition(
        db,
        user,
        reservation_id,
        ReservationStatus.SEATED,
        payload,
    )


@router.post(
    "/{reservation_id}/complete",
    response_model=ReservationDetailRead,
    status_code=status.HTTP_200_OK,
    summary="Completar una reserva",
    description="Completa una reserva sentada y libera todas sus mesas.",
    responses=_TRANSITION_RESPONSES,
)
def complete_reservation(
    reservation_id: int,
    payload: ReservationTransition | None = None,
    user: CurrentUser = Depends(require_permission(RESERVATION_PERMISSION)),
    db: Session = Depends(get_db),
) -> ReservationDetailRead:
    return _transition(
        db,
        user,
        reservation_id,
        ReservationStatus.COMPLETED,
        payload,
    )


@router.post(
    "/{reservation_id}/cancel",
    response_model=ReservationDetailRead,
    status_code=status.HTTP_200_OK,
    summary="Cancelar una reserva",
    description="Cancela una reserva activa y libera todas sus mesas.",
    responses=_TRANSITION_RESPONSES,
)
def cancel_reservation(
    reservation_id: int,
    payload: ReservationTransition | None = None,
    user: CurrentUser = Depends(require_permission(RESERVATION_PERMISSION)),
    db: Session = Depends(get_db),
) -> ReservationDetailRead:
    return _transition(
        db,
        user,
        reservation_id,
        ReservationStatus.CANCELLED,
        payload,
    )


@router.patch(
    "/{reservation_id}",
    response_model=ReservationDetailRead,
    status_code=status.HTTP_200_OK,
    summary="Editar una reserva",
    description=(
        "Edita fecha, hora, mesas, combinación, comensales o datos de cliente. "
        "La capacidad, el horario, los duplicados y el solapamiento se "
        "revalidan en una sola transacción."
    ),
    responses=_EDIT_RESPONSES,
)
def edit_reservation(
    reservation_id: int,
    payload: ReservationUpdate,
    user: CurrentUser = Depends(require_permission(RESERVATION_PERMISSION)),
    db: Session = Depends(get_db),
) -> ReservationDetailRead:
    restaurant = _get_restaurant(db, user)
    return editing_service.update_reservation(
        db,
        restaurant,
        reservation_id,
        payload,
    )
