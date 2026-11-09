"""Contract of the authentication/authorization schema: exactly one role per user.

The metadata checks run without a database. The duplicate checks run against the
configured PostgreSQL database and are rolled back by the `session` fixture.
"""

from datetime import time

import pytest
from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError

from app.database.base import Base
from app.models import (
    OpeningHours,
    Permission,
    Restaurant,
    RestaurantSettings,
    Role,
    RolePermission,
    User,
)


def test_users_role_id_is_not_null_and_references_roles():
    column = User.__table__.columns["role_id"]

    assert column.nullable is False
    assert {fk.target_fullname for fk in column.foreign_keys} == {"roles.id"}


def test_there_is_no_many_to_many_table_between_users_and_roles():
    assert "user_roles" not in Base.metadata.tables
    # A single direct FK is what makes the role unique per user.
    assert len(
        [fk for fk in User.__table__.foreign_keys if fk.target_fullname == "roles.id"]
    ) == 1


def test_role_permissions_primary_key_is_role_and_permission():
    primary_key = tuple(c.name for c in RolePermission.__table__.primary_key.columns)

    assert primary_key == ("role_id", "permission_id")


def test_postgres_rejects_a_duplicate_role_permission(session):
    role = Role(name="contract-duplicate-role")
    permission = Permission(code="contract:duplicate")
    session.add_all([role, permission])
    session.flush()

    session.add(RolePermission(role_id=role.id, permission_id=permission.id))
    session.flush()

    with pytest.raises(IntegrityError) as error:
        with session.begin_nested():
            session.execute(
                insert(RolePermission).values(
                    role_id=role.id, permission_id=permission.id
                )
            )

    assert error.value.orig.sqlstate == "23505"


def test_postgres_rejects_a_second_settings_row_for_the_same_restaurant(session):
    restaurant = Restaurant(name="contract-settings-restaurant", timezone="Europe/Madrid")
    session.add(restaurant)
    session.flush()

    session.add(RestaurantSettings(restaurant_id=restaurant.id))
    session.flush()

    with pytest.raises(IntegrityError) as error:
        with session.begin_nested():
            session.execute(insert(RestaurantSettings).values(restaurant_id=restaurant.id))

    assert error.value.orig.sqlstate == "23505"


def test_postgres_rejects_duplicate_opening_hours(session):
    restaurant = Restaurant(name="contract-hours-restaurant", timezone="Europe/Madrid")
    session.add(restaurant)
    session.flush()

    values = {
        "restaurant_id": restaurant.id,
        "day_of_week": 1,
        "period": "morning",
        "open_time": time(13, 0),
        "close_time": time(16, 0),
    }
    session.add(OpeningHours(**values))
    session.flush()

    with pytest.raises(IntegrityError) as error:
        with session.begin_nested():
            session.execute(insert(OpeningHours).values(**values))

    assert error.value.orig.sqlstate == "23505"


def test_user_role_and_restaurant_relationships_are_bidirectional():
    role = Role(name="contract-role")
    restaurant = Restaurant(name="contract-restaurant", timezone="Europe/Madrid")
    user = User(
        email="contract@example.com",
        password_hash="hash",
        role=role,
        restaurant=restaurant,
    )

    assert user.role is role
    assert role.users == [user]
    assert user.restaurant is restaurant
    assert restaurant.users == [user]


def test_opening_hours_restaurant_relationship_is_bidirectional():
    restaurant = Restaurant(name="contract-hours", timezone="Europe/Madrid")
    hours = OpeningHours(
        day_of_week=1,
        period="morning",
        open_time=time(13, 0),
        close_time=time(16, 0),
        restaurant=restaurant,
    )

    assert hours.restaurant is restaurant
    assert restaurant.opening_hours == [hours]


def test_restaurant_settings_relationship_is_still_bidirectional():
    restaurant = Restaurant(name="contract-settings", timezone="Europe/Madrid")
    settings = RestaurantSettings(restaurant=restaurant)

    assert settings.restaurant is restaurant
    assert restaurant.settings is settings
