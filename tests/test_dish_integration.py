from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database_connection import Base
from app.models import Allergen, Category, Dish, DishAllergen, Restaurant
from app.controllers.dish_controller import create_dish, get_dish
from app.schemas.dish_schema import DishCreate


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()

    session.add(Restaurant(id=10, name="Pruebas", time_zone="Europe/Madrid"))
    session.add(
        Category(
            id=1,
            restaurant_id=10,
            name="Platos principales",
            sort_order=0,
            is_active=True,
        )
    )
    session.add_all(
        [
            Allergen(id=1, code="GLUTEN", name="Gluten"),
            Allergen(id=2, code="CRUSTACEOS", name="Crustáceos"),
        ]
    )
    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_integration_create_dish_with_allergens(db):
    dish_data = DishCreate(
        name="Tortilla",
        description="Tortilla de patatas",
        price=Decimal("9.50"),
        category_id=1,
        allergen_ids=[1, 2],
    )

    result = create_dish(db, dish_data, restaurant_id=10)

    saved_dish = db.query(Dish).filter_by(id=result["id"]).first()
    saved_relations = db.query(DishAllergen).filter_by(
        dish_id=result["id"]
    ).all()

    assert saved_dish is not None
    assert saved_dish.name == "Tortilla"
    assert saved_dish.description == "Tortilla de patatas"
    assert saved_dish.price == Decimal("9.50")
    assert len(saved_relations) == 2
    assert {relation.allergen_id for relation in saved_relations} == {1, 2}


def test_integration_get_dish_with_allergens(db):
    dish_data = DishCreate(
        name="Tortilla",
        price=Decimal("9.50"),
        category_id=1,
        allergen_ids=[1, 2],
    )

    created = create_dish(db, dish_data, restaurant_id=10)

    result = get_dish(
        db,
        dish_id=created["id"],
        restaurant_id=10,
    )

    assert result["name"] == "Tortilla"
    assert set(result["allergen_ids"]) == {1, 2}


def test_integration_unknown_allergen_does_not_save_dish(db):
    dish_data = DishCreate(
        name="Plato no válido",
        price=Decimal("9.50"),
        category_id=1,
        allergen_ids=[999],
    )

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as error:
        create_dish(db, dish_data, restaurant_id=10)

    assert error.value.status_code == 422
    assert db.query(Dish).count() == 0
    assert db.query(DishAllergen).count() == 0

def test_integration_unknown_category_does_not_save_dish(db):
    dish_data = DishCreate(
        name="Plato no válido",
        price=Decimal("9.50"),
        category_id=999,
        allergen_ids=[],
    )

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as error:
        create_dish(db, dish_data, restaurant_id=10)

    assert error.value.status_code == 422
    assert db.query(Dish).count() == 0
    assert db.query(DishAllergen).count() == 0

def test_integration_failed_update_preserves_previous_allergens(db):
    from fastapi import HTTPException

    from app.controllers.dish_controller import update_dish
    from app.schemas.dish_schema import DishUpdate

    created = create_dish(
        db,
        DishCreate(
            name="Tortilla",
            price=Decimal("9.50"),
            category_id=1,
            allergen_ids=[1, 2],
        ),
        restaurant_id=10,
    )

    with pytest.raises(HTTPException) as error:
        update_dish(
            db,
            dish_id=created["id"],
            dish_data=DishUpdate(
                name="Tortilla modificada",
                allergen_ids=[999],
            ),
            restaurant_id=10,
        )

    db.expire_all()

    saved_dish = db.query(Dish).filter_by(id=created["id"]).first()
    saved_relations = db.query(DishAllergen).filter_by(
        dish_id=created["id"]
    ).all()

    assert error.value.status_code == 422
    assert saved_dish.name == "Tortilla"
    assert {relation.allergen_id for relation in saved_relations} == {1, 2}
