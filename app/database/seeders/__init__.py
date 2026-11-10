from sqlalchemy.orm import Session
from app.database.seeders.catalog import seed_allergens


def seed_minimum(db: Session):
    return seed_allergens(db)


def seed_all(db: Session):
    return seed_minimum(db)
