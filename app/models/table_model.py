from datetime import date

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database_connection import Base
from app.models.enums import TableLocation, enum_check
from app.models.mixins import TimestampMixin

LOCATION_INTERIOR = TableLocation.INTERIOR.value
LOCATION_EXTERIOR = TableLocation.EXTERIOR.value
LOCATION_BAR = TableLocation.BAR.value
LOCATIONS = tuple(item.value for item in TableLocation)


class DiningTable(TimestampMixin, Base):
    """Mesa física del restaurante."""

    __tablename__ = "tables"
    __table_args__ = (
        UniqueConstraint(
            "restaurant_id",
            "number",
            name="uq_table_restaurant_number",
        ),
        CheckConstraint(
            "min_capacity >= 1",
            name="ck_table_min_capacity",
        ),
        CheckConstraint(
            "max_capacity >= min_capacity",
            name="ck_table_capacity_range",
        ),
        CheckConstraint(
            enum_check("location", TableLocation),
            name="ck_table_location",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(
        ForeignKey("restaurant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    min_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    max_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    location: Mapped[str] = mapped_column(String(10), nullable=False)
    # El DER nombra las columnas is_enabled / is_capacity_adjustable. Los
    # atributos Python conservan los nombres que ya expone la API.
    is_active: Mapped[bool] = mapped_column(
        "is_enabled",
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
    adjustable_capacity: Mapped[bool] = mapped_column(
        "is_capacity_adjustable",
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )


class TableCombination(TimestampMixin, Base):
    """Combinación guardada de mesas para grupos grandes."""

    __tablename__ = "table_combinations"
    __table_args__ = (
        UniqueConstraint(
            "restaurant_id",
            "name",
            name="uq_table_combinations_restaurant_name",
        ),
        CheckConstraint(
            "capacity >= 1",
            name="ck_table_combinations_capacity",
        ),
        CheckConstraint(
            "valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from",
            name="ck_table_combinations_valid_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(
        ForeignKey("restaurant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )


class TableCombinationTable(Base):
    """Mesa integrante de una combinación."""

    __tablename__ = "table_combination_tables"

    combination_id: Mapped[int] = mapped_column(
        ForeignKey("table_combinations.id", ondelete="CASCADE"),
        primary_key=True,
    )
    table_id: Mapped[int] = mapped_column(
        ForeignKey("tables.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
