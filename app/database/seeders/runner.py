from sqlalchemy.orm import Session

from app.database.seeders.access import seed_demo_users, seed_roles
from app.database.seeders.dishes import seed_allergens, seed_categories
from app.database.seeders.restaurant import seed_demo_restaurant


def run_all(session: Session, demo_password: str | None = None) -> dict[str, int]:
    """Run every seeder in dependency order. Idempotent: returns rows inserted per table.

    The caller owns the transaction (commit or rollback).
    """
    restaurant_id, inserted = seed_demo_restaurant(session)
    inserted |= seed_roles(session)
    inserted |= seed_demo_users(session, restaurant_id, demo_password)
    inserted |= seed_allergens(session)
    inserted |= seed_categories(session, restaurant_id)
    return inserted
