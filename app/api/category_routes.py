from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.controllers.category_controller import (
    create_category,
    get_category,
    get_categories,
    update_category,
    deactivate_category
)
from app.core.database_connection import get_db
from app.schemas.category_schema import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse
)

router = APIRouter(
    prefix="/categories",
    tags=["categories"]
)


@router.post("/", response_model=CategoryResponse, status_code=201)
def create_category_route(
    category_data: CategoryCreate,
    restaurant_id: int,
    db: Session = Depends(get_db)
):
    return create_category(db, category_data, restaurant_id)


@router.get("/", response_model=list[CategoryResponse])
def get_categories_route(
    restaurant_id: int,
    db: Session = Depends(get_db)
):
    return get_categories(db, restaurant_id)


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category_route(
    category_id: int,
    restaurant_id: int,
    db: Session = Depends(get_db)
):
    return get_category(db, category_id, restaurant_id)


@router.patch("/{category_id}", response_model=CategoryResponse)
def update_category_route(
    category_id: int,
    category_data: CategoryUpdate,
    restaurant_id: int,
    db: Session = Depends(get_db)
):
    return update_category(db, category_id, category_data, restaurant_id)


@router.patch("/{category_id}/deactivate")
def deactivate_category_route(
    category_id: int,
    restaurant_id: int,
    db: Session = Depends(get_db)
):
    return deactivate_category(db, category_id, restaurant_id)
