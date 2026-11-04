from sqlalchemy import Boolean, CheckConstraint, ForeignKey, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database_connection import Base

LOCATION_INTERIOR = "interior"
LOCATION_EXTERIOR = "exterior"
LOCATIONS = (LOCATION_INTERIOR, LOCATION_EXTERIOR)


class DiningTable(Base):
    """Mesa física del restaurante.

    No se llama ``Table`` a propósito: choca con ``sqlalchemy.Table``.
    """

    __tablename__ = "tables"
    __table_args__ = (
        UniqueConstraint("restaurant_id", "number", name="uq_table_restaurant_number"),
        CheckConstraint("min_capacity >= 1", name="ck_table_min_capacity"),
        CheckConstraint("max_capacity >= min_capacity", name="ck_table_capacity_range"),
        CheckConstraint("location IN ('interior','exterior')", name="ck_table_location"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(
        ForeignKey("restaurant.id", ondelete="CASCADE"), index=True, nullable=False
    )
    number: Mapped[int] = mapped_column(nullable=False)
    min_capacity: Mapped[int] = mapped_column(nullable=False)
    max_capacity: Mapped[int] = mapped_column(nullable=False)
    location: Mapped[str] = mapped_column(String(10), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    adjustable_capacity: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
