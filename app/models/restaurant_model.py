from datetime import time

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Integer,
    SmallInteger,
    String,
    Time,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database_connection import Base
from app.models.mixins import TimestampMixin


class Restaurant(TimestampMixin, Base):
    """Restaurante, configuración de reservas y horario de apertura.

    La configuración se fusionó en esta tabla: no existe ``restaurant_settings``.
    El horario también vive aquí; no existe una tabla ``opening_hours``.
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
        CheckConstraint(
            "day_of_week IS NULL OR day_of_week BETWEEN 1 AND 7",
            name="ck_restaurant_day_of_week",
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
    day_of_week: Mapped[int | None] = mapped_column(SmallInteger)
    period: Mapped[str | None] = mapped_column(String(16))
    open_time: Mapped[time | None] = mapped_column(Time)
    close_time: Mapped[time | None] = mapped_column(Time)
    kitchen_close_time: Mapped[time | None] = mapped_column(Time)
    direction: Mapped[str | None] = mapped_column(String(255))
