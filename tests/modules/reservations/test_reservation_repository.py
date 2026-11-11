"""Pruebas de la base del agregado de reserva (ST-RES-03.1).

Requieren el esquema compartido de HU-AUT-02. Mientras esa rama no esté en el
árbol de trabajo, el módulo se omite para no romper el resto de la suite.
"""

import pytest

pytest.importorskip(
    "app.models.reservation_model",
    reason="Requiere el esquema compartido de HU-AUT-02",
)

from datetime import datetime, timezone

from pydantic import ValidationError
from sqlalchemy import delete, func, select

from app.models import (
    DiningTable,
    Reservation,
    ReservationStatusHistory,
    ReservationTable,
    Restaurant,
    TableCombination,
    TableCombinationTable,
)
from app.models.enums import (
    ReservationStatus,
    ReservationTableStatus,
)
from app.modules.reservations.repositories import reservation as repo
from app.modules.reservations.schemas.reservation import (
    ReservationCreate,
    ReservationDetailRead,
)

START = datetime(2026, 1, 10, 20, 0, tzinfo=timezone.utc)
END = datetime(2026, 1, 10, 21, 0, tzinfo=timezone.utc)


def _table(
    db,
    restaurant,
    *,
    number: int = 1,
    max_capacity: int = 4,
) -> DiningTable:
    table = DiningTable(
        restaurant_id=restaurant.id,
        number=number,
        min_capacity=1,
        max_capacity=max_capacity,
        location="interior",
        is_active=True,
        adjustable_capacity=False,
    )
    db.add(table)
    db.flush()
    return table


def _combination(
    db,
    restaurant,
    *,
    name: str = "A+B",
    capacity: int = 6,
) -> TableCombination:
    combination = TableCombination(
        restaurant_id=restaurant.id,
        name=name,
        capacity=capacity,
    )
    db.add(combination)
    db.flush()
    return combination


def _link_combination(db, combination: TableCombination, tables: list[DiningTable]) -> None:
    db.add_all(
        [
            TableCombinationTable(
                combination_id=combination.id,
                table_id=table.id,
            )
            for table in tables
        ]
    )
    db.flush()


def _reservation(
    db,
    restaurant,
    *,
    phone: str = "600000001",
    start_at: datetime = START,
    end_at: datetime = END,
    combination_id: int | None = None,
    status: str = ReservationStatus.CONFIRMED.value,
) -> Reservation:
    return repo.add_reservation(
        db,
        Reservation(
            restaurant_id=restaurant.id,
            combination_id=combination_id,
            customer_name="Cliente de prueba",
            phone=phone,
            party_size=4,
            start_at=start_at,
            end_at=end_at,
            status=status,
        ),
    )


def _occupy(
    db,
    reservation: Reservation,
    table: DiningTable,
    *,
    status: str = ReservationTableStatus.ACTIVE.value,
) -> ReservationTable:
    return repo.add_occupation(
        db,
        ReservationTable(
            reservation_id=reservation.id,
            table_id=table.id,
            start_at=reservation.start_at,
            end_at=reservation.end_at,
            status=status,
        ),
    )


def test_single_table_reservation_persists_one_occupation(db, restaurant):
    table = _table(db, restaurant)
    reservation = _reservation(db, restaurant)
    _occupy(db, reservation, table)
    db.commit()

    detail = repo.get_reservation_detail(db, reservation.id, restaurant.id)

    assert detail is not None
    assert detail.reservation.phone == "600000001"
    assert detail.reservation.status == ReservationStatus.CONFIRMED
    assert len(detail.tables) == 1
    assert detail.tables[0].table_id == table.id
    assert detail.history == []


def test_combination_reservation_persists_all_combination_tables(db, restaurant):
    table_a = _table(db, restaurant, number=1)
    table_b = _table(db, restaurant, number=2)
    combination = _combination(db, restaurant, capacity=6)
    _link_combination(db, combination, [table_a, table_b])

    reservation = _reservation(db, restaurant, combination_id=combination.id)
    _occupy(db, reservation, table_a)
    _occupy(db, reservation, table_b)
    db.commit()

    detail = repo.get_reservation_detail(db, reservation.id, restaurant.id)

    assert detail is not None
    assert detail.reservation.combination_id == combination.id
    assert {occupation.table_id for occupation in detail.tables} == {
        table_a.id,
        table_b.id,
    }
    assert repo.get_combination_table_ids(db, combination.id) == sorted(
        [table_a.id, table_b.id]
    )


def test_multiple_independent_tables_persist_occupations(db, restaurant):
    table_a = _table(db, restaurant, number=1)
    table_b = _table(db, restaurant, number=2)
    reservation = _reservation(db, restaurant, combination_id=None)
    _occupy(db, reservation, table_a)
    _occupy(db, reservation, table_b)
    db.commit()

    detail = repo.get_reservation_detail(db, reservation.id, restaurant.id)

    assert detail is not None
    assert detail.reservation.combination_id is None
    assert len(detail.tables) == 2
    assert [occupation.table_id for occupation in detail.tables] == sorted(
        [table_a.id, table_b.id]
    )


def test_reservation_detail_returns_occupations_and_history(db, restaurant):
    table = _table(db, restaurant)
    reservation = _reservation(db, restaurant)
    _occupy(db, reservation, table)
    repo.add_history(
        db,
        ReservationStatusHistory(
            reservation_id=reservation.id,
            previous_status=None,
            new_status=ReservationStatus.PENDING.value,
            changed_by_user_id=None,
            reason="Reserva creada",
        ),
    )
    repo.add_history(
        db,
        ReservationStatusHistory(
            reservation_id=reservation.id,
            previous_status=ReservationStatus.PENDING.value,
            new_status=ReservationStatus.CONFIRMED.value,
            changed_by_user_id=None,
            reason="Confirmada por el restaurante",
        ),
    )
    db.commit()

    detail = repo.get_reservation_detail(db, reservation.id, restaurant.id)
    schema = ReservationDetailRead.model_validate(detail)

    assert detail is not None
    assert len(detail.history) == 2
    assert detail.history[0].reason == "Reserva creada"
    assert detail.history[1].reason == "Confirmada por el restaurante"
    assert schema.reservation.phone == "600000001"
    assert schema.history[0].previous_status is None
    assert schema.history[0].new_status == ReservationStatus.PENDING
    assert schema.history[1].new_status == ReservationStatus.CONFIRMED
    assert schema.tables[0].status == ReservationTableStatus.ACTIVE


def test_repository_scopes_reservation_and_combination_by_restaurant(db, restaurant):
    other = Restaurant(
        id=2,
        name="Otro restaurante",
        time_zone="Europe/Madrid",
    )
    db.add(other)
    db.flush()

    table = _table(db, restaurant)
    combination = _combination(db, restaurant)
    _link_combination(db, combination, [table])
    reservation = _reservation(db, restaurant, combination_id=combination.id)
    _occupy(db, reservation, table)
    db.commit()

    assert repo.get_reservation(db, reservation.id, other.id) is None
    assert repo.get_combination(db, combination.id, other.id) is None
    assert repo.get_reservation_detail(db, reservation.id, other.id) is None


def test_get_tables_by_ids_returns_stable_order(db, restaurant):
    table_a = _table(db, restaurant, number=1)
    table_b = _table(db, restaurant, number=2)
    db.commit()

    tables = repo.get_tables_by_ids(db, [table_b.id, table_a.id])

    assert [table.id for table in tables] == sorted([table_a.id, table_b.id])


def test_deleting_reservation_cascades_occupations_and_history(db, restaurant):
    table = _table(db, restaurant)
    reservation = _reservation(db, restaurant)
    _occupy(db, reservation, table)
    repo.add_history(
        db,
        ReservationStatusHistory(
            reservation_id=reservation.id,
            previous_status=None,
            new_status=ReservationStatus.CONFIRMED.value,
            changed_by_user_id=None,
            reason=None,
        ),
    )
    db.commit()
    reservation_id = reservation.id

    db.execute(delete(Reservation).where(Reservation.id == reservation_id))
    db.commit()

    assert (
        db.scalar(
            select(func.count())
            .select_from(ReservationTable)
            .where(ReservationTable.reservation_id == reservation_id)
        )
        == 0
    )
    assert (
        db.scalar(
            select(func.count())
            .select_from(ReservationStatusHistory)
            .where(ReservationStatusHistory.reservation_id == reservation_id)
        )
        == 0
    )


def test_create_schema_uses_shared_field_names():
    payload = ReservationCreate(
        customer_name="Ana",
        phone="600123123",
        email="ana@example.com",
        party_size=2,
        start_at=START,
        table_ids=[1],
    )

    dumped = payload.model_dump()

    assert dumped["phone"] == "600123123"
    assert dumped["email"] == "ana@example.com"
    assert "customer_phone" not in dumped
    assert "customer_email" not in dumped


def test_create_schema_requires_tables_or_combination():
    with pytest.raises(ValidationError):
        ReservationCreate(
            customer_name="Ana",
            phone="600123123",
            party_size=2,
            start_at=START,
        )


def test_create_schema_rejects_repeated_tables():
    with pytest.raises(ValidationError):
        ReservationCreate(
            customer_name="Ana",
            phone="600123123",
            party_size=2,
            start_at=START,
            table_ids=[1, 1],
        )
