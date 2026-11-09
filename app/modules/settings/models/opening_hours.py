from datetime import time
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, SmallInteger, String, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.settings.models.restaurant import Restaurant


class OpeningHours(TimestampMixin, Base):
    """One opening period (morning/afternoon) of a restaurant for a weekday (1=Monday..7=Sunday)."""

    __tablename__ = "opening_hours"
    __table_args__ = (
        UniqueConstraint("restaurant_id", "day_of_week", "period"),
        CheckConstraint("day_of_week BETWEEN 1 AND 7", name="day_of_week_range"),
        CheckConstraint("period IN ('morning', 'afternoon')", name="period_allowed"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), nullable=False)
    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    period: Mapped[str] = mapped_column(String(16), nullable=False)
    open_time: Mapped[time] = mapped_column(Time, nullable=False)
    close_time: Mapped[time] = mapped_column(Time, nullable=False)
    kitchen_close_time: Mapped[time | None] = mapped_column(Time, nullable=True)

    restaurant: Mapped["Restaurant"] = relationship(back_populates="opening_hours")
