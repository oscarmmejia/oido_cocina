from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.category_model import Category
from app.models.dish_model import Dish
from app.schemas.category_schema import CategoryCreate, CategoryUpdate


def create_category(
    db: Session,
    category_data: CategoryCreate,
    restaurant_id: int
):
    try:
        # Comprobar que el nombre no existe en este restaurante
        existing_category = db.query(Category).filter(
            Category.restaurant_id == restaurant_id,
            Category.name == category_data.name
        ).first()

        if existing_category is not None:
            raise HTTPException(
                status_code=409,
                detail="Ya existe una categoría con ese nombre en este restaurante"
            )

        category = Category(
            restaurant_id=restaurant_id,
            name=category_data.name,
            sort_order=category_data.sort_order
        )

        db.add(category)
        db.flush()

        response = {
            "id": category.id,
            "restaurant_id": category.restaurant_id,
            "name": category.name,
            "sort_order": category.sort_order,
            "is_active": category.is_active
        }

        db.commit()
        return response

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ya existe una categoría con ese nombre en este restaurante"
        )

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="No se pudo crear la categoría"
        )


def get_category(
    db: Session,
    category_id: int,
    restaurant_id: int
):
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.restaurant_id == restaurant_id
    ).first()

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Categoría no encontrada"
        )

    return category


def get_categories(
    db: Session,
    restaurant_id: int
):
    return db.query(Category).filter(
        Category.restaurant_id == restaurant_id
    ).order_by(Category.sort_order, Category.id).all()


def update_category(
    db: Session,
    category_id: int,
    category_data: CategoryUpdate,
    restaurant_id: int
):
    try:
        category = db.query(Category).filter(
            Category.id == category_id,
            Category.restaurant_id == restaurant_id
        ).first()

        if category is None:
            raise HTTPException(
                status_code=404,
                detail="Categoría no encontrada"
            )

        changes = category_data.model_dump(exclude_unset=True)

        if not changes:
            raise HTTPException(
                status_code=422,
                detail="No se han enviado cambios"
            )

        if "name" in changes:
            existing_category = db.query(Category).filter(
                Category.restaurant_id == restaurant_id,
                Category.name == changes["name"],
                Category.id != category_id
            ).first()

            if existing_category is not None:
                raise HTTPException(
                    status_code=409,
                    detail="Ya existe una categoría con ese nombre en este restaurante"
                )

        for field, value in changes.items():
            setattr(category, field, value)

        response = {
            "id": category.id,
            "restaurant_id": category.restaurant_id,
            "name": category.name,
            "sort_order": category.sort_order,
            "is_active": category.is_active
        }

        db.commit()
        return response

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se pudo actualizar la categoría por un conflicto de datos"
        )

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="No se pudo actualizar la categoría"
        )


def deactivate_category(
    db: Session,
    category_id: int,
    restaurant_id: int
):
    try:
        category = db.query(Category).filter(
            Category.id == category_id,
            Category.restaurant_id == restaurant_id
        ).first()

        if category is None:
            raise HTTPException(
                status_code=404,
                detail="Categoría no encontrada"
            )

        active_dish = db.query(Dish).filter(
            Dish.category_id == category_id,
            Dish.restaurant_id == restaurant_id,
            Dish.is_active.is_(True)
        ).first()

        if active_dish is not None:
            raise HTTPException(
                status_code=409,
                detail="No se puede desactivar una categoría que tiene platos activos"
            )

        category.is_active = False
        db.commit()

        return {
            "message": "Categoría desactivada correctamente",
            "id": category.id
        }

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="No se pudo desactivar la categoría"
        )
