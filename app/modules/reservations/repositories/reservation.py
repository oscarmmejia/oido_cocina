"""Acceso a datos del agregado de reserva.

Este módulo no contiene reglas de negocio ni confirma transacciones: prepara
consultas y deja que el servicio decida cuándo hacer ``commit`` o ``rollback``.

Los modelos viven en ``app.models`` (esquema compartido de HU-AUT-02). No se
añaden relaciones ORM aquí para no modificar los modelos compartidos; las
ocupaciones y el historial se consultan de forma explícita.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import delete, exists, func, or_, select, update
from sqlalchemy.orm import Session

from app.models import (
    DiningTable,
    Reservation,
    ReservationStatusHistory,
    ReservationTable,
    TableCombination,
    TableCombinationTable,
)
from app.models.enums import ReservationTableStatus


@dataclass
class ReservationDetail:
    """Reserva con sus ocupaciones e historial ya cargados."""

    reservation: Reservation
    tables: list[ReservationTable]
    history: list[ReservationStatusHistory]


def add_reservation(db: Session, reservation: Reservation) -> Reservation:
    """Añade una reserva y asigna su clave primaria sin confirmar."""

    db.add(reservation)
    db.flush()
    db.refresh(reservation)
    return reservation


def add_occupation(db: Session, occupation: ReservationTable) -> ReservationTable:
    """Añade una ocupación de mesa y asigna su clave primaria."""

    db.add(occupation)
    db.flush()
    db.refresh(occupation)
    return occupation


def add_history(
    db: Session, history: ReservationStatusHistory
) -> ReservationStatusHistory:
    """Añade una entrada de historial y asigna su clave primaria."""

    db.add(history)
    db.flush()
    db.refresh(history)
    return history


def get_reservation(
    db: Session,
    reservation_id: int,
    restaurant_id: int,
    *,
    for_update: bool = False,
) -> Reservation | None:
    """Devuelve una reserva visible para el restaurante indicado."""

    statement = select(Reservation).where(
        Reservation.id == reservation_id,
        Reservation.restaurant_id == restaurant_id,
    )
    if for_update:
        statement = statement.with_for_update()

    return db.scalar(statement)


def get_reservation_detail(
    db: Session,
    reservation_id: int,
    restaurant_id: int,
    *,
    for_update: bool = False,
) -> ReservationDetail | None:
    """Devuelve la reserva junto a sus ocupaciones e historial."""

    reservation = get_reservation(
        db,
        reservation_id,
        restaurant_id,
        for_update=for_update,
    )
    if reservation is None:
        return None

    return ReservationDetail(
        reservation=reservation,
        tables=list_occupations(db, reservation.id),
        history=list_history(db, reservation.id),
    )


def get_combination(
    db: Session,
    combination_id: int,
    restaurant_id: int,
) -> TableCombination | None:
    """Devuelve una combinación visible para el restaurante indicado."""

    return db.scalar(
        select(TableCombination).where(
            TableCombination.id == combination_id,
            TableCombination.restaurant_id == restaurant_id,
        )
    )


def get_combination_table_ids(db: Session, combination_id: int) -> list[int]:
    """Devuelve los IDs de las mesas que forman una combinación."""

    return list(
        db.scalars(
            select(TableCombinationTable.table_id)
            .where(TableCombinationTable.combination_id == combination_id)
            .order_by(TableCombinationTable.table_id)
        )
    )


def get_tables_by_ids(db: Session, table_ids: list[int]) -> list[DiningTable]:
    """Devuelve las mesas indicadas en orden estable por ID.

    El orden es determinista para que los bloqueos posteriores con
    ``SELECT ... FOR UPDATE`` sigan siempre el mismo orden.
    """

    if not table_ids:
        return []

    return list(
        db.scalars(
            select(DiningTable)
            .where(DiningTable.id.in_(table_ids))
            .order_by(DiningTable.id)
        )
    )


def list_reservations(
    db: Session,
    *,
    restaurant_id: int,
    status: str | None = None,
    table_id: int | None = None,
    customer: str | None = None,
    customer_email: str | None = None,
    start_from: datetime | None = None,
    start_to: datetime | None = None,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Reservation], int]:
    """Devuelve reservas filtradas y el total de coincidencias."""

    conditions = [Reservation.restaurant_id == restaurant_id]

    if status is not None:
        conditions.append(Reservation.status == status)
    if start_from is not None:
        conditions.append(Reservation.start_at >= start_from)
    if start_to is not None:
        conditions.append(Reservation.start_at < start_to)
    if table_id is not None:
        conditions.append(
            exists().where(
                ReservationTable.reservation_id == Reservation.id,
                ReservationTable.table_id == table_id,
            )
        )
    if customer:
        pattern = f"%{customer}%"
        conditions.append(
            or_(
                Reservation.customer_name.ilike(pattern),
                Reservation.phone.ilike(pattern),
                Reservation.email.ilike(pattern),
            )
        )
    if customer_email is not None:
        conditions.append(func.lower(Reservation.email) == customer_email)

    total = (
        db.scalar(
            select(func.count())
            .select_from(Reservation)
            .where(*conditions)
        )
        or 0
    )
    items = list(
        db.scalars(
            select(Reservation)
            .where(*conditions)
            .order_by(Reservation.start_at, Reservation.id)
            .offset(offset)
            .limit(limit)
        )
    )
    return items, total


def lock_tables(db: Session, table_ids: list[int]) -> list[DiningTable]:
    """Bloquea las mesas indicadas en orden estable por ID."""

    if not table_ids:
        return []

    return list(
        db.scalars(
            select(DiningTable)
            .where(DiningTable.id.in_(table_ids))
            .order_by(DiningTable.id)
            .with_for_update()
        )
    )


def list_table_conflicts(
    db: Session,
    table_ids: list[int],
    start_at: datetime,
    end_at: datetime,
    *,
    exclude_reservation_id: int | None = None,
) -> list[ReservationTable]:
    """Devuelve ocupaciones activas que solapan el intervalo indicado."""

    if not table_ids:
        return []

    statement = select(ReservationTable).where(
        ReservationTable.table_id.in_(table_ids),
        ReservationTable.status == ReservationTableStatus.ACTIVE.value,
        ReservationTable.start_at < end_at,
        ReservationTable.end_at > start_at,
    )
    if exclude_reservation_id is not None:
        statement = statement.where(
            ReservationTable.reservation_id != exclude_reservation_id
        )

    return list(db.scalars(statement.order_by(ReservationTable.id)))


def release_occupations(db: Session, reservation_id: int) -> int:
    """Libera todas las ocupaciones activas de una reserva.

    El esquema compartido no tiene un estado ``released``; se usa
    ``cancelled`` como estado no activo. La restricción de exclusión solo
    considera las ocupaciones ``active``.
    """

    result = db.execute(
        update(ReservationTable)
        .where(
            ReservationTable.reservation_id == reservation_id,
            ReservationTable.status == ReservationTableStatus.ACTIVE.value,
        )
        .values(status=ReservationTableStatus.CANCELLED.value)
    )
    return result.rowcount or 0


def list_active_occupation_table_ids(
    db: Session, reservation_id: int
) -> list[int]:
    """Devuelve los IDs de las mesas con ocupación activa."""

    return list(
        db.scalars(
            select(ReservationTable.table_id)
            .where(
                ReservationTable.reservation_id == reservation_id,
                ReservationTable.status == ReservationTableStatus.ACTIVE.value,
            )
            .order_by(ReservationTable.table_id)
        )
    )


def replace_occupations(
    db: Session,
    reservation_id: int,
    table_ids: list[int],
    start_at: datetime,
    end_at: datetime,
) -> list[ReservationTable]:
    """Sustituye todas las ocupaciones de una reserva."""

    db.execute(
        delete(ReservationTable).where(
            ReservationTable.reservation_id == reservation_id
        )
    )
    occupations = [
        ReservationTable(
            reservation_id=reservation_id,
            table_id=table_id,
            start_at=start_at,
            end_at=end_at,
            status=ReservationTableStatus.ACTIVE.value,
        )
        for table_id in table_ids
    ]
    db.add_all(occupations)
    db.flush()
    return occupations


def list_occupations(db: Session, reservation_id: int) -> list[ReservationTable]:
    """Devuelve las ocupaciones de una reserva en orden de creación."""

    return list(
        db.scalars(
            select(ReservationTable)
            .where(ReservationTable.reservation_id == reservation_id)
            .order_by(ReservationTable.id)
        )
    )


def list_history(
    db: Session, reservation_id: int
) -> list[ReservationStatusHistory]:
    """Devuelve el historial de estados de una reserva en orden cronológico."""

    return list(
        db.scalars(
            select(ReservationStatusHistory)
            .where(ReservationStatusHistory.reservation_id == reservation_id)
            .order_by(
                ReservationStatusHistory.changed_at,
                ReservationStatusHistory.id,
            )
        )
    )
