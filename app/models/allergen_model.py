from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database_connection import Base
from app.models.mixins import TimestampMixin


class Allergen(TimestampMixin, Base):
    """Catálogo común de los catorce alérgenos de la Unión Europea."""

    __tablename__ = "allergens"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )
