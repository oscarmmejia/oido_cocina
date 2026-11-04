from sqlalchemy import CheckConstraint, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database_connection import Base


class RestaurantSettings(Base):
    __tablename__ = "restaurant_settings"

    # Clave primaria y foránea: garantiza una configuración por restaurante.
    restaurant_id: Mapped[int] = mapped_column(
        ForeignKey("restaurants.id"),
        primary_key=True
    )

    courtesy_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    slot_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    default_reservation_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    restaurant: Mapped["Restaurant"] = relationship(
        "Restaurant",
        back_populates="settings"
    )

    __table_args__ = (
        CheckConstraint("courtesy_minutes >= 0"),
        CheckConstraint("slot_minutes > 0"),
        CheckConstraint("default_reservation_minutes > 0"),
    )