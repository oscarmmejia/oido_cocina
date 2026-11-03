from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session


class SeedError(RuntimeError):
    """Raised when a seeder cannot run (for example, a missing required secret)."""


def insert_if_missing(
    session: Session, model: type, rows: list[dict[str, Any]], natural_key: list[str]
) -> int:
    """Insert rows that do not exist yet, matching by natural key. Returns rows inserted.

    Relies on a unique constraint over `natural_key`, so it is safe to run repeatedly
    (and concurrently): existing rows are left untouched.
    """
    if not rows:
        return 0
    statement = insert(model).values(rows).on_conflict_do_nothing(index_elements=natural_key)
    # RETURNING yields only the rows actually inserted (cursor.rowcount is unreliable here).
    primary_key = list(model.__table__.primary_key.columns)
    return len(session.execute(statement.returning(*primary_key)).all())
