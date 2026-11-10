"""Pruebas de la creación transaccional de reservas (ST-RES-03.3)."""

import pytest

pytest.importorskip(
    "app.models.reservation_model",
    reason="Requiere el esquema compartido de HU-AUT-02",
)

from datetime import datetime, time, timedelta  # noqa: E402
from zoneinfo import ZoneInfo  # noqa: E402

from sqlalchemy import func, select  # noqa: E402

from app.core.kernel.errors import AppError  # noqa: E402
from app.models import (  # noqa: E402
    DiningTable,
    Reservation,
    ReservationStatusHistory,
    ReservationTable,
    Role,
    TableCombination,
    TableCombinationTable,
    User,
)
from app.models.enums import ReservationStatus, ReservationTableStatus  # noqa: E402
from app.modules.reservations.repositories import reservation as reservation_repo  # noqa: E402
from app.modules.reservations.schemas.reservation import ReservationCreate  # noqa: E402
from app.modules.reservations.services.creation import create_reservation  # noqa: E402

TZ = ZoneInfo("Europe/Madrid")
START = datetime(2026, 1, 5, 20, 0, tzinfo=TZ)
END = datetime(2026, 1, 5, 21, 0, tzinfo=TZ)


@pytest.fixture
def open_restaurant(db, restaurant):
    restaurant.open_time = time(20, 0)
    restaurant.close_time = time(23, 0)
    restaurant.day_of_week = None
    restaurant.period = "afternoon"
    db.commit()
    return restaurant


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
    tables: list[DiningTable],
    capacity: int = 6,
) -> TableCombination:
    combination = TableCombination(
        restaurant_id=restaurant.id,
        name="A+B",
        capacity=capacity,
    )
    db.add(combination)
    db.flush()
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
    return combination


def _user(db, restaurant) -> User:
    role = Role(restaurant_id=restaurant.id, name="Sala")
    db.add(role)
    db.flush()
    user = User(
        restaurant_id=restaurant.id,
        role_id=role.id,
        name="Personal de sala",
        email="sala@example.com",
        password_hash="hash",
    )
    db.add(user)
    db.flush()
    return user


def _payload(
    *,
    phone: str = "600000001",
    party_size: int = 4,
    start_at: datetime = START,
    table_ids: list[int] | None = None,
    combination_id: int | None = None,
) -> ReservationCreate:
    return ReservationCreate(
        customer_name="Ana",
        phone=phone,
        party_size=party_size,
        start_at=start_at,
        table_ids=table_ids or [],
        combination_id=combination_id,
    )


def _existing_reservation(
    db,
    restaurant,
    table: DiningTable,
    *,
    phone: str = "600000099",
    start_at: datetime = START,
    end_at: datetime = END,
) -> Reservation:
    reservation = Reservation(
        restaurant_id=restaurant.id,
        customer_name="Cliente existente",
        phone=phone,
        party_size=2,
        start_at=start_at,
        end_at=end_at,
        status=ReservationStatus.CONFIRMED.value,
    )
    db.add(reservation)
    db.flush()
    db.add(
        ReservationTable(
            reservation_id=reservation.id,
            table_id=table.id,
            start_at=start_at,
            end_at=end_at,
            status=ReservationTableStatus.ACTIVE.value,
        )
    )
    db.flush()
    return reservation


def _expect_error(code: str, status_code: int, call) -> None:
    with pytest.raises(AppError) as error:
        call()

    assert error.value.code == code
    assert error.value.status_code == status_code


def test_create_single_table_reservation(db, open_restaurant):
    table = _table(db, open_restaurant, max_capacity=4)
    user = _user(db, open_restaurant)
    user_id = user.id
    table_id = table.id

    detail = create_reservation(
        db,
        open_restaurant,
        _payload(party_size=4, table_ids=[table_id]),
        created_by_user_id=user_id,
    )

    assert detail.reservation.status == ReservationStatus.CONFIRMED.value
    assert detail.reservation.created_by_user_id == user_id
    assert detail.reservation.combination_id is None
    assert detail.reservation.phone == "600000001"
    assert detail.reservation.end_at - detail.reservation.start_at == timedelta(
        minutes=60
    )
    assert len(detail.tables) == 1
    assert detail.tables[0].table_id == table_id
    assert detail.tables[0].status == ReservationTableStatus.ACTIVE.value
    assert len(detail.history) == 1
    assert detail.history[0].previous_status is None
    assert detail.history[0].new_status == ReservationStatus.CONFIRMED.value
    assert detail.history[0].changed_by_user_id == user_id
    assert detail.history[0].reason == "Reserva creada"


def test_create_combination_reservation_occupies_all_tables(db, open_restaurant):
    table_a = _table(db, open_restaurant, number=1)
    table_b = _table(db, open_restaurant, number=2)
    combination = _combination(
        db,
        open_restaurant,
        tables=[table_a, table_b],
        capacity=6,
    )
    user = _user(db, open_restaurant)
    combination_id = combination.id
    table_ids = {table_a.id, table_b.id}

    detail = create_reservation(
        db,
        open_restaurant,
        _payload(party_size=5, combination_id=combination_id),
        created_by_user_id=user.id,
    )

    assert detail.reservation.combination_id == combination_id
    assert {occupation.table_id for occupation in detail.tables} == table_ids


def test_create_multi_table_independent_reservation(db, open_restaurant):
    table_a = _table(db, open_restaurant, number=1)
    table_b = _table(db, open_restaurant, number=2)
    user = _user(db, open_restaurant)
    table_ids = [table_a.id, table_b.id]

    detail = create_reservation(
        db,
        open_restaurant,
        _payload(party_size=4, table_ids=table_ids),
        created_by_user_id=user.id,
    )

    assert detail.reservation.combination_id is None
    assert {occupation.table_id for occupation in detail.tables} == set(table_ids)


def test_overlapping_reservation_is_rejected(db, open_restaurant):
    table = _table(db, open_restaurant)
    user = _user(db, open_restaurant)
    _existing_reservation(db, open_restaurant, table)

    _expect_error(
        "TABLE_NOT_AVAILABLE",
        409,
        lambda: create_reservation(
            db,
            open_restaurant,
            _payload(
                phone="600000001",
                party_size=2,
                start_at=datetime(2026, 1, 5, 20, 30, tzinfo=TZ),
                table_ids=[table.id],
            ),
            created_by_user_id=user.id,
        ),
    )


def test_contiguous_reservation_is_allowed(db, open_restaurant):
    table = _table(db, open_restaurant)
    user = _user(db, open_restaurant)
    _existing_reservation(db, open_restaurant, table)

    detail = create_reservation(
        db,
        open_restaurant,
        _payload(
            phone="600000001",
            party_size=2,
            start_at=datetime(2026, 1, 5, 21, 0, tzinfo=TZ),
            table_ids=[table.id],
        ),
        created_by_user_id=user.id,
    )

    assert detail.reservation.phone == "600000001"


def test_rollback_when_occupation_fails(db, open_restaurant, monkeypatch):
    table_a = _table(db, open_restaurant, number=1)
    table_b = _table(db, open_restaurant, number=2)
    user = _user(db, open_restaurant)
    phone = "600000001"

    original_add_occupation = reservation_repo.add_occupation
    calls = {"count": 0}

    def failing_add_occupation(db_session, occupation):
        calls["count"] += 1
        if calls["count"] == 2:
            raise RuntimeError("fallo simulado en la segunda mesa")
        return original_add_occupation(db_session, occupation)

    monkeypatch.setattr(
        reservation_repo,
        "add_occupation",
        failing_add_occupation,
    )

    with pytest.raises(RuntimeError):
        create_reservation(
            db,
            open_restaurant,
            _payload(
                phone=phone,
                party_size=4,
                table_ids=[table_a.id, table_b.id],
            ),
            created_by_user_id=user.id,
        )

    assert (
        db.scalar(
            select(func.count())
            .select_from(Reservation)
            .where(Reservation.phone == phone)
        )
        == 0
    )
    assert (
        db.scalar(
            select(func.count())
            .select_from(ReservationTable)
        )
        == 0
    )
    assert (
        db.scalar(
            select(func.count())
            .select_from(ReservationStatusHistory)
        )
        == 0
    )
