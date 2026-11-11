from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.database_connection import engine
from app.models import (
    Allergen,
    Category,
    DiningTable,
    Dish,
    DishAllergen,
    Employee,
    Menu,
    MenuCollection,
    MenuDish,
    Permission,
    Reservation,
    ReservationTable,
    Restaurant,
    Role,
    RolePermission,
    Schedule,
    TableCombination,
    TableCombinationTable,
    User,
    WorkShift,
)


@pytest.fixture(autouse=True)
def pg_constraints():
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist"))
        connection.execute(
            text(
                "ALTER TABLE reservation_tables "
                "DROP CONSTRAINT IF EXISTS ex_reservation_tables_no_overlap"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE reservation_tables "
                "ADD CONSTRAINT ex_reservation_tables_no_overlap "
                "EXCLUDE USING gist ("
                "table_id WITH =, "
                "tstzrange(start_at, end_at) WITH &&"
                ") WHERE (status = 'active')"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE work_shifts "
                "DROP CONSTRAINT IF EXISTS ex_work_shifts_no_overlap"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE work_shifts "
                "ADD CONSTRAINT ex_work_shifts_no_overlap "
                "EXCLUDE USING gist ("
                "employee_id WITH =, "
                "tstzrange(start_at, end_at) WITH &&"
                ") WHERE (status <> 'cancelled')"
            )
        )
        connection.execute(
            text(
                "DROP INDEX IF EXISTS uq_reservations_active_contact_date"
            )
        )
        connection.execute(
            text(
                "CREATE UNIQUE INDEX uq_reservations_active_contact_date "
                "ON reservations ("
                "restaurant_id, "
                "COALESCE(lower(email), phone), "
                "((start_at AT TIME ZONE 'UTC')::date)"
                ") WHERE status IN ('pending', 'confirmed')"
            )
        )
    yield


def _restaurant(db) -> Restaurant:
    restaurant = Restaurant(name="Pruebas", time_zone="Europe/Madrid")
    db.add(restaurant)
    db.flush()
    return restaurant


def _table(db, restaurant, number=1) -> DiningTable:
    table = DiningTable(
        restaurant_id=restaurant.id,
        number=number,
        min_capacity=1,
        max_capacity=4,
        location="interior",
        is_active=True,
        adjustable_capacity=False,
    )
    db.add(table)
    db.flush()
    return table


def _reservation(
    db,
    restaurant,
    phone="600000000",
    start=None,
    end=None,
) -> Reservation:
    start = start or datetime(2026, 1, 10, 13, tzinfo=timezone.utc)
    end = end or datetime(2026, 1, 10, 15, tzinfo=timezone.utc)
    reservation = Reservation(
        restaurant_id=restaurant.id,
        customer_name="Cliente",
        phone=phone,
        party_size=2,
        start_at=start,
        end_at=end,
        status="pending",
    )
    db.add(reservation)
    db.flush()
    return reservation


def _user(db, restaurant) -> User:
    role = Role(restaurant_id=restaurant.id, name="admin")
    db.add(role)
    db.flush()
    user = User(
        restaurant_id=restaurant.id,
        role_id=role.id,
        name="Usuario",
        email=f"user-{role.id}@example.com",
        password_hash="x",
    )
    db.add(user)
    db.flush()
    return user


def _employee(db, restaurant) -> Employee:
    user = _user(db, restaurant)
    employee = Employee(
        restaurant_id=restaurant.id,
        user_id=user.id,
        full_name="Empleado",
        job_position="waiter",
    )
    db.add(employee)
    db.flush()
    return employee


def _schedule(db, restaurant) -> Schedule:
    schedule = Schedule(
        restaurant_id=restaurant.id,
        period_start=date(2026, 1, 5),
        period_end=date(2026, 1, 11),
        status="draft",
    )
    db.add(schedule)
    db.flush()
    return schedule


def test_table_number_is_unique(db):
    restaurant = _restaurant(db)
    _table(db, restaurant, number=1)
    db.add(
        DiningTable(
            restaurant_id=restaurant.id,
            number=1,
            min_capacity=1,
            max_capacity=2,
            location="interior",
        )
    )
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


@pytest.mark.parametrize(
    ("min_capacity", "max_capacity"),
    [(0, 4), (4, 2)],
)
def test_table_capacity_checks(db, min_capacity, max_capacity):
    restaurant = _restaurant(db)
    db.add(
        DiningTable(
            restaurant_id=restaurant.id,
            number=1,
            min_capacity=min_capacity,
            max_capacity=max_capacity,
            location="interior",
        )
    )
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_dish_price_and_menu_price_checks(db):
    restaurant = _restaurant(db)
    category = Category(
        restaurant_id=restaurant.id,
        name="Principales",
    )
    db.add(category)
    db.flush()
    db.add(
        Dish(
            restaurant_id=restaurant.id,
            category_id=category.id,
            name="Plato",
            price=Decimal("-1"),
        )
    )
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()

    restaurant = _restaurant(db)
    collection = MenuCollection(
        restaurant_id=restaurant.id,
        name="Menús",
        type="daily",
    )
    db.add(collection)
    db.flush()
    db.add(
        Menu(
            collection_id=collection.id,
            name="Menú",
            own_price=Decimal("-1"),
        )
    )
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_user_email_is_case_insensitive_unique(db):
    restaurant = _restaurant(db)
    role = Role(restaurant_id=restaurant.id, name="admin")
    db.add(role)
    db.flush()
    db.add_all(
        [
            User(
                restaurant_id=restaurant.id,
                role_id=role.id,
                name="Uno",
                email="Test@Example.com",
                password_hash="x",
            ),
            User(
                restaurant_id=restaurant.id,
                role_id=role.id,
                name="Dos",
                email="test@example.com",
                password_hash="x",
            ),
        ]
    )
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_combination_does_not_repeat_table(db):
    restaurant = _restaurant(db)
    table = _table(db, restaurant)
    combination = TableCombination(
        restaurant_id=restaurant.id,
        name="Mesa grande",
        capacity=8,
    )
    db.add(combination)
    db.flush()
    db.add_all(
        [
            TableCombinationTable(
                combination_id=combination.id,
                table_id=table.id,
            ),
            TableCombinationTable(
                combination_id=combination.id,
                table_id=table.id,
            ),
        ]
    )
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_dish_allergen_and_menu_dish_do_not_repeat(db):
    restaurant = _restaurant(db)
    category = Category(restaurant_id=restaurant.id, name="Principales")
    db.add(category)
    db.flush()
    dish = Dish(
        restaurant_id=restaurant.id,
        category_id=category.id,
        name="Plato",
        price=Decimal("10.00"),
    )
    allergen = Allergen(code="GLUTEN", name="Gluten")
    db.add_all([dish, allergen])
    db.flush()
    db.add_all(
        [
            DishAllergen(dish_id=dish.id, allergen_id=allergen.id),
            DishAllergen(dish_id=dish.id, allergen_id=allergen.id),
        ]
    )
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()

    restaurant = _restaurant(db)
    category = Category(restaurant_id=restaurant.id, name="Principales")
    collection = MenuCollection(
        restaurant_id=restaurant.id,
        name="Menús",
        type="daily",
    )
    db.add_all([category, collection])
    db.flush()
    dish = Dish(
        restaurant_id=restaurant.id,
        category_id=category.id,
        name="Plato",
        price=Decimal("10.00"),
    )
    menu = Menu(
        collection_id=collection.id,
        name="Menú",
        own_price=Decimal("15.00"),
    )
    db.add_all([dish, menu])
    db.flush()
    db.add_all(
        [
            MenuDish(menu_id=menu.id, dish_id=dish.id, role="main"),
            MenuDish(menu_id=menu.id, dish_id=dish.id, role="main"),
        ]
    )
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_role_permission_does_not_repeat(db):
    restaurant = _restaurant(db)
    role = Role(restaurant_id=restaurant.id, name="admin")
    permission = Permission(name="dish:create")
    db.add_all([role, permission])
    db.flush()
    db.add_all(
        [
            RolePermission(role_id=role.id, permission_id=permission.id),
            RolePermission(role_id=role.id, permission_id=permission.id),
        ]
    )
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_reservation_tables_cannot_overlap(db):
    restaurant = _restaurant(db)
    table = _table(db, restaurant)
    first = _reservation(db, restaurant, phone="600000001")
    second = _reservation(db, restaurant, phone="600000002")
    db.add_all(
        [
            ReservationTable(
                reservation_id=first.id,
                table_id=table.id,
                start_at=first.start_at,
                end_at=first.end_at,
                status="active",
            ),
            ReservationTable(
                reservation_id=second.id,
                table_id=table.id,
                start_at=second.start_at,
                end_at=second.end_at,
                status="active",
            ),
        ]
    )
    with pytest.raises(IntegrityError) as error:
        db.flush()
    assert error.value.orig.sqlstate == "23P01"
    db.rollback()


def test_work_shifts_cannot_overlap(db):
    restaurant = _restaurant(db)
    employee = _employee(db, restaurant)
    schedule = _schedule(db, restaurant)
    start = datetime(2026, 1, 10, 8, tzinfo=timezone.utc)
    end = datetime(2026, 1, 10, 16, tzinfo=timezone.utc)
    db.add_all(
        [
            WorkShift(
                schedule_id=schedule.id,
                employee_id=employee.id,
                start_at=start,
                end_at=end,
                type="morning",
                status="scheduled",
            ),
            WorkShift(
                schedule_id=schedule.id,
                employee_id=employee.id,
                start_at=start,
                end_at=end,
                type="morning",
                status="scheduled",
            ),
        ]
    )
    with pytest.raises(IntegrityError) as error:
        db.flush()
    assert error.value.orig.sqlstate == "23P01"
    db.rollback()


def test_active_reservations_cannot_duplicate_contact_date(db):
    restaurant = _restaurant(db)
    _reservation(db, restaurant, phone="600000001")
    db.add(
        Reservation(
            restaurant_id=restaurant.id,
            customer_name="Otro cliente",
            phone="600000001",
            party_size=2,
            start_at=datetime(2026, 1, 10, 20, tzinfo=timezone.utc),
            end_at=datetime(2026, 1, 10, 22, tzinfo=timezone.utc),
            status="confirmed",
        )
    )
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()
