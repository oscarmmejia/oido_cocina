from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database_connection import Base


class DishAllergen(Base):
    """Alérgenos declarados por un plato."""

    __tablename__ = "dish_allergens"

    dish_id: Mapped[int] = mapped_column(
        ForeignKey("dishes.id", ondelete="CASCADE"),
        primary_key=True,
    )
    allergen_id: Mapped[int] = mapped_column(
        ForeignKey("allergens.id", ondelete="CASCADE"),
        primary_key=True,
    )
