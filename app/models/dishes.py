from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint, true
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class Allergen(TimestampMixin, Base):
    """Common catalog of the 14 EU allergens. `code` is the stable natural key."""

    __tablename__ = "allergens"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)


class Category(TimestampMixin, Base):
    """Menu category (starters, desserts...). Each restaurant has its own."""

    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("restaurant_id", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())
