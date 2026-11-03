import pytest
from pydantic import ValidationError
from sqlalchemy import inspect

from app.core.config import get_settings
from app.core.database_connection import get_engine, get_session_factory


@pytest.fixture
def session():
    """A session on the configured database, rolled back after each test (data is left as found).

    Skipped only when no database is configured at all. If one is configured but not migrated,
    the test fails loudly: a silent skip would give a false green.
    """
    try:
        get_settings()
    except ValidationError:
        pytest.skip("DATABASE_URL is not configured.")

    if not inspect(get_engine()).has_table("roles"):
        pytest.fail("The database is not migrated. Run `alembic upgrade head` first.")

    with get_session_factory()() as session:
        yield session
        session.rollback()
