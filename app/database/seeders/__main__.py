"""Run all seeders: python -m app.database.seeders (after `alembic upgrade head`)."""

import sys

from app.core.config import get_settings
from app.core.database_connection import get_session_factory
from app.database.seeders._helpers import SeedError
from app.database.seeders.runner import run_all


def main() -> int:
    password = get_settings().seed_demo_password
    try:
        with get_session_factory()() as session, session.begin():
            inserted = run_all(session, password.get_secret_value() if password else None)
    except SeedError as error:
        print(f"Seeding aborted, nothing was saved: {error}", file=sys.stderr)
        return 1

    for table, count in inserted.items():
        print(f"{table}: {count} inserted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
