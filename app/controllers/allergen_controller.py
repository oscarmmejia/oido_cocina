from sqlalchemy.orm import Session
from app.models.allergen_model import Allergen


def get_all_allergens(db: Session):
    return db.query(Allergen).order_by(Allergen.id).all()
