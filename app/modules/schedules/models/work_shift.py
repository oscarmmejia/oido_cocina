from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database_connection import Base

if TYPE_CHECKING:
    from app.modules.schedules.models.schedule import Schedule


class WorkShift(Base):
    """Bloque continuo de trabajo. Un turno partido son dos filas del mismo día."""

    __tablename__ = "work_shifts"
    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="ck_work_shift_time_order"),
        Index("ix_work_shifts_employee_starts", "employee_id", "starts_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    schedule_id: Mapped[int] = mapped_column(
        ForeignKey("schedules.id", ondelete="CASCADE"), index=True
    )
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    schedule: Mapped["Schedule"] = relationship(back_populates="shifts")
