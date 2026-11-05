"""Modelo unificado de restaurante conforme al DER actualizado del equipo."""
from datetime import time
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Integer, String, Time, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Boolean, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.settings.models.restaurant_settings import RestaurantSettings


class Restaurant(Base):
    __tablename__ = "restaurant"
class Restaurant(TimestampMixin, Base):
    """Root of the multi-restaurant model: every business entity hangs from here."""

    __tablename__ = "restaurants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    time_zone: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    # El DER escribe "curtesy_minutes"; el atributo Python se llama correctamente
    # "courtesy_minutes" y se mapea a la columna literal del DER.
    courtesy_minutes: Mapped[int] = mapped_column(
        "curtesy_minutes", Integer, nullable=False, server_default=text("5")
    )
    # Según acuerdo del equipo, no existe default_reservation_minutes separado.
    slot_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("60")
    )

    # Campos descritos en restaurant dentro del DER.
    # DER no determina obligatoriedad/tipos exactos para estos campos:
    # se dejan opcionales hasta definir el contrato de uso.
    min_break_between_shifts: Mapped[int | None] = mapped_column(Integer)
    day_of_week: Mapped[int | None] = mapped_column(Integer)
    period: Mapped[str | None] = mapped_column(String(16))
    open_time: Mapped[time | None] = mapped_column(Time)
    close_time: Mapped[time | None] = mapped_column(Time)
    kitchen_close_time: Mapped[time | None] = mapped_column(Time)
    direction: Mapped[str | None] = mapped_column(String(255))

    __table_args__ = (
        CheckConstraint("curtesy_minutes >= 0", name="ck_restaurant_curtesy_nonnegative"),
        CheckConstraint("slot_minutes > 0", name="ck_restaurant_slot_positive"),
        CheckConstraint(
            "min_break_between_shifts IS NULL OR min_break_between_shifts >= 0",
            name="ck_restaurant_min_break_nonnegative",
        ),
        CheckConstraint(
            "day_of_week IS NULL OR day_of_week BETWEEN 1 AND 7",
            name="ck_restaurant_day_of_week",
        ),
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())

    settings: Mapped["RestaurantSettings | None"] = relationship(
        back_populates="restaurant", uselist=False
    )
