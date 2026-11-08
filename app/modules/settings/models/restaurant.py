from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.settings.models.restaurant_settings import RestaurantSettings


class Restaurant(TimestampMixin, Base):
    """Root of the multi-restaurant model: every business entity hangs from here."""

    __tablename__ = "restaurants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())

    settings: Mapped["RestaurantSettings | None"] = relationship(
        back_populates="restaurant", uselist=False
    )
