"""Contract of `RestaurantSettings`: defaults, one row per restaurant and checks.

These tests run against the local PostgreSQL database and roll back afterwards.
"""

import pytest
from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database_connection import get_engine
from app.modules.settings.models.restaurant import Restaurant
from app.modules.settings.models.restaurant_settings import RestaurantSettings


def test_one_settings_per_restaurant():
    engine = get_engine()

    # Evitamos ejecutar esta prueba en un servidor remoto.
    assert engine.url.host in ("localhost", "127.0.0.1")

    with engine.connect() as connection:
        transaction = connection.begin()

        try:
            # Creamos un restaurante de prueba.
            restaurant_id = connection.execute(
                insert(Restaurant)
                .values(name="Prueba pytest", timezone="Europe/Madrid")
                .returning(Restaurant.id)
            ).scalar_one()

            settings = {
                "restaurant_id": restaurant_id,
                "courtesy_minutes": 10,
                "slot_minutes": 15,
                "default_reservation_minutes": 90,
            }

            # Primera configuración: válida.
            connection.execute(insert(RestaurantSettings).values(**settings))

            # Segunda configuración: debe rechazarse.
            with pytest.raises(IntegrityError) as error:
                with connection.begin_nested():
                    connection.execute(insert(RestaurantSettings).values(**settings))

            assert error.value.orig.sqlstate == "23505"

        finally:
            # Deshacemos los datos de prueba.
            transaction.rollback()


def test_settings_apply_the_business_defaults():
    engine = get_engine()
    assert engine.url.host in ("localhost", "127.0.0.1")

    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            restaurant_id = connection.execute(
                insert(Restaurant)
                .values(name="Prueba defaults", timezone="Europe/Madrid")
                .returning(Restaurant.id)
            ).scalar_one()

            connection.execute(
                insert(RestaurantSettings).values(restaurant_id=restaurant_id)
            )

            row = connection.execute(
                select(
                    RestaurantSettings.courtesy_minutes,
                    RestaurantSettings.slot_minutes,
                    RestaurantSettings.default_reservation_minutes,
                ).where(RestaurantSettings.restaurant_id == restaurant_id)
            ).one()

            assert tuple(row) == (5, 60, 60)
        finally:
            transaction.rollback()


def test_slot_minutes_must_be_positive():
    engine = get_engine()
    assert engine.url.host in ("localhost", "127.0.0.1")

    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            restaurant_id = connection.execute(
                insert(Restaurant)
                .values(name="Prueba check", timezone="Europe/Madrid")
                .returning(Restaurant.id)
            ).scalar_one()
            connection.execute(
                insert(RestaurantSettings).values(restaurant_id=restaurant_id)
            )

            with pytest.raises(IntegrityError) as error:
                with connection.begin_nested():
                    connection.execute(
                        update(RestaurantSettings)
                        .where(RestaurantSettings.restaurant_id == restaurant_id)
                        .values(slot_minutes=0)
                    )

            assert error.value.orig.sqlstate == "23514"
        finally:
            transaction.rollback()


def test_restaurant_and_settings_relationship_is_bidirectional():
    engine = get_engine()
    assert engine.url.host in ("localhost", "127.0.0.1")

    with Session(engine) as session:
        transaction = session.begin()
        try:
            restaurant = Restaurant(name="Prueba relación", timezone="Europe/Madrid")
            restaurant.settings = RestaurantSettings()
            session.add(restaurant)
            session.flush()

            assert restaurant.settings.restaurant_id == restaurant.id
            assert restaurant.settings.restaurant is restaurant
        finally:
            transaction.rollback()
