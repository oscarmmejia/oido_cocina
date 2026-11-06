from sqlalchemy import String, Integer, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database_connection import Base


class Category(Base):
    __tablename__ = "Category"

    __table_args__ = (
        UniqueConstraint(
            "restaurantId",
            "name",
            name="uq_category_restaurant_name"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    restaurant_id: Mapped[int] = mapped_column(
        "restaurantId",
        Integer,
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    sort_order: Mapped[int] = mapped_column(
        "sortOrder",
        Integer,
        nullable=False,
        default=0
    )

    is_active: Mapped[bool] = mapped_column(
        "isActive",
        Boolean,
        nullable=False,
        default=True
    )
