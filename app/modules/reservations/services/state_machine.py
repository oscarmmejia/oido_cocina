"""Máquina de estados pura de la reserva.

No accede a base de datos ni escribe historial. La persistencia atómica de las
transiciones corresponde a la capa de servicio que consuma estas funciones.
"""

from app.core.kernel.errors import AppError
from app.models.enums import ReservationStatus

FINAL_STATUSES = frozenset(
    {
        ReservationStatus.COMPLETED,
        ReservationStatus.CANCELLED,
        ReservationStatus.NO_SHOW,
    }
)

ALLOWED_TRANSITIONS: dict[
    ReservationStatus,
    frozenset[ReservationStatus],
] = {
    ReservationStatus.PENDING: frozenset(
        {
            ReservationStatus.CONFIRMED,
            ReservationStatus.CANCELLED,
        }
    ),
    ReservationStatus.CONFIRMED: frozenset(
        {
            ReservationStatus.SEATED,
            ReservationStatus.CANCELLED,
            ReservationStatus.NO_SHOW,
        }
    ),
    ReservationStatus.SEATED: frozenset(
        {
            ReservationStatus.COMPLETED,
        }
    ),
    ReservationStatus.COMPLETED: frozenset(),
    ReservationStatus.CANCELLED: frozenset(),
    ReservationStatus.NO_SHOW: frozenset(),
}


def coerce_status(status: ReservationStatus | str) -> ReservationStatus:
    """Normaliza un estado de reserva a ``ReservationStatus``."""

    if isinstance(status, ReservationStatus):
        return status

    try:
        return ReservationStatus(status)
    except ValueError as error:
        raise AppError(
            "INVALID_RESERVATION_TRANSITION",
            f"Estado de reserva desconocido: {status}",
            409,
        ) from error


def is_final_status(status: ReservationStatus | str) -> bool:
    """Indica si la reserva está en un estado terminal."""

    return coerce_status(status) in FINAL_STATUSES


def allowed_targets(
    status: ReservationStatus | str,
) -> frozenset[ReservationStatus]:
    """Devuelve los estados alcanzables desde el estado indicado."""

    return ALLOWED_TRANSITIONS[coerce_status(status)]


def can_transition(
    current: ReservationStatus | str,
    target: ReservationStatus | str,
) -> bool:
    """Indica si la transición está permitida."""

    current_status = coerce_status(current)
    target_status = coerce_status(target)
    return target_status in ALLOWED_TRANSITIONS[current_status]


def ensure_transition_allowed(
    current: ReservationStatus | str,
    target: ReservationStatus | str,
) -> None:
    """Valida la transición o lanza un conflicto de negocio."""

    current_status = coerce_status(current)
    target_status = coerce_status(target)

    if target_status in ALLOWED_TRANSITIONS[current_status]:
        return

    if current_status in FINAL_STATUSES:
        message = (
            f"La reserva está en estado final ({current_status.value}) "
            "y no puede modificarse"
        )
    else:
        message = (
            "Transición no permitida: "
            f"{current_status.value} -> {target_status.value}"
        )

    raise AppError(
        "INVALID_RESERVATION_TRANSITION",
        message,
        409,
    )
