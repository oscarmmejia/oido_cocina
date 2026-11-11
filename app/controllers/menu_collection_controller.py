from datetime import date

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.menu_model import Menu, MenuCollection
from app.schemas.menu_collection_schema import (
    MenuCollectionCreate,
    MenuCollectionStatusUpdate,
    MenuCollectionUpdate,
    check_validity_range,
)


def create_menu_collection(
    db: Session,
    collection_data: MenuCollectionCreate,
    restaurant_id: int
):
    try:
        existing_collection = db.query(MenuCollection).filter(
            MenuCollection.restaurant_id == restaurant_id,
            MenuCollection.name == collection_data.name
        ).first()

        if existing_collection is not None:
            raise HTTPException(
                status_code=409,
                detail="Ya existe una colección con ese nombre en este restaurante"
            )

        collection = MenuCollection(
            restaurant_id=restaurant_id,
            name=collection_data.name,
            type=collection_data.type,
            valid_from=collection_data.valid_from,
            valid_to=collection_data.valid_to
        )

        db.add(collection)
        db.commit()

        return collection

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ya existe una colección con ese nombre en este restaurante"
        )

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="No se pudo crear la colección"
        )


def get_menu_collection(
    db: Session,
    collection_id: int,
    restaurant_id: int
):
    collection = db.query(MenuCollection).filter(
        MenuCollection.id == collection_id,
        MenuCollection.restaurant_id == restaurant_id
    ).first()

    if collection is None:
        raise HTTPException(
            status_code=404,
            detail="Colección no encontrada"
        )

    return collection


def get_menu_collections(
    db: Session,
    restaurant_id: int
):
    return db.query(MenuCollection).filter(
        MenuCollection.restaurant_id == restaurant_id
    ).order_by(MenuCollection.id).all()


def update_menu_collection(
    db: Session,
    collection_id: int,
    collection_data: MenuCollectionUpdate,
    restaurant_id: int
):
    try:
        collection = db.query(MenuCollection).filter(
            MenuCollection.id == collection_id,
            MenuCollection.restaurant_id == restaurant_id
        ).first()

        if collection is None:
            raise HTTPException(
                status_code=404,
                detail="Colección no encontrada"
            )

        changes = collection_data.model_dump(exclude_unset=True)

        if not changes:
            raise HTTPException(
                status_code=422,
                detail="No se han enviado cambios"
            )

        if "name" in changes:
            existing_collection = db.query(MenuCollection).filter(
                MenuCollection.restaurant_id == restaurant_id,
                MenuCollection.name == changes["name"],
                MenuCollection.id != collection_id
            ).first()

            if existing_collection is not None:
                raise HTTPException(
                    status_code=409,
                    detail="Ya existe una colección con ese nombre en este restaurante"
                )

        merged_valid_from = changes.get("valid_from", collection.valid_from)
        merged_valid_to = changes.get("valid_to", collection.valid_to)

        try:
            check_validity_range(merged_valid_from, merged_valid_to)
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail=str(exc)
            )

        for field, value in changes.items():
            setattr(collection, field, value)

        db.commit()

        return collection

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ya existe una colección con ese nombre en este restaurante"
        )

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="No se pudo actualizar la colección"
        )


def update_menu_collection_status(
    db: Session,
    collection_id: int,
    status_data: MenuCollectionStatusUpdate,
    restaurant_id: int
):
    try:
        collection = db.query(MenuCollection).filter(
            MenuCollection.id == collection_id,
            MenuCollection.restaurant_id == restaurant_id
        ).first()

        if collection is None:
            raise HTTPException(
                status_code=404,
                detail="Colección no encontrada"
            )

        changes = status_data.model_dump(exclude_unset=True)

        if not changes:
            raise HTTPException(
                status_code=422,
                detail="Debe indicar al menos un estado"
            )

        for field, value in changes.items():
            setattr(collection, field, value)

        db.commit()

        return collection

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="No se pudo actualizar el estado de la colección"
        )


def delete_menu_collection(
    db: Session,
    collection_id: int,
    restaurant_id: int
):
    try:
        collection = db.query(MenuCollection).filter(
            MenuCollection.id == collection_id,
            MenuCollection.restaurant_id == restaurant_id
        ).first()

        if collection is None:
            raise HTTPException(
                status_code=404,
                detail="Colección no encontrada"
            )

        collection_with_menus = db.query(Menu.id).filter(
            Menu.collection_id == collection.id
        ).first()

        if collection_with_menus is not None:
            raise HTTPException(
                status_code=409,
                detail="No se puede borrar una colección con menús; desactívela en su lugar"
            )

        db.delete(collection)
        db.commit()

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="No se pudo borrar la colección"
        )


def get_public_menu_collections(
    db: Session,
    restaurant_id: int
):
    today = date.today()

    collections = db.query(MenuCollection).filter(
        MenuCollection.restaurant_id == restaurant_id,
        MenuCollection.is_active.is_(True),
        or_(
            MenuCollection.valid_from.is_(None),
            MenuCollection.valid_from <= today
        ),
        or_(
            MenuCollection.valid_to.is_(None),
            MenuCollection.valid_to >= today
        )
    ).order_by(MenuCollection.id).all()

    results = []

    for collection in collections:
        menus = db.query(Menu).filter(
            Menu.collection_id == collection.id
        ).order_by(Menu.id).all()

        results.append({
            "id": collection.id,
            "name": collection.name,
            "type": collection.type,
            "valid_from": collection.valid_from,
            "valid_to": collection.valid_to,
            "menus": [{
                "id": menu.id,
                "name": menu.name,
                "own_price": menu.own_price,
                "is_active": menu.is_active,
                "is_available": menu.is_available
            } for menu in menus]
        })

    return results