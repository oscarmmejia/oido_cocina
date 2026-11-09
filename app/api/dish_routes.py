from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.controllers.dish_controller import (
    create_dish,
    deactivate_dish,
    get_dish,
    get_dishes,
    get_public_dish,
    get_public_dishes,
    update_dish,
    update_dish_status,
)
from app.core.database_connection import get_db
from app.core.kernel.permissions import require_permission
from app.schemas.dish_schema import (
    DishCreate,
    DishPublicResponse,
    DishResponse,
    DishStatusUpdate,
    DishUpdate,
    PaginatedDishesResponse,
)

router = APIRouter(
    prefix="/dishes",
    tags=["dishes"]
)


@router.post("/", response_model=DishResponse, status_code=201)
def create_dish_route(
    dish_data: DishCreate,
    restaurant_id: int,
    db: Session = Depends(get_db)
):
    return create_dish(db, dish_data, restaurant_id)


@router.get("/public", response_model=PaginatedDishesResponse)
def get_public_dishes_route(
    restaurant_id: int,
    category_id: int | None = None,
    is_available: bool | None = None,
    allergen_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return get_public_dishes(db, restaurant_id, category_id, is_available, allergen_id, page, page_size)


@router.get("/public/{dish_id}", response_model=DishPublicResponse)
def get_public_dish_route(
    dish_id: int,
    restaurant_id: int,
    db: Session = Depends(get_db)
):
    return get_public_dish(db, dish_id, restaurant_id)


@router.get("/", response_model=list[DishResponse])
def get_dishes_route(
    restaurant_id: int,
    db: Session = Depends(get_db)
):
    return get_dishes(db, restaurant_id)


@router.get("/{dish_id}", response_model=DishResponse)
def get_dish_route(
    dish_id: int,
    restaurant_id: int,
    db: Session = Depends(get_db)
):
    return get_dish(db, dish_id, restaurant_id)


@router.patch("/{dish_id}", response_model=DishResponse)
def update_dish_route(
    dish_id: int,
    dish_data: DishUpdate,
    restaurant_id: int,
    db: Session = Depends(get_db)
):
    return update_dish(db, dish_id, dish_data, restaurant_id)


@router.patch("/{dish_id}/deactivate")
def deactivate_dish_route(
    dish_id: int,
    restaurant_id: int,
    _=Depends(require_permission("dish:deactivate")),
    db: Session = Depends(get_db)
):
    return deactivate_dish(db, dish_id, restaurant_id)




@router.patch("/{dish_id}/status", response_model=DishResponse)
def update_dish_status_route(
    dish_id: int,
    status_data: DishStatusUpdate,
    restaurant_id: int,
    _=Depends(require_permission("dish:deactivate")),
    db: Session = Depends(get_db)
):
    return update_dish_status(db, dish_id, status_data, restaurant_id)

