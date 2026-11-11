from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.controllers.employee_controller import get_employee
from app.core.kernel.errors import AppError
from app.models.enums import ScheduleStatus
from app.modules.schedules.models.schedule import Schedule
from app.modules.schedules.schemas.schedule import ScheduleCreate, ScheduleUpdate


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
    get_employee(db, restaurant_id, data.responsible_id)
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


def list_schedules(db: Session, restaurant_id: int) -> list[Schedule]:
    return list(
        db.scalars(
            select(Schedule)
            .where(Schedule.restaurant_id == restaurant_id)
            .order_by(Schedule.period_start.desc(), Schedule.id.desc())
        )
    )


def update_schedule(
    db: Session,
    restaurant_id: int,
    schedule_id: int,
    data: ScheduleUpdate,
) -> Schedule:
    schedule = get_schedule(db, restaurant_id, schedule_id)
    if schedule.status != ScheduleStatus.DRAFT.value:
        raise AppError(
            "SCHEDULE_NOT_EDITABLE", "Un cuadrante publicado no se puede modificar.", 409
        )

    changes = data.model_dump(exclude_unset=True)
    period_start = changes.get("period_start", schedule.period_start)
    period_end = changes.get("period_end", schedule.period_end)
    if period_start > period_end:
        raise AppError(
            "SCHEDULE_INVALID_PERIOD",
            "La fecha de inicio del periodo no puede ser posterior a la fecha de fin.",
            422,
        )

    if "responsible_id" in changes:
        get_employee(db, restaurant_id, changes["responsible_id"])

    for field, value in changes.items():
        setattr(schedule, field, value)
    db.commit()
    db.refresh(schedule)
    return schedule


def delete_schedule(db: Session, restaurant_id: int, schedule_id: int) -> None:
    schedule = get_schedule(db, restaurant_id, schedule_id)
    if schedule.status != ScheduleStatus.DRAFT.value:
        raise AppError(
            "SCHEDULE_NOT_EDITABLE", "Un cuadrante publicado no se puede borrar.", 409
        )
    db.delete(schedule)
    db.commit()


def publish_schedule(db: Session, restaurant_id: int, schedule_id: int) -> Schedule:
    schedule = get_schedule(db, restaurant_id, schedule_id)
    if schedule.status == ScheduleStatus.PUBLISHED.value:
        raise AppError(
            "SCHEDULE_ALREADY_PUBLISHED", "El cuadrante ya se encuentra publicado.", 409
        )
    schedule.status = ScheduleStatus.PUBLISHED.value
    schedule.published_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(schedule)
    return schedule
