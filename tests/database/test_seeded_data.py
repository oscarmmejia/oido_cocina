"""What the seeders must leave in the database (briefing roles, EU allergens, categories)."""

import pytest
from sqlalchemy import select, text

from app.database.seeders._helpers import SeedError
from app.database.seeders.access import ROLES
from app.database.seeders.dishes import ALLERGENS, CATEGORIES
from app.database.seeders.runner import run_all
from app.models import Allergen, Category, Role, User

DEMO_PASSWORD = "test-only-password"


def test_the_fourteen_eu_allergens_are_loaded(session):
    run_all(session, DEMO_PASSWORD)

    codes = set(session.scalars(select(Allergen.code)))
    assert codes == {code for code, _ in ALLERGENS}
    assert len(codes) == 14


def test_initial_categories_are_loaded(session):
    run_all(session, DEMO_PASSWORD)

    assert set(CATEGORIES) <= set(session.scalars(select(Category.name)))


def test_every_role_of_the_briefing_has_at_least_one_user(session):
    run_all(session, DEMO_PASSWORD)

    assert set(session.scalars(select(Role.name))) >= set(ROLES)
    roles_without_users = session.scalars(
        select(Role.name).outerjoin(User, User.role_id == Role.id).where(User.id.is_(None))
    ).all()
    assert roles_without_users == []


def test_demo_user_passwords_are_stored_hashed(session):
    run_all(session, DEMO_PASSWORD)

    hashes = session.scalars(select(User.password_hash).where(User.email.like("demo-%"))).all()
    assert hashes
    assert all(h.startswith("$argon2id$") and DEMO_PASSWORD not in h for h in hashes)


def test_missing_password_aborts_when_users_must_be_created(session):
    session.execute(text("TRUNCATE users CASCADE"))

    with pytest.raises(SeedError):
        run_all(session, demo_password=None)
