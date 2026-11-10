from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database_connection import Base
from app.models.enums import (
    JobPosition,
    RequestStatus,
    ScheduleStatus,
    ShiftStatus,
    ShiftType,
    TimeOffType,
    enum_check,
)
from app.models.mixins import TimestampMixin


class Employee(TimestampMixin, Base):
    """Empleado del restaurante, con usuario opcional."""

    __tablename__ = "employees"
    __table_args__ = (
        UniqueConstraint(
            "restaurant_id",
            "user_id",
            name="uq_employees_restaurant_user",
        ),
        CheckConstraint(
            enum_check("job_position", JobPosition),
            name="ck_employees_job_position",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(
        ForeignKey("restaurant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    job_position: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )


class Schedule(TimestampMixin, Base):
    """Cuadrante de un periodo."""

    __tablename__ = "schedules"
    __table_args__ = (
        UniqueConstraint(
            "restaurant_id",
            "period_start",
            "period_end",
            name="uq_schedules_restaurant_period",
        ),
        CheckConstraint(
            "period_end >= period_start",
            name="ck_schedules_period_range",
        ),
        CheckConstraint(
            enum_check("status", ScheduleStatus),
            name="ck_schedules_status",
        ),
        Index(
            "ix_schedules_restaurant_period",
            "restaurant_id",
            "period_start",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(
        ForeignKey("restaurant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ScheduleStatus.DRAFT.value,
        server_default=ScheduleStatus.DRAFT.value,
    )
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    published_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class WorkShift(TimestampMixin, Base):
    """Turno individual de un empleado dentro de un cuadrante."""

    __tablename__ = "work_shifts"
    __table_args__ = (
        CheckConstraint(
            "end_at > start_at",
            name="ck_work_shifts_time_range",
        ),
        CheckConstraint(
            enum_check("type", ShiftType),
            name="ck_work_shifts_type",
        ),
        CheckConstraint(
            enum_check("status", ShiftStatus),
            name="ck_work_shifts_status",
        ),
        Index(
            "ix_work_shifts_schedule_id",
            "schedule_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    schedule_id: Mapped[int] = mapped_column(
        ForeignKey("schedules.id", ondelete="CASCADE"),
        nullable=False,
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    end_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ShiftType.MORNING.value,
        server_default=text("'morning'"),
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ShiftStatus.SCHEDULED.value,
        server_default=ShiftStatus.SCHEDULED.value,
    )


class TimeOffRequest(TimestampMixin, Base):
    """Solicitud de ausencia de un empleado."""

    __tablename__ = "time_off_requests"
    __table_args__ = (
        CheckConstraint(
            "end_at > start_at",
            name="ck_time_off_requests_time_range",
        ),
        CheckConstraint(
            enum_check("type", TimeOffType),
            name="ck_time_off_requests_type",
        ),
        CheckConstraint(
            enum_check("status", RequestStatus),
            name="ck_time_off_requests_status",
        ),
        Index(
            "ix_time_off_requests_employee_status",
            "employee_id",
            "status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    end_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=RequestStatus.PENDING.value,
        server_default=RequestStatus.PENDING.value,
    )
    reason: Mapped[str | None] = mapped_column(String(255))
    resolved_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ShiftSwapRequest(TimestampMixin, Base):
    """Solicitud de intercambio de turnos entre empleados."""

    __tablename__ = "shift_swap_requests"
    __table_args__ = (
        CheckConstraint(
            "target_shift_id IS NULL OR target_shift_id <> origin_shift_id",
            name="ck_shift_swap_requests_distinct_shifts",
        ),
        CheckConstraint(
            enum_check("status", RequestStatus),
            name="ck_shift_swap_requests_status",
        ),
        Index(
            "ix_shift_swap_requests_status",
            "status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    origin_shift_id: Mapped[int] = mapped_column(
        ForeignKey("work_shifts.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_shift_id: Mapped[int | None] = mapped_column(
        ForeignKey("work_shifts.id", ondelete="SET NULL"),
        nullable=True,
    )
    requested_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolved_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=RequestStatus.PENDING.value,
        server_default=RequestStatus.PENDING.value,
    )
    reason: Mapped[str | None] = mapped_column(String(255))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
