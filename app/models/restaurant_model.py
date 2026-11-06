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
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database_connection import Base
from app.models.enums import OpeningPeriod, enum_check
from app.models.mixins import TimestampMixin


class Restaurant(TimestampMixin, Base):
    """Restaurante y su configuración de reservas.

    La configuración se fusionó en esta tabla: no existe ``restaurant_settings``.
    """

    __tablename__ = "restaurant"
    __table_args__ = (
        CheckConstraint(
            "curtesy_minutes >= 0",
            name="ck_restaurant_curtesy_nonnegative",
        ),
        CheckConstraint(
            "slot_minutes > 0",
            name="ck_restaurant_slot_positive",
        ),
        CheckConstraint(
            "min_break_between_shifts IS NULL OR min_break_between_shifts >= 0",
            name="ck_restaurant_min_break_nonnegative",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    time_zone: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="Europe/Madrid",
        server_default=text("'Europe/Madrid'"),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
    # El DER escribe "curtesy_minutes"; el atributo Python conserva la
    # ortografía correcta.
    courtesy_minutes: Mapped[int] = mapped_column(
        "curtesy_minutes",
        Integer,
        nullable=False,
        default=5,
        server_default=text("5"),
    )
    slot_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=60,
        server_default=text("60"),
    )
    min_break_between_shifts: Mapped[int | None] = mapped_column(Integer)
    direction: Mapped[str | None] = mapped_column(String(255))


class OpeningHours(TimestampMixin, Base):
    """Franja de apertura de un restaurante para un día y periodo."""

    __tablename__ = "opening_hours"
    __table_args__ = (
        UniqueConstraint(
            "restaurant_id",
            "day_of_week",
            "period",
            name="uq_opening_hours_restaurant_day_period",
        ),
        CheckConstraint(
            "day_of_week BETWEEN 1 AND 7",
            name="ck_opening_hours_day_of_week",
        ),
        CheckConstraint(
            enum_check("period", OpeningPeriod),
            name="ck_opening_hours_period",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(
        ForeignKey("restaurant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    period: Mapped[str] = mapped_column(String(16), nullable=False)
    open_time: Mapped[time] = mapped_column(Time, nullable=False)
    close_time: Mapped[time] = mapped_column(Time, nullable=False)
    kitchen_close_time: Mapped[time | None] = mapped_column(Time)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
