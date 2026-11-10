from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database_connection import Base
from app.models.enums import (
    ReservationStatus,
    ReservationTableStatus,
    enum_check,
)
from app.models.mixins import TimestampMixin


class Reservation(TimestampMixin, Base):
    """Cabecera de una reserva."""

    __tablename__ = "reservations"
    __table_args__ = (
        CheckConstraint(
            "party_size >= 1",
            name="ck_reservations_party_size",
        ),
        CheckConstraint(
            "end_at > start_at",
            name="ck_reservations_time_range",
        ),
        CheckConstraint(
            enum_check("status", ReservationStatus),
            name="ck_reservations_status",
        ),
        Index(
            "ix_reservations_restaurant_start",
            "restaurant_id",
            "start_at",
        ),
        Index(
            "ix_reservations_restaurant_phone_start",
            "restaurant_id",
            "phone",
            "start_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(
        ForeignKey("restaurant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    combination_id: Mapped[int | None] = mapped_column(
        ForeignKey("table_combinations.id", ondelete="SET NULL"),
        nullable=True,
    )
    customer_name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    party_size: Mapped[int] = mapped_column(Integer, nullable=False)
    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    end_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ReservationStatus.PENDING.value,
        server_default=ReservationStatus.PENDING.value,
    )
    notes: Mapped[str | None] = mapped_column(Text)


class ReservationTable(Base):
    """Ocupación de una mesa por una reserva."""

    __tablename__ = "reservation_tables"
    __table_args__ = (
        UniqueConstraint(
            "reservation_id",
            "table_id",
            name="uq_reservation_tables_reservation_table",
        ),
        CheckConstraint(
            "end_at > start_at",
            name="ck_reservation_tables_time_range",
        ),
        CheckConstraint(
            enum_check("status", ReservationTableStatus),
            name="ck_reservation_tables_status",
        ),
        Index(
            "ix_reservation_tables_reservation_id",
            "reservation_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    reservation_id: Mapped[int] = mapped_column(
        ForeignKey("reservations.id", ondelete="CASCADE"),
        nullable=False,
    )
    table_id: Mapped[int] = mapped_column(
        ForeignKey("tables.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    end_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ReservationTableStatus.ACTIVE.value,
        server_default=ReservationTableStatus.ACTIVE.value,
    )


class ReservationStatusHistory(Base):
    """Historial funcional de cambios de estado de una reserva."""

    __tablename__ = "reservation_status_history"
    __table_args__ = (
        Index(
            "ix_reservation_status_history_reservation",
            "reservation_id",
            "changed_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    reservation_id: Mapped[int] = mapped_column(
        ForeignKey("reservations.id", ondelete="CASCADE"),
        nullable=False,
    )
    previous_status: Mapped[str | None] = mapped_column(String(20))
    new_status: Mapped[str] = mapped_column(String(20), nullable=False)
    changed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reason: Mapped[str | None] = mapped_column(String(255))
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
