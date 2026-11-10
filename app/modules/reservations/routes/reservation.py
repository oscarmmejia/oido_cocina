from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database_connection import get_db
from app.core.kernel.errors import AppError
from app.core.kernel.identity import CurrentUser, get_current_user
from app.core.kernel.permissions import require_permission
from app.models import Restaurant
from app.models.enums import ReservationStatus
from app.modules.reservations.repositories.reservation import ReservationDetail
from app.modules.reservations.schemas.reservation import (
    ReservationCreate,
    ReservationDetailRead,
    ReservationList,
    ReservationTransition,
    ReservationUpdate,
)
from app.modules.reservations.services import creation as creation_service
from app.modules.reservations.services import editing as editing_service
from app.modules.reservations.services import queries as query_service
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

_CREATE_RESPONSES = {
    403: {"description": "No tienes permisos para gestionar reservas."},
    404: {"description": "No existe alguna de las mesas o el restaurante."},
    409: {
        "description": (
            "Alguna mesa ya está ocupada o existe una reserva duplicada."
        )
    },
    422: {
        "description": (
            "Los datos no son válidos, la capacidad se excede o la reserva "
            "queda fuera de horario."
        )
    },
}

_LIST_RESPONSES = {
    422: {"description": "Los filtros o la paginación no son válidos."},
}

_DETAIL_RESPONSES = {
    404: {"description": "No existe la reserva o no es visible para el usuario."},
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
    "",
    response_model=ReservationDetailRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una reserva",
    description=(
        "Registra una reserva confirmada con una o varias mesas. Valida "
        "horario, capacidad, combinación, solapamiento y duplicados en una "
        "sola transacción."
    ),
    responses=_CREATE_RESPONSES,
)
def create_reservation(
    payload: ReservationCreate,
    user: CurrentUser = Depends(require_permission(RESERVATION_PERMISSION)),
    db: Session = Depends(get_db),
) -> ReservationDetailRead:
    restaurant = _get_restaurant(db, user)
    return creation_service.create_reservation(
        db,
        restaurant,
        payload,
        created_by_user_id=user.id,
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


@router.get(
    "",
    response_model=ReservationList,
    status_code=status.HTTP_200_OK,
    summary="Listar reservas",
    description=(
        "Devuelve las reservas visibles para el usuario con filtros por rango "
        "de fechas, estado, mesa y cliente, y paginación."
    ),
    responses=_LIST_RESPONSES,
)
def list_reservations(
    date_from: date | None = Query(
        default=None,
        description="Fecha local inicial, inclusive.",
    ),
    date_to: date | None = Query(
        default=None,
        description="Fecha local final, inclusive.",
    ),
    reservation_status: ReservationStatus | None = Query(
        default=None,
        alias="status",
        description="Estado de la reserva.",
    ),
    table_id: int | None = Query(
        default=None,
        gt=0,
        description="Mesa asociada a la reserva.",
    ),
    customer: str | None = Query(
        default=None,
        min_length=1,
        description="Búsqueda por nombre, teléfono o email.",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReservationList:
    restaurant = _get_restaurant(db, user)
    items, total = query_service.list_reservations(
        db,
        restaurant,
        user,
        date_from=date_from,
        date_to=date_to,
        reservation_status=reservation_status,
        table_id=table_id,
        customer=customer,
        page=page,
        page_size=page_size,
    )
    return ReservationList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{reservation_id}",
    response_model=ReservationDetailRead,
    status_code=status.HTTP_200_OK,
    summary="Consultar una reserva",
    description=(
        "Devuelve la reserva con sus ocupaciones e historial de estados. Un "
        "cliente solo puede consultar sus propias reservas."
    ),
    responses=_DETAIL_RESPONSES,
)
def get_reservation(
    reservation_id: int,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReservationDetailRead:
    restaurant = _get_restaurant(db, user)
    return query_service.get_reservation_detail_for_user(
        db,
        restaurant,
        user,
        reservation_id,
    )
