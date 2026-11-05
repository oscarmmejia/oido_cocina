from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database_connection import get_db
from app.schemas.schedule_schema import ScheduleCreate, ScheduleResponse
from app.controllers.schedule_controller import ScheduleController

# Definimos el prefijo del módulo aquí
router = APIRouter(prefix="/schedules", tags=["Schedules"])

class MockUser:
    def __init__(self, id: int = 1):
        self.id = id

def get_current_user() -> MockUser:
    return MockUser(id=1)


@router.post("/", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_schedule(
    schedule_in: ScheduleCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Crea un cuadrante por periodo en estado borrador."""
    return ScheduleController.create_schedule(db=db, schedule_in=schedule_in, responsible_id=current_user.id)


@router.patch("/{schedule_id}/publish", response_model=ScheduleResponse)
def publish_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Publica un cuadrante controlado por el permiso correspondiente."""
    return ScheduleController.publish_schedule(db=db, schedule_id=schedule_id, current_user_id=current_user.id)


@router.get("/{schedule_id}", response_model=ScheduleResponse)
def get_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtiene los detalles de un cuadrante."""
    return ScheduleController.get_schedule(db=db, schedule_id=schedule_id)