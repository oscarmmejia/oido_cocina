from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database_connection import get_db
from app.core.kernel.errors import ErrorResponse
from app.core.kernel.identity import CurrentUser, get_current_user
from app.core.kernel.permissions import require_permission
from app.modules.schedules.schemas.work_shift import WorkShiftCreate, WorkShiftRead
from app.modules.schedules.services import work_shift as shift_service

router = APIRouter(prefix="/schedules/{schedule_id}/shifts", tags=["Work shifts"])

manage = Depends(require_permission("schedule:manage"))
ScheduleId = Annotated[int, Path(gt=0, description="ID del cuadrante.", examples=[1])]
ShiftId = Annotated[int, Path(gt=0, description="ID del turno.", examples=[10])]
EmployeeFilter = Annotated[
    int | None,
    Query(gt=0, description="Muestra solo los turnos de este empleado.", examples=[3]),
]
DateFrom = Annotated[
    date | None,
    Query(description="Fecha local inicial (YYYY-MM-DD), inclusive.", examples=["2026-11-09"]),
]
DateTo = Annotated[
    date | None,
    Query(description="Fecha local final (YYYY-MM-DD), inclusive.", examples=["2026-11-15"]),
]

CONFLICT_RESPONSES = {
    404: {"model": ErrorResponse, "description": "Cuadrante o turno no encontrado."},
    409: {
        "model": ErrorResponse,
        "description": (
            "SCHEDULE_NOT_EDITABLE (cuadrante publicado), SHIFT_OVERLAP (solape), "
            "SHIFT_BREAK_TOO_SHORT (descanso insuficiente) o EMPLOYEE_INACTIVE."
        ),
    },
}


@router.post(
    "",
    response_model=WorkShiftRead,
    status_code=status.HTTP_201_CREATED,
    summary="Añadir turno a un cuadrante en borrador",
    description=(
        "Valida que el turno caiga dentro del periodo, que el empleado esté activo "
        "y que no solape ni quede a menos del descanso mínimo del restaurante."
    ),
    dependencies=[manage],
    responses={**CONFLICT_RESPONSES, 422: {"model": ErrorResponse, "description": "Turno fuera del periodo."}},
)
def create_shift(
    schedule_id: ScheduleId,
    data: WorkShiftCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    return shift_service.create_shift(db, user.restaurant_id, schedule_id, data)


@router.get(
    "",
    response_model=list[WorkShiftRead],
    summary="Listar turnos de un cuadrante",
    dependencies=[manage],
    responses=CONFLICT_RESPONSES,
)
def list_shifts(
    schedule_id: ScheduleId,
    employee_id: EmployeeFilter = None,
    date_from: DateFrom = None,
    date_to: DateTo = None,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    return shift_service.list_shifts(
        db, user.restaurant_id, schedule_id,
        employee_id=employee_id, date_from=date_from, date_to=date_to,
    )


@router.delete(
    "/{shift_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar turno de un cuadrante en borrador",
    dependencies=[manage],
    responses=CONFLICT_RESPONSES,
)
def delete_shift(
    schedule_id: ScheduleId,
    shift_id: ShiftId,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    shift_service.delete_shift(db, user.restaurant_id, schedule_id, shift_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
