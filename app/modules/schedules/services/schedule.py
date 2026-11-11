from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.controllers.employee_controller import get_employee
from app.core.kernel.errors import AppError
from app.models.enums import ScheduleStatus
from app.modules.schedules.models.schedule import Schedule
from app.modules.schedules.schemas.schedule import ScheduleCreate


def get_schedule(db: Session, restaurant_id: int, schedule_id: int) -> Schedule:
    schedule = db.scalar(
        select(Schedule).where(
            Schedule.id == schedule_id, Schedule.restaurant_id == restaurant_id
        )
    )
    if schedule is None:
        raise AppError("SCHEDULE_NOT_FOUND", "Cuadrante no encontrado.", 404)
    return schedule


def create_schedule(db: Session, restaurant_id: int, data: ScheduleCreate) -> Schedule:
    get_employee(db, restaurant_id, data.responsible_id)  # valida pertenencia al restaurante
    schedule = Schedule(
        restaurant_id=restaurant_id,
        period_start=data.period_start,
        period_end=data.period_end,
        responsible_id=data.responsible_id,
        status=ScheduleStatus.DRAFT.value,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


def publish_schedule(db: Session, restaurant_id: int, schedule_id: int) -> Schedule:
    schedule = get_schedule(db, restaurant_id, schedule_id)
    if schedule.status == ScheduleStatus.PUBLISHED.value:
        raise AppError(
            "SCHEDULE_ALREADY_PUBLISHED", "El cuadrante ya se encuentra publicado.", 400
        )
    schedule.status = ScheduleStatus.PUBLISHED.value
    schedule.published_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(schedule)
    return schedule
