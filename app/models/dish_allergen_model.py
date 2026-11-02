from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database_connection import Base


class DishAllergen(Base):
    __tablename__ = "DishAllergen"

    dish_id: Mapped[int] = mapped_column(
        "dishId",
        ForeignKey("Dish.id"),
        primary_key=True
    )

    allergen_id: Mapped[int] = mapped_column(
        "allergenId",
        ForeignKey("Allergen.id"),
        primary_key=True
    )
