from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.controllers.employee_controller import get_employee
from app.core.kernel.errors import AppError
from app.models.enums import ScheduleStatus, ShiftStatus
from app.models.restaurant_model import Restaurant
from app.modules.schedules.models.schedule import Schedule
from app.modules.schedules.models.work_shift import WorkShift
from app.modules.schedules.schemas.work_shift import WorkShiftCreate, WorkShiftUpdate
from app.modules.schedules.services.schedule import get_schedule


def _get_restaurant(db: Session, restaurant_id: int) -> Restaurant:
    restaurant = db.get(Restaurant, restaurant_id)
    if restaurant is None:
        raise AppError("RESTAURANT_NOT_FOUND", "Restaurante no encontrado.", 404)
    return restaurant


def _local_zone(restaurant: Restaurant) -> ZoneInfo:
    return ZoneInfo(restaurant.time_zone)


def _get_editable_schedule(db: Session, restaurant_id: int, schedule_id: int) -> Schedule:
    schedule = get_schedule(db, restaurant_id, schedule_id)
    if schedule.status != ScheduleStatus.DRAFT.value:
        raise AppError(
            "SCHEDULE_NOT_EDITABLE", "Un cuadrante publicado no se puede modificar.", 409
        )
    return schedule


def _ensure_within_period(restaurant: Restaurant, schedule: Schedule, starts_at: datetime) -> None:
    local_day = starts_at.astimezone(_local_zone(restaurant)).date()
    if not schedule.period_start <= local_day <= schedule.period_end:
        raise AppError(
            "SHIFT_OUTSIDE_PERIOD",
            "El turno empieza fuera del periodo del cuadrante.",
            422,
        )


def _get_shift(db: Session, schedule_id: int, shift_id: int) -> WorkShift:
    shift = db.scalar(
        select(WorkShift).where(
            WorkShift.id == shift_id, WorkShift.schedule_id == schedule_id
        )
    )
    if shift is None:
        raise AppError("SHIFT_NOT_FOUND", "Turno no encontrado.", 404)
    return shift


def _ensure_free_slot(
    db: Session,
    restaurant: Restaurant,
    employee_id: int,
    starts_at: datetime,
    ends_at: datetime,
    exclude_shift_id: int | None = None,
) -> None:
    """Rechaza solapes y descansos más cortos que el mínimo configurado en el restaurante."""
    min_break = restaurant.min_break_between_shifts or 0
    gap = timedelta(minutes=min_break)
    query = (
        select(WorkShift)
        .join(Schedule, WorkShift.schedule_id == Schedule.id)
        .where(
            Schedule.restaurant_id == restaurant.id,
            WorkShift.employee_id == employee_id,
            WorkShift.status != ShiftStatus.CANCELLED.value,
            WorkShift.start_at < ends_at + gap,
            WorkShift.end_at > starts_at - gap,
        )
    )
    if exclude_shift_id is not None:
        query = query.where(WorkShift.id != exclude_shift_id)
    nearby = db.scalars(query).all()

    if any(s.start_at < ends_at and s.end_at > starts_at for s in nearby):
        raise AppError(
            "SHIFT_OVERLAP", "El empleado ya tiene un turno que se solapa con esa franja.", 409
        )
    if nearby:
        raise AppError(
            "SHIFT_BREAK_TOO_SHORT",
            f"Deben pasar al menos {min_break} minutos entre turnos.",
            409,
        )


def create_shift(
    db: Session, restaurant_id: int, schedule_id: int, data: WorkShiftCreate
) -> WorkShift:
    schedule = _get_editable_schedule(db, restaurant_id, schedule_id)
    employee = get_employee(db, restaurant_id, data.employee_id)
    if not employee.is_active:
        raise AppError("EMPLOYEE_INACTIVE", "El empleado está inactivo.", 422)

    restaurant = _get_restaurant(db, restaurant_id)
    _ensure_within_period(restaurant, schedule, data.starts_at)
    _ensure_free_slot(db, restaurant, employee.id, data.starts_at, data.ends_at)

    shift = WorkShift(
        schedule_id=schedule.id,
        employee_id=employee.id,
        start_at=data.starts_at,
        end_at=data.ends_at,
        type=data.type.value,
    )
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift


def update_shift(
    db: Session,
    restaurant_id: int,
    schedule_id: int,
    shift_id: int,
    data: WorkShiftUpdate,
) -> WorkShift:
    schedule = _get_editable_schedule(db, restaurant_id, schedule_id)
    shift = _get_shift(db, schedule.id, shift_id)
    changes = data.model_dump(exclude_unset=True)
    if "type" in changes:
        changes["type"] = changes["type"].value

    employee_id = changes.get("employee_id", shift.employee_id)
    starts_at = changes.get("starts_at", shift.start_at)
    ends_at = changes.get("ends_at", shift.end_at)

    if starts_at.tzinfo is None or ends_at.tzinfo is None:
        raise AppError(
            "SHIFT_INVALID_TIME",
            "Las fechas deben incluir zona horaria, por ejemplo +01:00.",
            422,
        )
    if ends_at <= starts_at:
        raise AppError(
            "SHIFT_INVALID_TIME",
            "El fin del turno debe ser posterior al inicio.",
            422,
        )

    employee = get_employee(db, restaurant_id, employee_id)
    if not employee.is_active:
        raise AppError("EMPLOYEE_INACTIVE", "El empleado está inactivo.", 422)

    restaurant = _get_restaurant(db, restaurant_id)
    _ensure_within_period(restaurant, schedule, starts_at)
    _ensure_free_slot(
        db,
        restaurant,
        employee.id,
        starts_at,
        ends_at,
        exclude_shift_id=shift.id,
    )

    shift.employee_id = employee_id
    shift.start_at = starts_at
    shift.end_at = ends_at
    if "type" in changes:
        shift.type = changes["type"]
    db.commit()
    db.refresh(shift)
    return shift


def list_shifts(
    db: Session,
    restaurant_id: int,
    schedule_id: int,
    employee_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[WorkShift]:
    schedule = get_schedule(db, restaurant_id, schedule_id)
    restaurant = _get_restaurant(db, restaurant_id)
    zone = _local_zone(restaurant)

    query = select(WorkShift).where(WorkShift.schedule_id == schedule.id)
    if employee_id is not None:
        query = query.where(WorkShift.employee_id == employee_id)
    if date_from is not None:
        start_local = datetime.combine(date_from, time.min, tzinfo=zone)
        query = query.where(WorkShift.start_at >= start_local)
    if date_to is not None:
        end_local = datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=zone)
        query = query.where(WorkShift.start_at < end_local)

    return list(db.scalars(query.order_by(WorkShift.start_at)))


def delete_shift(db: Session, restaurant_id: int, schedule_id: int, shift_id: int) -> None:
    schedule = _get_editable_schedule(db, restaurant_id, schedule_id)
    shift = _get_shift(db, schedule.id, shift_id)
    db.delete(shift)
    db.commit()
