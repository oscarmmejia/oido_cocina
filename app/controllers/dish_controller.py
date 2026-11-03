from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.dish_model import Dish
from app.models.dish_allergen_model import DishAllergen
from app.schemas.dish_schema import DishCreate, DishUpdate



def create_dish(
    db: Session,
    dish_data: DishCreate,
    restaurant_id: int
):
    try:
        # 1. Comprobar que no hay alérgenos duplicados
        if len(dish_data.allergen_ids) != len(set(dish_data.allergen_ids)):
            raise HTTPException(
                status_code=422,
                detail="No se permiten alérgenos duplicados"
            )

        # 2. Comprobar que la categoría pertenece al restaurante
        category = db.execute(
            text("""
                SELECT id
                FROM "Category"
                WHERE id = :category_id
                AND "restaurantId" = :restaurant_id
            """),
            {
                "category_id": dish_data.category_id,
                "restaurant_id": restaurant_id
            }
        ).first()

        if category is None:
            raise HTTPException(
                status_code=422,
                detail="La categoría no existe para este restaurante"
            )

        # 3. Comprobar que todos los alérgenos existen
        for allergen_id in dish_data.allergen_ids:
            allergen = db.execute(
                text("""
                    SELECT id
                    FROM "Allergen"
                    WHERE id = :allergen_id
                """),
                {"allergen_id": allergen_id}
            ).first()

            if allergen is None:
                raise HTTPException(
                    status_code=422,
                    detail=f"El alérgeno {allergen_id} no existe"
                )

        # 4. Crear el plato
        dish = Dish(
            restaurant_id=restaurant_id,
            category_id=dish_data.category_id,
            name=dish_data.name,
            description=dish_data.description,
            price=dish_data.price
        )

        db.add(dish)
        db.flush()

        # 5. Crear las relaciones con los alérgenos
        for allergen_id in dish_data.allergen_ids:
            db.add(
                DishAllergen(
                    dish_id=dish.id,
                    allergen_id=allergen_id
                )
            )

        # 6. Preparar la respuesta antes de confirmar
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

        # 7. Guardar todo junto
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

        # Validar categoría
        if "category_id" in changes:
            category = db.execute(
                text("""
                    SELECT id
                    FROM "Category"
                    WHERE id = :category_id
                    AND "restaurantId" = :restaurant_id
                """),
                {
                    "category_id": changes["category_id"],
                    "restaurant_id": restaurant_id
                }
            ).first()

            if category is None:
                raise HTTPException(
                    status_code=422,
                    detail="La categoría no existe para este restaurante"
                )

        # Validar y actualizar alérgenos
        if "allergen_ids" in changes:
            allergen_ids = changes.pop("allergen_ids")

            if len(allergen_ids) != len(set(allergen_ids)):
                raise HTTPException(
                    status_code=422,
                    detail="No se permiten alérgenos duplicados"
                )

            for allergen_id in allergen_ids:
                allergen = db.execute(
                    text("""
                        SELECT id
                        FROM "Allergen"
                        WHERE id = :allergen_id
                    """),
                    {"allergen_id": allergen_id}
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

        # Aplicar los cambios del plato
        for field, value in changes.items():
            setattr(dish, field, value)

        # Preparar los alérgenos de la respuesta antes del commit
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

        # Preparar la respuesta
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

        # Confirmar al final
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