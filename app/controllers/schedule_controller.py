from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.schedule_model import ScheduleModel, ScheduleStatus
from app.schemas.schedule_schema import ScheduleCreate


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