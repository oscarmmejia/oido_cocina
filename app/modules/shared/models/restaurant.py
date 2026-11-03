from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database_connection import Base

DEMO_RESTAURANT_NAME = "Demo"


# TEMPORAL: duplicado de HU-AUT-03. Eliminar cuando esté en dev.
class Restaurant(Base):
    """Restaurante mínimo para poder resolver la clave foránea de las mesas."""

    __tablename__ = "restaurant"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
