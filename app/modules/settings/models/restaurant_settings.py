from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.settings.models.restaurant import Restaurant


class RestaurantSettings(TimestampMixin, Base):
    """Per-restaurant configuration. One row per restaurant, nothing hardcoded in code."""

    __tablename__ = "restaurant_settings"
    __table_args__ = (
        CheckConstraint("courtesy_minutes >= 0", name="courtesy_minutes_non_negative"),
        CheckConstraint("slot_minutes > 0", name="slot_minutes_positive"),
        CheckConstraint("default_reservation_minutes > 0", name="default_reservation_minutes_positive"),
        CheckConstraint(
            "min_break_between_shifts IS NULL OR min_break_between_shifts >= 0",
            name="min_break_non_negative",
        ),
    )

    # Primary and foreign key at once: guarantees a single settings row per restaurant.
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), primary_key=True)
    courtesy_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="5")
    slot_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="60")
    default_reservation_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="60"
    )
    min_break_between_shifts: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Minutes"
    )

    restaurant: Mapped["Restaurant"] = relationship(back_populates="settings")
