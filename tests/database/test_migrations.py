from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from app.core.database_connection import Base, engine

EXPECTED_TABLES = {
    "allergens",
    "audit_logs",
    "categories",
    "dish_allergens",
    "dishes",
    "employees",
    "menu_collections",
    "menu_dishes",
    "menus",
    "opening_hours",
    "permissions",
    "price_history",
    "reservation_status_history",
    "reservation_tables",
    "reservations",
    "restaurant",
    "role_permissions",
    "roles",
    "schedules",
    "shift_swap_requests",
    "table_combination_tables",
    "table_combinations",
    "tables",
    "time_off_requests",
    "users",
    "work_shifts",
}


def _reset_schema() -> None:
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist"))


def _restore_schema() -> None:
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist"))
    Base.metadata.create_all(bind=engine)


def test_migrations_upgrade_from_empty_and_downgrade_to_empty() -> None:
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    _reset_schema()
    try:
        command.upgrade(config, "head")

        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        assert EXPECTED_TABLES <= tables
        assert tables - EXPECTED_TABLES == {"alembic_version"}

        with engine.connect() as connection:
            constraints = {
                row[0]
                for row in connection.execute(
                    text(
                        "SELECT conname FROM pg_constraint "
                        "WHERE conname IN ("
                        "'ex_reservation_tables_no_overlap',"
                        "'ex_work_shifts_no_overlap'"
                        ")"
                    )
                )
            }
            indexes = {
                row[0]
                for row in connection.execute(
                    text(
                        "SELECT indexname FROM pg_indexes "
                        "WHERE indexname = "
                        "'uq_reservations_active_contact_date'"
                    )
                )
            }
        assert constraints == {
            "ex_reservation_tables_no_overlap",
            "ex_work_shifts_no_overlap",
        }
        assert indexes == {"uq_reservations_active_contact_date"}

        command.downgrade(config, "base")
        remaining = set(inspect(engine).get_table_names())
        assert remaining <= {"alembic_version"}
    finally:
        _restore_schema()
