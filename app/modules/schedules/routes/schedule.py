from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response, status
from sqlalchemy.orm import Session

from app.core.database_connection import get_db
from app.core.kernel.errors import ErrorResponse
from app.core.kernel.identity import CurrentUser
from app.core.kernel.permissions import require_permission
from app.modules.schedules.schemas.schedule import (
    ScheduleCreate,
    ScheduleResponse,
    ScheduleUpdate,
)
from app.modules.schedules.services import schedule as schedule_service

router = APIRouter(prefix="/schedules", tags=["Schedules"])

ScheduleId = Annotated[int, Path(gt=0, description="ID del cuadrante.", examples=[1])]
NOT_FOUND = {404: {"model": ErrorResponse, "description": "Cuadrante no encontrado."}}
NOT_EDITABLE = {
    409: {
        "model": ErrorResponse,
        "description": "El cuadrante está publicado y no se puede modificar ni borrar.",
    }
}


@router.post(
    "/",
    response_model=ScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear cuadrante en borrador",
)
def create_schedule(
    data: ScheduleCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("schedule:manage")),
):
    return schedule_service.create_schedule(db, user.restaurant_id, data)


@router.get(
    "",
    response_model=list[ScheduleResponse],
    summary="Listar cuadrantes del restaurante",
)
def list_schedules(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("schedule:manage")),
):
    return schedule_service.list_schedules(db, user.restaurant_id)


@router.get(
    "/{schedule_id}",
    response_model=ScheduleResponse,
    summary="Obtener cuadrante",
    responses=NOT_FOUND,
)
def get_schedule(
    schedule_id: ScheduleId,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("schedule:manage")),
):
    return schedule_service.get_schedule(db, user.restaurant_id, schedule_id)


@router.patch(
    "/{schedule_id}",
    response_model=ScheduleResponse,
    summary="Editar cuadrante en borrador",
    responses={**NOT_FOUND, **NOT_EDITABLE},
)
def update_schedule(
    schedule_id: ScheduleId,
    data: ScheduleUpdate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("schedule:manage")),
):
    return schedule_service.update_schedule(db, user.restaurant_id, schedule_id, data)


@router.delete(
    "/{schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar cuadrante en borrador",
    responses={**NOT_FOUND, **NOT_EDITABLE},
)
def delete_schedule(
    schedule_id: ScheduleId,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("schedule:manage")),
):
    schedule_service.delete_schedule(db, user.restaurant_id, schedule_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/{schedule_id}/publish",
    response_model=ScheduleResponse,
    summary="Publicar cuadrante (lo deja inmutable)",
    responses={
        **NOT_FOUND,
        409: {
            "model": ErrorResponse,
            "description": "El cuadrante ya estaba publicado.",
        },
    },
)
def publish_schedule(
    schedule_id: ScheduleId,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("schedule:manage")),
):
    return schedule_service.publish_schedule(db, user.restaurant_id, schedule_id)
