from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from app.core.database_connection import get_db
from app.core.kernel.errors import ErrorResponse
from app.core.kernel.identity import CurrentUser, get_current_user
from app.core.kernel.permissions import require_permission
from app.modules.schedules.schemas.schedule import ScheduleCreate, ScheduleResponse
from app.modules.schedules.services import schedule as schedule_service

router = APIRouter(prefix="/schedules", tags=["Schedules"])

manage = Depends(require_permission("schedule:manage"))
ScheduleId = Annotated[int, Path(gt=0, description="ID del cuadrante.", examples=[1])]
NOT_FOUND = {404: {"model": ErrorResponse, "description": "Cuadrante no encontrado."}}


@router.post(
    "/",
    response_model=ScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear cuadrante en borrador",
    dependencies=[manage],
)
def create_schedule(
    data: ScheduleCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    return schedule_service.create_schedule(db, user.restaurant_id, data)


@router.get(
    "/{schedule_id}",
    response_model=ScheduleResponse,
    summary="Obtener cuadrante",
    dependencies=[manage],
    responses=NOT_FOUND,
)
def get_schedule(
    schedule_id: ScheduleId,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    return schedule_service.get_schedule(db, user.restaurant_id, schedule_id)


@router.patch(
    "/{schedule_id}/publish",
    response_model=ScheduleResponse,
    summary="Publicar cuadrante (lo deja inmutable)",
    dependencies=[manage],
    responses={**NOT_FOUND, 400: {"model": ErrorResponse, "description": "Ya estaba publicado."}},
)
def publish_schedule(
    schedule_id: ScheduleId,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    return schedule_service.publish_schedule(db, user.restaurant_id, schedule_id)
