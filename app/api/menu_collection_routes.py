from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.controllers.menu_collection_controller import (
    create_menu_collection,
    delete_menu_collection,
    get_menu_collection,
    get_menu_collections,
    get_public_menu_collections,
    update_menu_collection,
    update_menu_collection_status,
)
from app.core.database_connection import get_db
from app.core.kernel.permissions import require_permission
from app.schemas.menu_collection_schema import (
    MenuCollectionCreate,
    MenuCollectionPublicResponse,
    MenuCollectionResponse,
    MenuCollectionStatusUpdate,
    MenuCollectionUpdate,
)

router = APIRouter(
    prefix="/menu-collections",
    tags=["menu-collections"]
)


@router.post("/", response_model=MenuCollectionResponse, status_code=201)
def create_menu_collection_route(
    collection_data: MenuCollectionCreate,
    restaurant_id: int,
    _=Depends(require_permission("menu:create")),
    db: Session = Depends(get_db)
):
    return create_menu_collection(db, collection_data, restaurant_id)


@router.get("/public", response_model=list[MenuCollectionPublicResponse])
def get_public_menu_collections_route(
    restaurant_id: int,
    db: Session = Depends(get_db)
):
    return get_public_menu_collections(db, restaurant_id)


@router.get("/", response_model=list[MenuCollectionResponse])
def get_menu_collections_route(
    restaurant_id: int,
    db: Session = Depends(get_db)
):
    return get_menu_collections(db, restaurant_id)


@router.get("/{collection_id}", response_model=MenuCollectionResponse)
def get_menu_collection_route(
    collection_id: int,
    restaurant_id: int,
    db: Session = Depends(get_db)
):
    return get_menu_collection(db, collection_id, restaurant_id)


@router.patch("/{collection_id}", response_model=MenuCollectionResponse)
def update_menu_collection_route(
    collection_id: int,
    collection_data: MenuCollectionUpdate,
    restaurant_id: int,
    _=Depends(require_permission("menu:update")),
    db: Session = Depends(get_db)
):
    return update_menu_collection(db, collection_id, collection_data, restaurant_id)


@router.patch("/{collection_id}/status", response_model=MenuCollectionResponse)
def update_menu_collection_status_route(
    collection_id: int,
    status_data: MenuCollectionStatusUpdate,
    restaurant_id: int,
    _=Depends(require_permission("menu:update")),
    db: Session = Depends(get_db)
):
    return update_menu_collection_status(db, collection_id, status_data, restaurant_id)


@router.delete("/{collection_id}", status_code=204)
def delete_menu_collection_route(
    collection_id: int,
    restaurant_id: int,
    _=Depends(require_permission("menu:update")),
    db: Session = Depends(get_db)
):
    delete_menu_collection(db, collection_id, restaurant_id)