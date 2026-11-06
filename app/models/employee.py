from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database_connection import Base


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurant.id"), index=True)
    # TODO(HU-AUT-06): añadir ForeignKey("users.id") cuando exista la tabla users
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    full_name: Mapped[str] = mapped_column(String(120))
    job_position: Mapped[str] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")