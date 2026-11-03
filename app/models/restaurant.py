from datetime import time

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Time,
    UniqueConstraint,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class Restaurant(TimestampMixin, Base):
    """Root of the multi-restaurant model: every business entity hangs from here."""

    __tablename__ = "restaurants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())


class RestaurantSettings(TimestampMixin, Base):
    """Per-restaurant configuration. One row per restaurant, nothing hardcoded in code."""

    __tablename__ = "restaurant_settings"
    __table_args__ = (
        CheckConstraint("courtesy_minutes >= 0", name="courtesy_minutes_non_negative"),
        CheckConstraint("slot_minutes > 0", name="slot_minutes_positive"),
        CheckConstraint(
            "min_break_between_shifts IS NULL OR min_break_between_shifts >= 0",
            name="min_break_non_negative",
        ),
    )

    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), primary_key=True)
    courtesy_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="5")
    slot_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="60")
    min_break_between_shifts: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Minutes"
    )


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
