"""Pruebas de validación previa de reservas (ST-RES-03.2)."""

import pytest

pytest.importorskip(
    "app.models.reservation_model",
    reason="Requiere el esquema compartido de HU-AUT-02",
)

from datetime import date, datetime, time, timedelta  # noqa: E402
from zoneinfo import ZoneInfo  # noqa: E402

from app.core.kernel.errors import AppError  # noqa: E402
from app.models import (  # noqa: E402
    DiningTable,
    OpeningHours,
    Reservation,
    Restaurant,
    TableCombination,
    TableCombinationTable,
)
from app.models.enums import ReservationStatus  # noqa: E402
from app.modules.reservations.schemas.reservation import ReservationCreate  # noqa: E402
from app.modules.reservations.services.validation import validate_reservation  # noqa: E402

TZ = ZoneInfo("Europe/Madrid")
START = datetime(2026, 1, 5, 20, 0, tzinfo=TZ)
END = datetime(2026, 1, 5, 21, 0, tzinfo=TZ)


@pytest.fixture
def open_restaurant(db, restaurant):
    for day in range(1, 8):
        db.add_all(
            [
                OpeningHours(
                    restaurant_id=restaurant.id,
                    day_of_week=day,
                    period="morning",
                    open_time=time(13, 0),
                    close_time=time(16, 0),
                ),
                OpeningHours(
                    restaurant_id=restaurant.id,
                    day_of_week=day,
                    period="afternoon",
                    open_time=time(20, 0),
                    close_time=time(23, 0),
                ),
            ]
        )
    db.flush()
    return restaurant


def _table(
    db,
    restaurant,
    *,
    number: int = 1,
    max_capacity: int = 4,
    is_active: bool = True,
) -> DiningTable:
    table = DiningTable(
        restaurant_id=restaurant.id,
        number=number,
        min_capacity=1,
        max_capacity=max_capacity,
        location="interior",
        is_active=is_active,
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
    name: str = "A+B",
    capacity: int = 6,
    is_enabled: bool = True,
    valid_from: date | None = None,
    valid_to: date | None = None,
) -> TableCombination:
    combination = TableCombination(
        restaurant_id=restaurant.id,
        name=name,
        capacity=capacity,
        is_enabled=is_enabled,
        valid_from=valid_from,
        valid_to=valid_to,
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


def _existing_reservation(
    db,
    restaurant,
    *,
    phone: str = "600000001",
    email: str | None = None,
    start_at: datetime = START,
    end_at: datetime = END,
    status: str = ReservationStatus.SEATED.value,
) -> Reservation:
    reservation = Reservation(
        restaurant_id=restaurant.id,
        customer_name="Cliente existente",
        phone=phone,
        email=email,
        party_size=2,
        start_at=start_at,
        end_at=end_at,
        status=status,
    )
    db.add(reservation)
    db.flush()
    return reservation


def _payload(
    *,
    phone: str = "600000001",
    email: str | None = None,
    party_size: int = 2,
    start_at: datetime = START,
    table_ids: list[int] | None = None,
    combination_id: int | None = None,
) -> ReservationCreate:
    return ReservationCreate(
        customer_name="Ana",
        phone=phone,
        email=email,
        party_size=party_size,
        start_at=start_at,
        table_ids=table_ids or [],
        combination_id=combination_id,
    )


def _expect_error(code: str, status_code: int, call) -> None:
    with pytest.raises(AppError) as error:
        call()

    assert error.value.code == code
    assert error.value.status_code == status_code


def test_valid_single_table_reservation(db, open_restaurant):
    table = _table(db, open_restaurant, max_capacity=4)

    result = validate_reservation(
        db,
        open_restaurant,
        _payload(party_size=4, table_ids=[table.id]),
    )

    assert [item.id for item in result.tables] == [table.id]
    assert result.combination is None
    assert result.end_at - result.start_at == timedelta(minutes=60)


def test_party_size_must_be_positive(db, open_restaurant):
    table = _table(db, open_restaurant)
    payload = ReservationCreate.model_construct(
        customer_name="Ana",
        phone="600000001",
        email=None,
        party_size=0,
        start_at=START,
        table_ids=[table.id],
        combination_id=None,
        notes=None,
    )

    _expect_error(
        "VALIDATION_ERROR",
        422,
        lambda: validate_reservation(db, open_restaurant, payload),
    )


def test_requires_tables_or_combination(db, open_restaurant):
    payload = ReservationCreate.model_construct(
        customer_name="Ana",
        phone="600000001",
        email=None,
        party_size=2,
        start_at=START,
        table_ids=[],
        combination_id=None,
        notes=None,
    )

    _expect_error(
        "VALIDATION_ERROR",
        422,
        lambda: validate_reservation(db, open_restaurant, payload),
    )


def test_inactive_table_is_rejected(db, open_restaurant):
    table = _table(db, open_restaurant, is_active=False)

    _expect_error(
        "TABLE_NOT_AVAILABLE",
        409,
        lambda: validate_reservation(
            db,
            open_restaurant,
            _payload(table_ids=[table.id]),
        ),
    )


def test_table_from_other_restaurant_is_not_found(db, open_restaurant):
    other = Restaurant(id=2, name="Otro", time_zone="Europe/Madrid")
    db.add(other)
    db.flush()
    table = _table(db, other, number=1)

    _expect_error(
        "TABLE_NOT_FOUND",
        404,
        lambda: validate_reservation(
            db,
            open_restaurant,
            _payload(table_ids=[table.id]),
        ),
    )


def test_unknown_table_is_not_found(db, open_restaurant):
    _expect_error(
        "TABLE_NOT_FOUND",
        404,
        lambda: validate_reservation(
            db,
            open_restaurant,
            _payload(table_ids=[9999]),
        ),
    )


def test_single_table_capacity_exceeded(db, open_restaurant):
    table = _table(db, open_restaurant, max_capacity=2)

    _expect_error(
        "CAPACITY_EXCEEDED",
        422,
        lambda: validate_reservation(
            db,
            open_restaurant,
            _payload(party_size=4, table_ids=[table.id]),
        ),
    )


def test_multiple_independent_tables_capacity_is_summed(db, open_restaurant):
    table_a = _table(db, open_restaurant, number=1, max_capacity=2)
    table_b = _table(db, open_restaurant, number=2, max_capacity=2)

    result = validate_reservation(
        db,
        open_restaurant,
        _payload(party_size=4, table_ids=[table_a.id, table_b.id]),
    )

    assert {item.id for item in result.tables} == {table_a.id, table_b.id}


def test_multiple_independent_tables_capacity_exceeded(db, open_restaurant):
    table_a = _table(db, open_restaurant, number=1, max_capacity=2)
    table_b = _table(db, open_restaurant, number=2, max_capacity=2)

    _expect_error(
        "CAPACITY_EXCEEDED",
        422,
        lambda: validate_reservation(
            db,
            open_restaurant,
            _payload(
                party_size=5,
                table_ids=[table_a.id, table_b.id],
            ),
        ),
    )


def test_combination_capacity_is_used(db, open_restaurant):
    table_a = _table(db, open_restaurant, number=1)
    table_b = _table(db, open_restaurant, number=2)
    combination = _combination(
        db,
        open_restaurant,
        tables=[table_a, table_b],
        capacity=6,
    )

    result = validate_reservation(
        db,
        open_restaurant,
        _payload(party_size=5, combination_id=combination.id),
    )

    assert result.combination is not None
    assert result.combination.id == combination.id
    assert {item.id for item in result.tables} == {table_a.id, table_b.id}


def test_combination_capacity_exceeded(db, open_restaurant):
    table_a = _table(db, open_restaurant, number=1)
    table_b = _table(db, open_restaurant, number=2)
    combination = _combination(
        db,
        open_restaurant,
        tables=[table_a, table_b],
        capacity=6,
    )

    _expect_error(
        "CAPACITY_EXCEEDED",
        422,
        lambda: validate_reservation(
            db,
            open_restaurant,
            _payload(party_size=7, combination_id=combination.id),
        ),
    )


def test_combination_with_matching_tables(db, open_restaurant):
    table_a = _table(db, open_restaurant, number=1)
    table_b = _table(db, open_restaurant, number=2)
    combination = _combination(
        db,
        open_restaurant,
        tables=[table_a, table_b],
    )

    result = validate_reservation(
        db,
        open_restaurant,
        _payload(
            combination_id=combination.id,
            table_ids=[table_b.id, table_a.id],
        ),
    )

    assert {item.id for item in result.tables} == {table_a.id, table_b.id}


def test_combination_with_mismatched_tables_is_rejected(db, open_restaurant):
    table_a = _table(db, open_restaurant, number=1)
    table_b = _table(db, open_restaurant, number=2)
    combination = _combination(
        db,
        open_restaurant,
        tables=[table_a, table_b],
    )

    _expect_error(
        "VALIDATION_ERROR",
        422,
        lambda: validate_reservation(
            db,
            open_restaurant,
            _payload(
                combination_id=combination.id,
                table_ids=[table_a.id],
            ),
        ),
    )


def test_combination_must_be_enabled(db, open_restaurant):
    table_a = _table(db, open_restaurant, number=1)
    table_b = _table(db, open_restaurant, number=2)
    combination = _combination(
        db,
        open_restaurant,
        tables=[table_a, table_b],
        is_enabled=False,
    )

    _expect_error(
        "COMBINATION_NOT_AVAILABLE",
        409,
        lambda: validate_reservation(
            db,
            open_restaurant,
            _payload(combination_id=combination.id),
        ),
    )


def test_combination_validity_dates_are_enforced(db, open_restaurant):
    table_a = _table(db, open_restaurant, number=1)
    table_b = _table(db, open_restaurant, number=2)
    combination = _combination(
        db,
        open_restaurant,
        tables=[table_a, table_b],
        valid_to=date(2026, 1, 4),
    )

    _expect_error(
        "COMBINATION_NOT_AVAILABLE",
        409,
        lambda: validate_reservation(
            db,
            open_restaurant,
            _payload(combination_id=combination.id),
        ),
    )


def test_combination_requires_at_least_two_tables(db, open_restaurant):
    table = _table(db, open_restaurant, number=1)
    combination = _combination(
        db,
        open_restaurant,
        tables=[table],
    )

    _expect_error(
        "COMBINATION_NOT_AVAILABLE",
        409,
        lambda: validate_reservation(
            db,
            open_restaurant,
            _payload(combination_id=combination.id),
        ),
    )


def test_reservation_before_opening_is_rejected(db, open_restaurant):
    table = _table(db, open_restaurant)

    _expect_error(
        "OUTSIDE_OPENING_HOURS",
        422,
        lambda: validate_reservation(
            db,
            open_restaurant,
            _payload(
                start_at=datetime(2026, 1, 5, 12, 0, tzinfo=TZ),
                table_ids=[table.id],
            ),
        ),
    )


def test_reservation_ending_after_close_is_rejected(db, open_restaurant):
    table = _table(db, open_restaurant)

    _expect_error(
        "OUTSIDE_OPENING_HOURS",
        422,
        lambda: validate_reservation(
            db,
            open_restaurant,
            _payload(
                start_at=datetime(2026, 1, 5, 15, 30, tzinfo=TZ),
                table_ids=[table.id],
            ),
        ),
    )


def test_duplicate_by_normalized_phone(db, open_restaurant):
    table = _table(db, open_restaurant)
    _existing_reservation(
        db,
        open_restaurant,
        phone="600 000 001",
        status=ReservationStatus.SEATED.value,
    )

    _expect_error(
        "DUPLICATE_RESERVATION",
        409,
        lambda: validate_reservation(
            db,
            open_restaurant,
            _payload(phone="600-000-001", table_ids=[table.id]),
        ),
    )


def test_duplicate_by_normalized_email(db, open_restaurant):
    table = _table(db, open_restaurant)
    _existing_reservation(
        db,
        open_restaurant,
        email="ANA@Example.com",
        status=ReservationStatus.SEATED.value,
    )

    _expect_error(
        "DUPLICATE_RESERVATION",
        409,
        lambda: validate_reservation(
            db,
            open_restaurant,
            _payload(
                phone="600000002",
                email=" ana@example.com ",
                table_ids=[table.id],
            ),
        ),
    )


def test_confirmed_reservation_blocks_duplicate_phone(db, open_restaurant):
    table = _table(db, open_restaurant)
    _existing_reservation(
        db,
        open_restaurant,
        phone="600000001",
        email="existing@example.com",
        status=ReservationStatus.CONFIRMED.value,
    )

    _expect_error(
        "DUPLICATE_RESERVATION",
        409,
        lambda: validate_reservation(
            db,
            open_restaurant,
            _payload(phone="600000001", table_ids=[table.id]),
        ),
    )


def test_seated_reservation_blocks_duplicate(db, open_restaurant):
    table = _table(db, open_restaurant)
    _existing_reservation(
        db,
        open_restaurant,
        phone="600000001",
        status=ReservationStatus.SEATED.value,
    )

    _expect_error(
        "DUPLICATE_RESERVATION",
        409,
        lambda: validate_reservation(
            db,
            open_restaurant,
            _payload(phone="600000001", table_ids=[table.id]),
        ),
    )


def test_cancelled_reservation_does_not_block(db, open_restaurant):
    table = _table(db, open_restaurant)
    _existing_reservation(
        db,
        open_restaurant,
        phone="600000001",
        status=ReservationStatus.CANCELLED.value,
    )

    result = validate_reservation(
        db,
        open_restaurant,
        _payload(phone="600000001", table_ids=[table.id]),
    )

    assert result.tables[0].id == table.id


@pytest.mark.parametrize(
    "status",
    [
        ReservationStatus.COMPLETED.value,
        ReservationStatus.NO_SHOW.value,
    ],
)
def test_final_states_do_not_block(db, open_restaurant, status):
    table = _table(db, open_restaurant)
    _existing_reservation(
        db,
        open_restaurant,
        phone="600000001",
        status=status,
    )

    result = validate_reservation(
        db,
        open_restaurant,
        _payload(phone="600000001", table_ids=[table.id]),
    )

    assert result.tables[0].id == table.id


def test_non_overlapping_reservation_does_not_block(db, open_restaurant):
    table = _table(db, open_restaurant)
    _existing_reservation(
        db,
        open_restaurant,
        phone="600000001",
        start_at=datetime(2026, 1, 5, 18, 0, tzinfo=TZ),
        end_at=datetime(2026, 1, 5, 19, 0, tzinfo=TZ),
        status=ReservationStatus.SEATED.value,
    )

    result = validate_reservation(
        db,
        open_restaurant,
        _payload(phone="600000001", table_ids=[table.id]),
    )

    assert result.tables[0].id == table.id


def test_different_contact_does_not_block(db, open_restaurant):
    table = _table(db, open_restaurant)
    _existing_reservation(
        db,
        open_restaurant,
        phone="600000001",
        email="existing@example.com",
        status=ReservationStatus.SEATED.value,
    )

    result = validate_reservation(
        db,
        open_restaurant,
        _payload(
            phone="600000002",
            email="other@example.com",
            table_ids=[table.id],
        ),
    )

    assert result.tables[0].id == table.id


def test_exclude_reservation_id_allows_self(db, open_restaurant):
    table = _table(db, open_restaurant)
    existing = _existing_reservation(
        db,
        open_restaurant,
        phone="600000001",
        email="existing@example.com",
        status=ReservationStatus.CONFIRMED.value,
    )

    result = validate_reservation(
        db,
        open_restaurant,
        _payload(
            phone="600000001",
            email="existing@example.com",
            table_ids=[table.id],
        ),
        exclude_reservation_id=existing.id,
    )

    assert result.tables[0].id == table.id
