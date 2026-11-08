"""DB-level contract of the `Restaurant` model.

A restaurant only stores its identity. Configuration and opening hours live in
`restaurant_settings` / `opening_hours`, so this test also guards against the
columns of the discarded unified DER model leaking back into `restaurants`.

It runs against the local PostgreSQL database; the transaction is rolled back.
"""

from sqlalchemy import insert, select

from app.core.database_connection import get_engine
from app.modules.settings.models.restaurant import Restaurant

IDENTITY_COLUMNS = {"id", "name", "timezone", "is_active", "created_at", "updated_at"}

# Columns of the discarded unified REST model: they belong to other tables now.
SETTINGS_AND_SCHEDULE_COLUMNS = {
    "courtesy_minutes",
    "curtesy_minutes",
    "slot_minutes",
    "default_reservation_minutes",
    "min_break_between_shifts",
    "day_of_week",
    "period",
    "open_time",
    "close_time",
    "kitchen_close_time",
    "direction",
}


def test_restaurant_maps_only_identity_columns():
    columns = set(Restaurant.__table__.columns.keys())

    assert columns == IDENTITY_COLUMNS
    assert SETTINGS_AND_SCHEDULE_COLUMNS.isdisjoint(columns)


def test_restaurant_stores_identity_and_applies_database_defaults():
    engine = get_engine()
    assert engine.url.host in ("localhost", "127.0.0.1"), (
        "Esta prueba no debe ejecutarse sobre una base remota."
    )

    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            restaurant_id = connection.execute(
                insert(Restaurant)
                .values(name="Prueba modelo", timezone="Europe/Madrid")
                .returning(Restaurant.id)
            ).scalar_one()

            row = connection.execute(
                select(
                    Restaurant.name,
                    Restaurant.timezone,
                    Restaurant.is_active,
                    Restaurant.created_at,
                    Restaurant.updated_at,
                ).where(Restaurant.id == restaurant_id)
            ).one()

            assert row.name == "Prueba modelo"
            assert row.timezone == "Europe/Madrid"
            assert row.is_active is True
            assert row.created_at is not None
            assert row.updated_at is not None
        finally:
            transaction.rollback()
