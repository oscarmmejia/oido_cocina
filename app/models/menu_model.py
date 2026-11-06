from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database_connection import Base
from app.models.enums import MenuCollectionType, MenuDishRole, enum_check
from app.models.mixins import TimestampMixin


class MenuCollection(TimestampMixin, Base):
    """Agrupación de menús con tipo y vigencia."""

    __tablename__ = "menu_collections"
    __table_args__ = (
        UniqueConstraint(
            "restaurant_id",
            "name",
            name="uq_menu_collections_restaurant_name",
        ),
        CheckConstraint(
            enum_check("type", MenuCollectionType),
            name="ck_menu_collections_type",
        ),
        CheckConstraint(
            "valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from",
            name="ck_menu_collections_valid_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(
        ForeignKey("restaurant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )


class Menu(TimestampMixin, Base):
    """Menú concreto dentro de una colección."""

    __tablename__ = "menus"
    __table_args__ = (
        UniqueConstraint(
            "collection_id",
            "name",
            name="uq_menus_collection_name",
        ),
        CheckConstraint(
            "own_price >= 0",
            name="ck_menus_own_price_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    collection_id: Mapped[int] = mapped_column(
        ForeignKey("menu_collections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    own_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
    is_available: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
    inactive_reason: Mapped[str | None] = mapped_column(String(255))


class MenuDish(Base):
    """Composición de un menú."""

    __tablename__ = "menu_dishes"
    __table_args__ = (
        CheckConstraint(
            enum_check("role", MenuDishRole),
            name="ck_menu_dishes_role",
        ),
    )

    menu_id: Mapped[int] = mapped_column(
        ForeignKey("menus.id", ondelete="CASCADE"),
        primary_key=True,
    )
    dish_id: Mapped[int] = mapped_column(
        ForeignKey("dishes.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    is_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
    includes_drink: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
