from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database_connection import get_db
from app.schemas.schedule_schema import (
    ScheduleCreate,
    ScheduleResponse,
    ScheduleUpdate,
    ShiftCreate,
    ShiftRead,
    ShiftUpdate,
)
from app.controllers.schedule_controller import ScheduleController


router = APIRouter(prefix="/schedules", tags=["Schedules"])

class MockUser:
    def __init__(self, id: int = 1):
        self.id = id

def get_current_user() -> MockUser:
    return MockUser(id=1)


@router.post("/", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED,
            summary="Crear cuadrante por periodo",
            description="Crea un nuevo cuadrante (schedule) para un periodo, con fechas de inicio y fin, en estado borrador.")

def create_schedule(
    schedule_in: ScheduleCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):

    return ScheduleController.create_schedule(db=db, schedule_in=schedule_in, responsible_id=current_user.id)

@router.patch("/{schedule_id}/publish", response_model=ScheduleResponse,
             summary="Publicar cuadrante",
             description="Publica un cuadrante existente, registrando el responsable y la fecha de publicacion.")

def publish_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    return ScheduleController.publish_schedule(db=db, schedule_id=schedule_id, current_user_id=current_user.id)

@router.get("/{schedule_id}", response_model=ScheduleResponse,
           summary="Obtener cuadrante",
           description="Consulta los detalles de un cuadrante por su identificador.")
def get_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return ScheduleController.get_schedule(db=db, schedule_id=schedule_id)
@router.post("/{schedule_id}/shifts", response_model=ShiftRead, status_code=status.HTTP_201_CREATED)
def create_shift(schedule_id: int, shift_in: ShiftCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return ScheduleController.create_shift(db=db, shift_in=shift_in)


@router.patch("/{schedule_id}/shifts/{shift_id}", response_model=ShiftRead)
def update_shift(schedule_id: int, shift_id: int, shift_in: ShiftUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return ScheduleController.update_shift(db=db, schedule_id=schedule_id, shift_id=shift_id, shift_in=shift_in)


@router.delete("/{schedule_id}/shifts/{shift_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shift(schedule_id: int, shift_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    ScheduleController.delete_shift(db=db, schedule_id=schedule_id, shift_id=shift_id)
    return None


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(schedule_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    ScheduleController.delete_schedule(db=db, schedule_id=schedule_id)
    return None


@router.patch("/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(schedule_id: int, schedule_in: ScheduleUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return ScheduleController.update_schedule(db=db, schedule_id=schedule_id, schedule_in=schedule_in)