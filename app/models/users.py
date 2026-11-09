from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    func,
    true,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.settings.models.restaurant import Restaurant


class Role(TimestampMixin, Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    # One role can be assigned to many users (users.role_id is the only link).
    users: Mapped[list["User"]] = relationship(back_populates="role")


class Permission(TimestampMixin, Base):
    """Named permission such as 'dish:create'. The backend checks permissions, not roles."""

    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), primary_key=True)
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id"), primary_key=True)


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    # NULL for users that do not belong to a single restaurant (superadmin, customers).
    restaurant_id: Mapped[int | None] = mapped_column(
        ForeignKey("restaurants.id"), nullable=True, index=True
    )
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())

    # A user has exactly one role: a direct FK, never a many-to-many table.
    role: Mapped["Role"] = relationship(back_populates="users")
    # NULL for superadmins and customers, who do not belong to a single restaurant.
    restaurant: Mapped["Restaurant | None"] = relationship(back_populates="users")


class AuditLog(Base):
    """Append-only trail of relevant actions. Never stores passwords, hashes or tokens."""

    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_logs_restaurant_id_created_at", "restaurant_id", "created_at"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    restaurant_id: Mapped[int | None] = mapped_column(ForeignKey("restaurants.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    old_value: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    new_value: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    result: Mapped[str] = mapped_column(String(20), nullable=False, server_default="success")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
