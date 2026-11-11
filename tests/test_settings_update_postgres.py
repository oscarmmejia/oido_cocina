"""Persistencia en PostgreSQL local con transacción exterior revertida."""

from sqlalchemy.orm import Session

from app.core.database_connection import engine
from app.modules.settings.models.restaurant import Restaurant
from app.modules.settings.schemas import RestaurantSettingsUpdate
from app.modules.settings.services.restaurant_service import update_restaurant_settings


def test_partial_update_persists_and_preserves_other_restaurants():
    assert engine.url.host in ("localhost", "127.0.0.1"), (
        "Esta prueba no debe ejecutarse sobre una base remota."
    )

    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            with Session(
                bind=connection, join_transaction_mode="create_savepoint"
            ) as db:
                restaurant = Restaurant(
                    name="Prueba OICO-44",
                    time_zone="Europe/Madrid",
                    period="comida",
                )
                other = Restaurant(name="Otro restaurante", time_zone="UTC")
                db.add_all([restaurant, other])
                db.flush()
                restaurant_id, other_id = restaurant.id, other.id

                update_restaurant_settings(
                    db,
                    restaurant_id,
                    RestaurantSettingsUpdate(slot_minutes=30, period=None),
                )
                db.expire_all()
                stored = db.get(Restaurant, restaurant_id)
                stored_other = db.get(Restaurant, other_id)

                assert stored.slot_minutes == 30
                assert stored.period is None
                assert stored.courtesy_minutes == 5
                assert stored.time_zone == "Europe/Madrid"
                assert stored.name == "Prueba OICO-44"
                assert stored_other.slot_minutes == 60
                assert stored_other.time_zone == "UTC"
        finally:
            transaction.rollback()
