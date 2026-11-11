from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database_connection import Base
from app.models.enums import PriceEntityType, enum_check


class AuditLog(Base):
    """Rastro de acciones relevantes. Nunca guarda secretos."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index(
            "ix_audit_logs_restaurant_created",
            "restaurant_id",
            "created_at",
        ),
        Index(
            "ix_audit_logs_entity",
            "entity_name",
            "entity_id",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    restaurant_id: Mapped[int | None] = mapped_column(
        ForeignKey("restaurant.id", ondelete="CASCADE"),
        nullable=True,
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_name: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(64))
    old_values: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    new_values: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    result: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="success",
        server_default="success",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class PriceHistory(Base):
    """Historial dedicado de precios de platos y menús."""

    __tablename__ = "price_history"
    __table_args__ = (
        CheckConstraint(
            enum_check("entity_type", PriceEntityType),
            name="ck_price_history_entity_type",
        ),
        CheckConstraint(
            "old_price >= 0",
            name="ck_price_history_old_price_non_negative",
        ),
        CheckConstraint(
            "new_price >= 0",
            name="ck_price_history_new_price_non_negative",
        ),
        Index(
            "ix_price_history_entity_created",
            "entity_type",
            "entity_id",
            "created_at",
        ),
        Index(
            "ix_price_history_restaurant_created",
            "restaurant_id",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(
        ForeignKey("restaurant.id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_type: Mapped[str] = mapped_column(String(10), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    old_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    new_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    changed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
