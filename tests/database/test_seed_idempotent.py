from sqlalchemy import func, select

from app.core.database_connection import Base
from app.core.permissions import PERMISSIONS
from app.database.seeders import seed_all
from app.models import Allergen, Permission, Restaurant, Role, User


def _counts(db) -> dict[str, int]:
    return {
        table.name: db.scalar(select(func.count()).select_from(table))
        for table in Base.metadata.sorted_tables
    }


def test_seed_all_twice_keeps_row_counts(db) -> None:
    seed_all(db)
    db.commit()
    first = _counts(db)

    seed_all(db)
    db.commit()
    second = _counts(db)

    assert first == second


def test_api_starts_after_seeding(client, db) -> None:
    seed_all(db)
    db.commit()

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"app": "ok", "database": "ok"}


def test_seed_loads_required_catalogs(db) -> None:
    seed_all(db)
    db.commit()

    assert db.scalar(select(func.count()).select_from(Allergen)) == 14
    assert db.scalar(select(func.count()).select_from(Permission)) == len(
        PERMISSIONS
    )
    assert db.scalar(select(func.count()).select_from(Role)) == 5
    assert db.scalar(select(func.count()).select_from(User)) == 5

    restaurant = db.scalar(select(Restaurant))
    assert restaurant is not None
    assert restaurant.day_of_week == 1
    assert restaurant.period == "morning"
    assert restaurant.open_time is not None
    assert restaurant.close_time is not None
    assert restaurant.kitchen_close_time is not None

    roles = db.scalars(select(Role)).all()
    for role in roles:
        users = db.scalar(
            select(func.count())
            .select_from(User)
            .where(User.role_id == role.id)
        )
        assert users >= 1
