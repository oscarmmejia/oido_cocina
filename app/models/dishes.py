from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    false,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.menu import MenuDish
    from app.modules.settings.models.restaurant import Restaurant


class Allergen(TimestampMixin, Base):
    """Common catalog of the 14 EU allergens. `code` is the stable natural key."""

    __tablename__ = "allergens"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    dishes: Mapped[list["Dish"]] = relationship(
        secondary="dish_allergens", back_populates="allergens"
    )


class Category(TimestampMixin, Base):
    """Menu category (starters, desserts...). Each restaurant has its own."""

    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("restaurant_id", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())

    restaurant: Mapped["Restaurant"] = relationship(back_populates="categories")
    dishes: Mapped[list["Dish"]] = relationship(back_populates="category")


class Dish(TimestampMixin, Base):
    """A dish of the menu, always scoped to one restaurant and one category."""

    __tablename__ = "dishes"
    __table_args__ = (CheckConstraint("price >= 0", name="price_non_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(
        ForeignKey("restaurants.id"), nullable=False, index=True
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())

    restaurant: Mapped["Restaurant"] = relationship(back_populates="dishes")
    category: Mapped["Category"] = relationship(back_populates="dishes")
    allergens: Mapped[list["Allergen"]] = relationship(
        secondary="dish_allergens", back_populates="dishes"
    )
    menu_links: Mapped[list["MenuDish"]] = relationship(back_populates="dish")


class DishAllergen(Base):
    """Allergens declared by a dish. The pair is the primary key (no duplicates)."""

    __tablename__ = "dish_allergens"

    dish_id: Mapped[int] = mapped_column(
        ForeignKey("dishes.id", ondelete="CASCADE"), primary_key=True
    )
    allergen_id: Mapped[int] = mapped_column(
        ForeignKey("allergens.id", ondelete="CASCADE"), primary_key=True
    )
