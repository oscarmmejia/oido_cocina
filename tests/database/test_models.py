"""Contract of the SQLAlchemy metadata: normalized schema and relationships.

These checks do not touch the database, so they run even when no local PostgreSQL
is available.
"""

from app.database.base import Base
from app.models import (
    AuditLog,
    OpeningHours,
    Restaurant,
    RestaurantSettings,
    RolePermission,
    User,
)

EXPECTED_TABLES = {
    "allergens",
    "audit_logs",
    "categories",
    "dish_allergens",
    "dishes",
    "menu_collections",
    "menu_dishes",
    "menus",
    "opening_hours",
    "permissions",
    "restaurant_settings",
    "restaurants",
    "role_permissions",
    "roles",
    "users",
}

RESTAURANT_COLUMNS = {"id", "name", "timezone", "is_active", "created_at", "updated_at"}


def test_metadata_registers_the_fifteen_expected_tables():
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_every_table_has_a_primary_key():
    for table in Base.metadata.sorted_tables:
        assert table.primary_key.columns, f"{table.name} has no primary key"


def test_restaurant_is_identity_only():
    assert set(Restaurant.__table__.columns.keys()) == RESTAURANT_COLUMNS


def test_restaurant_settings_key_and_foreign_key():
    table = RestaurantSettings.__table__

    assert set(table.primary_key.columns.keys()) == {"restaurant_id"}
    foreign_keys = {fk.target_fullname for fk in table.foreign_keys}
    assert foreign_keys == {"restaurants.id"}


def test_opening_hours_are_unique_per_restaurant_day_and_period():
    table = OpeningHours.__table__
    unique_columns = {
        tuple(column.name for column in constraint.columns)
        for constraint in table.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }

    assert ("restaurant_id", "day_of_week", "period") in unique_columns


def test_user_restaurant_is_optional_but_role_is_required():
    assert User.__table__.columns["restaurant_id"].nullable is True
    assert User.__table__.columns["role_id"].nullable is False


def test_role_permissions_and_audit_logs_have_no_updated_at():
    assert "updated_at" not in RolePermission.__table__.columns
    assert "updated_at" not in AuditLog.__table__.columns
