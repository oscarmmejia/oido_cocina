from sqlalchemy.orm import Session
from app.models.allergen_model import Allergen


def get_all_allergens(db: Session):
    """Obtiene el listado completo del catálogo común de alérgenos."""
    return db.query(Allergen).all()