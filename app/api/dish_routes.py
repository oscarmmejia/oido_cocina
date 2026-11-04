from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.controllers.dish_controller import (
    create_dish,
    get_dish,
    get_dishes,
    update_dish,
)
from app.core.database_connection import get_db
from app.schemas.dish_schema import (
    DishCreate,
    DishResponse,
    DishUpdate,
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
