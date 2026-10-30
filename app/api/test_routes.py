from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.controllers.test_controller import check_health
from app.core.database_connection import get_db
from app.schemas.test_schema import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)):
    return check_health(db)