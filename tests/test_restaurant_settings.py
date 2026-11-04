import pytest
from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError

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
            connection.execute(
                insert(RestaurantSettings).values(**settings)
            )

            # Segunda configuración: debe rechazarse.
            with pytest.raises(IntegrityError) as error:
                with connection.begin_nested():
                    connection.execute(
                        insert(RestaurantSettings).values(**settings)
                    )

            assert error.value.orig.sqlstate == "23505"

        finally:
            # Deshacemos los datos de prueba.
            transaction.rollback()