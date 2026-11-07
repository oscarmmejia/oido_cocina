from datetime import date, datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database_connection import Base

if TYPE_CHECKING:
    from app.modules.schedules.models.work_shift import WorkShift


class ScheduleStatus(StrEnum):
    BORRADOR = "borrador"
    PUBLICADO = "publicado"


class Schedule(Base):
    __tablename__ = "schedules"
    __table_args__ = (
        CheckConstraint("period_start <= period_end", name="ck_schedule_period_order"),
        CheckConstraint("status IN ('borrador', 'publicado')", name="ck_schedule_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(
        ForeignKey("restaurant.id", ondelete="CASCADE"), index=True
    )
    period_start: Mapped[date] = mapped_column(Date, index=True)
    period_end: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(
        String(20), default=ScheduleStatus.BORRADOR.value, server_default=ScheduleStatus.BORRADOR.value
    )
    responsible_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    shifts: Mapped[list["WorkShift"]] = relationship(
        back_populates="schedule", cascade="all, delete-orphan"
    )
