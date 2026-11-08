from sqlalchemy.orm import Session

from app.core.kernel.identity import DEV_RESTAURANT_ID, DEV_USER_ID  # noqa: F401
from app.database.seeders import seed_minimum


def seed_minimum_data(db: Session) -> None:
    seed_minimum(db)
