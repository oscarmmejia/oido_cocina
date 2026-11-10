
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database_connection import Base


class Dish(Base):
    __tablename__ = "Dish"

    __table_args__ = (
        CheckConstraint(
            "price >= 0",
            name="ck_dish_price_non_negative"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    restaurant_id: Mapped[int] = mapped_column(
        "restaurantId",
        nullable=False
    )

    category_id: Mapped[int] = mapped_column(
        "categoryId",
        ForeignKey("Category.id"),
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        nullable=True
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        "isActive",
        default=True,
        nullable=False
    )

    is_published: Mapped[bool] = mapped_column(
        "isPublished",
        default=False,
        nullable=False
    )

    is_available: Mapped[bool] = mapped_column(
        "isAvailable",
        default=True,
        nullable=False
    )
