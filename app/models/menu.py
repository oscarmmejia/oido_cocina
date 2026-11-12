from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    false,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.dishes import Dish
    from app.modules.settings.models.restaurant import Restaurant


class MenuCollection(TimestampMixin, Base):
    """Group of menus with a type and an optional validity period.

    Validity is inclusive on both ends and may overlap: the database only
    rejects a range whose end is before its start.
    """

    __tablename__ = "menu_collections"
    __table_args__ = (
        UniqueConstraint("restaurant_id", "name"),
        CheckConstraint("type IN ('daily', 'seasonal', 'fixed')", name="type"),
        CheckConstraint(
            "valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from",
            name="valid_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(
        ForeignKey("restaurants.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())

    restaurant: Mapped["Restaurant"] = relationship(back_populates="menu_collections")
    menus: Mapped[list["Menu"]] = relationship(back_populates="collection")


class Menu(TimestampMixin, Base):
    """A concrete menu inside a collection, with its own explicit price."""

    __tablename__ = "menus"
    __table_args__ = (
        UniqueConstraint("collection_id", "name"),
        CheckConstraint("own_price >= 0", name="own_price_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    collection_id: Mapped[int] = mapped_column(
        ForeignKey("menu_collections.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    own_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())
    inactive_reason: Mapped[str | None] = mapped_column(String(255))

    collection: Mapped["MenuCollection"] = relationship(back_populates="menus")
    dish_links: Mapped[list["MenuDish"]] = relationship(back_populates="menu")


class MenuDish(Base):
    """Composition of a menu: which dishes it includes and with what role.

    `is_required` marks whether the dish is mandatory inside the menu.
    `includes_drink` is the independent "menu includes a drink" indicator;
    the drink itself is a dish with `role='drink'`.
    """

    __tablename__ = "menu_dishes"
    __table_args__ = (
        CheckConstraint(
            "role IN ('starter', 'main', 'dessert', 'drink', 'other')",
            name="role",
        ),
    )

    menu_id: Mapped[int] = mapped_column(
        ForeignKey("menus.id", ondelete="CASCADE"), primary_key=True
    )
    dish_id: Mapped[int] = mapped_column(
        ForeignKey("dishes.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    is_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=true()
    )
    includes_drink: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=false()
    )

    menu: Mapped["Menu"] = relationship(back_populates="dish_links")
    dish: Mapped["Dish"] = relationship(back_populates="menu_links")
