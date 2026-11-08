"""Alembic history contract: one configured, linear chain with both directions.

The textual SQL checks use Alembic offline mode, so they never open a database
connection. They only need `DATABASE_URL` to exist because `env.py` reads it
through the application settings.
"""

from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect

from app.core.config import get_settings
from app.core.database_connection import get_engine
from app.database.base import Base

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPO_ROOT / "app" / "database" / "migrations"

EXPECTED_TABLES = {
    "allergens",
    "audit_logs",
    "categories",
    "opening_hours",
    "permissions",
    "restaurant_settings",
    "restaurants",
    "role_permissions",
    "roles",
    "users",
}


def make_config() -> Config:
    config = Config(str(REPO_ROOT / "alembic.ini"))
    # Absolute path: the test does not depend on the current working directory.
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    return config


def test_alembic_points_to_the_canonical_history():
    config = Config(str(REPO_ROOT / "alembic.ini"))

    assert config.get_main_option("script_location") == "app/database/migrations"


def test_history_has_a_single_linear_head():
    script = ScriptDirectory.from_config(make_config())
    revisions = list(script.walk_revisions())

    assert len(script.get_heads()) == 1
    assert revisions[-1].revision == "0001"
    assert revisions[-1].down_revision is None

    for revision in revisions:
        assert revision.down_revision is None or isinstance(revision.down_revision, str)


def test_offline_upgrade_creates_every_table(capsys):
    try:
        get_settings()
    except SystemExit:
        pytest.skip("DATABASE_URL is not configured.")

    command.upgrade(make_config(), "head", sql=True)
    rendered = capsys.readouterr().out

    for table in EXPECTED_TABLES:
        assert f"CREATE TABLE {table}" in rendered


def test_offline_downgrade_drops_every_table(capsys):
    try:
        get_settings()
    except SystemExit:
        pytest.skip("DATABASE_URL is not configured.")

    command.downgrade(make_config(), "head:base", sql=True)
    rendered = capsys.readouterr().out

    for table in EXPECTED_TABLES:
        assert f"DROP TABLE {table}" in rendered


def test_live_database_matches_the_models():
    """Equivalent to `alembic check`, as a test (read-only)."""
    try:
        get_settings()
    except SystemExit:
        pytest.skip("DATABASE_URL is not configured.")

    engine = get_engine()
    if not inspect(engine).has_table("alembic_version"):
        pytest.fail("The database is not migrated. Run `alembic upgrade head` first.")

    with engine.connect() as connection:
        context = MigrationContext.configure(connection, opts={"compare_type": True})
        differences = compare_metadata(context, Base.metadata)

    assert differences == []
