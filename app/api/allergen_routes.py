from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database_connection import get_db
from app.controllers.allergen_controller import get_all_allergens
from app.schemas.allergen_schema import AllergenResponse

router = APIRouter(prefix="/allergens", tags=["Alérgenos"])


@router.get(
    "/",
    response_model=List[AllergenResponse],
    summary="Obtener catálogo oficial de alérgenos",
    description="Devuelve el catálogo público y común de los 14 alérgenos de obligada declaración en la Unión Europea. No requiere autenticación."
)
def list_allergens(db: Session = Depends(get_db)):
    """
    Endpoint público para consultar todos los alérgenos registrados en el sistema.
    """
    return get_all_allergens(db)