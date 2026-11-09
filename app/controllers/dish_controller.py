import math

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.allergen_model import Allergen
from app.models.category_model import Category
from app.models.dish_allergen_model import DishAllergen
from app.models.dish_model import Dish
from app.schemas.dish_schema import DishCreate, DishStatusUpdate, DishUpdate

def create_dish(
    db: Session,
    dish_data: DishCreate,
    restaurant_id: int
):
    try:
        if len(dish_data.allergen_ids) != len(set(dish_data.allergen_ids)):
            raise HTTPException(
                status_code=422,
                detail="No se permiten alérgenos duplicados"
            )

        category = db.query(Category).filter(
            Category.id == dish_data.category_id,
            Category.restaurant_id == restaurant_id
        ).first()

        if category is None:
            raise HTTPException(
                status_code=422,
                detail="La categoría no existe para este restaurante"
            )

        for allergen_id in dish_data.allergen_ids:
            allergen = db.query(Allergen).filter(
                Allergen.id == allergen_id
            ).first()

            if allergen is None:
                raise HTTPException(
                    status_code=422,
                    detail=f"El alérgeno {allergen_id} no existe"
                )

        dish = Dish(
            restaurant_id=restaurant_id,
            category_id=dish_data.category_id,
            name=dish_data.name,
            description=dish_data.description,
            price=dish_data.price
        )

        db.add(dish)
        db.flush()

        for allergen_id in dish_data.allergen_ids:
            db.add(
                DishAllergen(
                    dish_id=dish.id,
                    allergen_id=allergen_id
                )
            )

        response = {
            "id": dish.id,
            "restaurant_id": dish.restaurant_id,
            "category_id": dish.category_id,
            "name": dish.name,
            "description": dish.description,
            "price": dish.price,
            "is_active": dish.is_active,
            "is_published": dish.is_published,
            "is_available": dish.is_available,
            "allergen_ids": dish_data.allergen_ids
        }

        db.commit()

        return response

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="No se pudo guardar el plato"
        )


def get_dish(
    db: Session,
    dish_id: int,
    restaurant_id: int
):
    dish = db.query(Dish).filter(
        Dish.id == dish_id,
        Dish.restaurant_id == restaurant_id
    ).first()

    if dish is None:
        raise HTTPException(
            status_code=404,
            detail="Plato no encontrado"
        )

    allergen_ids = db.query(
        DishAllergen.allergen_id
    ).filter(
        DishAllergen.dish_id == dish.id
    ).all()

    return {
        "id": dish.id,
        "restaurant_id": dish.restaurant_id,
        "category_id": dish.category_id,
        "name": dish.name,
        "description": dish.description,
        "price": dish.price,
        "is_active": dish.is_active,
        "is_published": dish.is_published,
        "is_available": dish.is_available,
        "allergen_ids": [row[0] for row in allergen_ids]
    }


def get_dishes(
    db: Session,
    restaurant_id: int
):
    dishes = db.query(Dish).filter(
        Dish.restaurant_id == restaurant_id
    ).order_by(Dish.id).all()

    results = []

    for dish in dishes:
        allergen_ids = db.query(
            DishAllergen.allergen_id
        ).filter(
            DishAllergen.dish_id == dish.id
        ).all()

        results.append({
            "id": dish.id,
            "restaurant_id": dish.restaurant_id,
            "category_id": dish.category_id,
            "name": dish.name,
            "description": dish.description,
            "price": dish.price,
            "is_active": dish.is_active,
            "is_published": dish.is_published,
            "is_available": dish.is_available,
            "allergen_ids": [row[0] for row in allergen_ids]
        })

    return results


def update_dish(
    db: Session,
    dish_id: int,
    dish_data: DishUpdate,
    restaurant_id: int
):
    try:
        dish = db.query(Dish).filter(
            Dish.id == dish_id,
            Dish.restaurant_id == restaurant_id
        ).first()

        if dish is None:
            raise HTTPException(
                status_code=404,
                detail="Plato no encontrado"
            )

        changes = dish_data.model_dump(exclude_unset=True)

        if "category_id" in changes:
            category = db.query(Category).filter(
                Category.id == changes["category_id"],
                Category.restaurant_id == restaurant_id
            ).first()

            if category is None:
                raise HTTPException(
                    status_code=422,
                    detail="La categoría no existe para este restaurante"
                )

        if "allergen_ids" in changes:
            allergen_ids = changes.pop("allergen_ids")

            if len(allergen_ids) != len(set(allergen_ids)):
                raise HTTPException(
                    status_code=422,
                    detail="No se permiten alérgenos duplicados"
                )

            for allergen_id in allergen_ids:
                allergen = db.query(Allergen).filter(
                    Allergen.id == allergen_id
                ).first()

                if allergen is None:
                    raise HTTPException(
                        status_code=422,
                        detail=f"El alérgeno {allergen_id} no existe"
                    )

            db.query(DishAllergen).filter(
                DishAllergen.dish_id == dish.id
            ).delete(synchronize_session=False)

            for allergen_id in allergen_ids:
                db.add(
                    DishAllergen(
                        dish_id=dish.id,
                        allergen_id=allergen_id
                    )
                )

        for field, value in changes.items():
            setattr(dish, field, value)

        if "allergen_ids" in dish_data.model_fields_set:
            response_allergen_ids = dish_data.allergen_ids
        else:
            allergen_rows = db.query(
                DishAllergen.allergen_id
            ).filter(
                DishAllergen.dish_id == dish.id
            ).all()

            response_allergen_ids = [
                row[0] for row in allergen_rows
            ]

        response = {
            "id": dish.id,
            "restaurant_id": dish.restaurant_id,
            "category_id": dish.category_id,
            "name": dish.name,
            "description": dish.description,
            "price": dish.price,
            "is_active": dish.is_active,
            "is_published": dish.is_published,
            "is_available": dish.is_available,
            "allergen_ids": response_allergen_ids
        }

        db.commit()

        return response

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="No se pudo actualizar el plato"
        )


def deactivate_dish(
    db: Session,
    dish_id: int,
    restaurant_id: int
):
    try:
        dish = db.query(Dish).filter(
            Dish.id == dish_id,
            Dish.restaurant_id == restaurant_id
        ).first()

        if dish is None:
            raise HTTPException(
                status_code=404,
                detail="Plato no encontrado"
            )

        if not dish.is_active:
            raise HTTPException(
                status_code=409,
                detail="El plato ya está desactivado"
            )

        dish.is_active = False
        db.commit()

        return {"message": "Plato desactivado correctamente", "id": dish.id}

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="No se pudo desactivar el plato"
        )
        
def update_dish_status(
    db: Session,
    dish_id: int,
    status_data: DishStatusUpdate,
    restaurant_id: int
):
    try:
        dish = db.query(Dish).filter(
            Dish.id == dish_id,
            Dish.restaurant_id == restaurant_id
        ).first()

        if dish is None:
            raise HTTPException(
                status_code=404,
                detail="Plato no encontrado"
            )

        changes = status_data.model_dump(exclude_unset=True)

        if not changes:
            raise HTTPException(
                status_code=422,
                detail="Debe indicar al menos un estado"
            )

        for field, value in changes.items():
            setattr(dish, field, value)

        db.commit()

        return get_dish(db, dish.id, restaurant_id)

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="No se pudo actualizar el estado del plato"
        )       


def get_public_dishes(
    db: Session,
    restaurant_id: int,
    category_id: int | None = None,
    is_available: bool | None = None,
    allergen_id: int | None = None,
    page: int = 1,
    page_size: int = 20
):
    query = db.query(Dish).filter(
        Dish.restaurant_id == restaurant_id,
        Dish.is_active.is_(True),
        Dish.is_published.is_(True)
    )

    if category_id is not None:
        query = query.filter(Dish.category_id == category_id)

    if is_available is not None:
        query = query.filter(Dish.is_available == is_available)

    if allergen_id is not None:
        dishIdsWithAllergen = select(DishAllergen.dish_id).where(
            DishAllergen.allergen_id == allergen_id
        )
        
        query = query.filter(Dish.id.in_(dishIdsWithAllergen))
    total = query.count()
    dishes = query.order_by(Dish.id).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for dish in dishes:
        allergen_ids = [
            row[0] for row in db.query(DishAllergen.allergen_id).filter(
                DishAllergen.dish_id == dish.id
            ).all()
        ]
        items.append({
            "id": dish.id,
            "name": dish.name,
            "description": dish.description,
            "price": dish.price,
            "category_id": dish.category_id,
            "is_available": dish.is_available,
            "allergen_ids": allergen_ids
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if total > 0 else 0
    }


def get_public_dish(
    db: Session,
    dish_id: int,
    restaurant_id: int
):
    dish = db.query(Dish).filter(
        Dish.id == dish_id,
        Dish.restaurant_id == restaurant_id,
        Dish.is_active.is_(True),
        Dish.is_published.is_(True)
    ).first()

    if dish is None:
        raise HTTPException(
            status_code=404,
            detail="Plato no encontrado"
        )

    allergen_ids = [
        row[0] for row in db.query(DishAllergen.allergen_id).filter(
            DishAllergen.dish_id == dish.id
        ).all()
    ]

    return {
        "id": dish.id,
        "name": dish.name,
        "description": dish.description,
        "price": dish.price,
        "category_id": dish.category_id,
        "is_available": dish.is_available,
        "allergen_ids": allergen_ids
    }
