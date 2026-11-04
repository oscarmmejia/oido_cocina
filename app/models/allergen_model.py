from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database_connection import Base


class Allergen(Base):
    __tablename__ = "Allergen"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True
    )