from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.schedule_model import (
    ScheduleModel,
    ScheduleStatus,
    ShiftModel,
    ShiftStatus,
    ShiftType,
)
from app.models.employee import Employee
from app.schemas.schedule_schema import (
    ScheduleCreate,
    ScheduleUpdate,
    ShiftCreate,
    ShiftUpdate,
)
from app.core.kernel.errors import AppError

class ScheduleController:

    @staticmethod
    def create_schedule(db: Session, schedule_in: ScheduleCreate, responsible_id: int) -> ScheduleModel:
        
        db_schedule = ScheduleModel(
            period_start=schedule_in.period_start,
            period_end=schedule_in.period_end,
            status=ScheduleStatus.BORRADOR,
            responsible_id=responsible_id
        )
        db.add(db_schedule)
        db.commit()
        db.refresh(db_schedule)
        return db_schedule

    @staticmethod
    def publish_schedule(db: Session, schedule_id: int, current_user_id: int) -> ScheduleModel:

        schedule = db.query(ScheduleModel).filter(ScheduleModel.id == schedule_id).first()
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NOT_FOUND", "message": "Cuadrante no encontrado"}
            )

        if schedule.status == ScheduleStatus.PUBLICADO:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "BAD_REQUEST", "message": "El cuadrante ya se encuentra publicado"}
            )

        schedule.status = ScheduleStatus.PUBLICADO
        schedule.responsible_id = current_user_id
        schedule.published_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(schedule)
        return schedule

    @staticmethod
    def get_schedule(db: Session, schedule_id: int) -> ScheduleModel:
        schedule = db.query(ScheduleModel).filter(ScheduleModel.id == schedule_id).first()
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NOT_FOUND", "message": "Cuadrante no encontrado"}
            )
        return schedule

    @staticmethod
    def update_schedule(db: Session, schedule_id: int, schedule_in: ScheduleUpdate) -> ScheduleModel:
        schedule = db.query(ScheduleModel).filter(ScheduleModel.id == schedule_id).first()
        if not schedule:
            raise AppError("NOT_FOUND", "Cuadrante no encontrado", 404)
        if schedule.status == ScheduleStatus.PUBLICADO:
            raise AppError("CONFLICT", "No se puede modificar un cuadrante publicado", 409)

        changes = schedule_in.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(schedule, field, value)
        db.commit()
        db.refresh(schedule)
        return schedule

    @staticmethod
    def delete_schedule(db: Session, schedule_id: int) -> None:
        schedule = db.query(ScheduleModel).filter(ScheduleModel.id == schedule_id).first()
        if not schedule:
            raise AppError("NOT_FOUND", "Cuadrante no encontrado", 404)
        if schedule.status == ScheduleStatus.PUBLICADO:
            raise AppError("CONFLICT", "No se puede borrar un cuadrante publicado", 409)

        db.query(ShiftModel).filter(ShiftModel.schedule_id == schedule_id).delete(synchronize_session=False)
        db.delete(schedule)
        db.commit()

    @staticmethod
    def create_shift(db: Session, shift_in: ShiftCreate) -> ShiftModel:
        schedule = db.query(ScheduleModel).filter(ScheduleModel.id == shift_in.schedule_id).first()
        if not schedule:
            raise AppError("NOT_FOUND", "Cuadrante no encontrado", 404)
        if schedule.status == ScheduleStatus.PUBLICADO:
            raise AppError("CONFLICT", "No se pueden crear turnos en un cuadrante publicado", 409)

        employee = db.query(Employee).filter(Employee.id == shift_in.employee_id).first()
        if employee is None or not employee.is_active:
            raise AppError("VALIDATION_ERROR", "El empleado no está activo", 422)

        shift = ShiftModel(
            schedule_id=shift_in.schedule_id,
            employee_id=shift_in.employee_id,
            start_at=shift_in.start_at,
            end_at=shift_in.end_at,
            type=ShiftType,
            status=ShiftStatus.BORRADOR,
        )

        db.add(shift)
        db.commit()
        db.refresh(shift)
        return shift

    @staticmethod
    def update_shift(db: Session, schedule_id: int, shift_id: int, shift_in: ShiftUpdate) -> ShiftModel:
        schedule = db.query(ScheduleModel).filter(ScheduleModel.id == schedule_id).first()
        if not schedule:
            raise AppError("NOT_FOUND", "Cuadrante no encontrado", 404)
        if schedule.status == ScheduleStatus.PUBLICADO:
            raise AppError("CONFLICT", "No se pueden modificar turnos en un cuadrante publicado", 409)

        shift = db.query(ShiftModel).filter(ShiftModel.id == shift_id, ShiftModel.schedule_id == schedule_id).first()
        if not shift:
            raise AppError("NOT_FOUND", "Turno no encontrado", 404)

        changes = shift_in.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(shift, field, value)
        db.commit()
        db.refresh(shift)
        return shift

    @staticmethod
    def delete_shift(db: Session, schedule_id: int, shift_id: int) -> None:
        schedule = db.query(ScheduleModel).filter(ScheduleModel.id == schedule_id).first()
        if not schedule:
            raise AppError("NOT_FOUND", "Cuadrante no encontrado", 404)
        if schedule.status == ScheduleStatus.PUBLICADO:
            raise AppError("CONFLICT", "No se pueden borrar turnos en un cuadrante publicado", 409)

        shift = db.query(ShiftModel).filter(ShiftModel.id == shift_id, ShiftModel.schedule_id == schedule_id).first()
        if not shift:
            raise AppError("NOT_FOUND", "Turno no encontrado", 404)
        db.delete(shift)
        db.commit()