"""Running the seeders twice must leave exactly the same state as running them once."""

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.database.seeders.runner import run_all
from app.models import (
    Allergen,
    Category,
    OpeningHours,
    Restaurant,
    RestaurantSettings,
    Role,
    User,
)

# Every table the seeders write to.
SEEDED_MODELS = [Restaurant, RestaurantSettings, OpeningHours, Role, User, Allergen, Category]


def count_rows(session: Session) -> dict[str, int]:
    return {
        model.__tablename__: session.scalar(select(func.count()).select_from(model))
        for model in SEEDED_MODELS
    }


def snapshot(session: Session) -> dict[str, list]:
    """Full content of the seeded tables: catches duplicates and also modified rows."""
    state = {}
    for model in SEEDED_MODELS:
        order = list(model.__table__.primary_key.columns)
        rows = session.execute(select(model.__table__).order_by(*order)).all()
        state[model.__tablename__] = [tuple(row) for row in rows]
    return state


def empty_seeded_tables(session: Session) -> None:
    # TRUNCATE is transactional in PostgreSQL: the fixture's rollback restores everything.
    # CASCADE also covers tables added later that reference these ones.
    session.execute(text("TRUNCATE restaurants, roles, allergens CASCADE"))


def test_second_run_keeps_the_same_row_counts_from_an_empty_database(session):
    empty_seeded_tables(session)
    assert set(count_rows(session).values()) == {0}

    run_all(session, "demo-password")
    counts_after_first_run = count_rows(session)
    assert all(count > 0 for count in counts_after_first_run.values())

    inserted_by_second_run = run_all(session, "demo-password")

    assert count_rows(session) == counts_after_first_run
    assert inserted_by_second_run == {table: 0 for table in inserted_by_second_run}


def test_second_run_keeps_the_same_row_counts_on_an_already_seeded_database(session):
    run_all(session, "demo-password")
    counts_before = count_rows(session)

    run_all(session, "demo-password")

    assert count_rows(session) == counts_before


def test_second_run_does_not_modify_existing_rows(session):
    empty_seeded_tables(session)
    run_all(session, "first-password")
    state_after_first_run = snapshot(session)

    # A different password on the second run must not re-hash or touch existing users.
    run_all(session, "other-password")

    assert snapshot(session) == state_after_first_run
