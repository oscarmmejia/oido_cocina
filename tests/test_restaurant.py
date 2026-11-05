"""Prueba de integración mínima para el modelo unificado.

Se ejecuta contra PostgreSQL LOCAL; transacción revertida al finalizar.
"""
import pytest
from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError

from app.core.database_connection import engine
from app.modules.settings.models.restaurant import Restaurant


def test_restaurant_stores_settings_and_validates_slot():
    assert engine.url.host in ("localhost", "127.0.0.1"), (
        "Esta prueba no debe ejecutarse sobre una base remota."
    )

    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            restaurant_id = connection.execute(
                insert(Restaurant)
                .values(name="Prueba DER", time_zone="Europe/Madrid")
                .returning(Restaurant.id)
            ).scalar_one()

            row = connection.execute(
                select(Restaurant.courtesy_minutes, Restaurant.slot_minutes)
                .where(Restaurant.id == restaurant_id)
            ).one()
            assert tuple(row) == (5, 60)

            connection.execute(
                update(Restaurant)
                .where(Restaurant.id == restaurant_id)
                .values(courtesy_minutes=10, slot_minutes=30)
            )
            row = connection.execute(
                select(Restaurant.courtesy_minutes, Restaurant.slot_minutes)
                .where(Restaurant.id == restaurant_id)
            ).one()
            assert tuple(row) == (10, 30)

            with pytest.raises(IntegrityError) as error:
                with connection.begin_nested():
                    connection.execute(
                        update(Restaurant)
                        .where(Restaurant.id == restaurant_id)
                        .values(slot_minutes=0)
                    )
            assert error.value.orig.sqlstate == "23514"
        finally:
            transaction.rollback()
