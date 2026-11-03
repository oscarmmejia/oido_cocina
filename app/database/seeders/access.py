from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.database.seeders._helpers import SeedError, insert_if_missing
from app.models import Role, User

# Roles of the briefing (section 3.1). `name` is the stable natural key.
ROLES = ["superadmin", "admin", "chef", "staff", "customer"]

# (role, email, belongs to the demo restaurant). Superadmin and customers are not tied to one restaurant.
DEMO_USERS = [
    ("superadmin", "demo-superadmin@example.com", False),
    ("admin", "demo-admin@example.com", True),
    ("chef", "demo-chef@example.com", True),
    ("staff", "demo-staff@example.com", True),
    ("customer", "demo-customer@example.com", False),
]


def seed_roles(session: Session) -> dict[str, int]:
    return {"roles": insert_if_missing(session, Role, [{"name": name} for name in ROLES], ["name"])}


def seed_demo_users(
    session: Session, restaurant_id: int, demo_password: str | None
) -> dict[str, int]:
    """Create one demo user per role. Existing users are never modified or re-hashed."""
    role_ids = dict(session.execute(select(Role.name, Role.id)).all())
    existing_emails = set(session.scalars(select(User.email)))
    missing = [user for user in DEMO_USERS if user[1] not in existing_emails]

    if missing and not demo_password:
        raise SeedError("SEED_DEMO_PASSWORD is not set: it is required to create the demo users.")

    rows = [
        {
            "role_id": role_ids[role],
            "restaurant_id": restaurant_id if in_restaurant else None,
            "email": email,
            "password_hash": hash_password(demo_password),
        }
        for role, email, in_restaurant in missing
    ]
    return {"users": insert_if_missing(session, User, rows, natural_key=["email"])}
