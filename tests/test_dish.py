from decimal import Decimal

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.controllers.dish_controller import create_dish, get_dish
from app.schemas.dish_schema import DishCreate, DishUpdate


def test_dish_rejects_negative_price():
    with pytest.raises(ValidationError):
        DishCreate(
            name="Pizza cuatro quesos",
            price=Decimal("-1.00"),
            category_id=1,
            allergen_ids=[1, 2]
        )


def test_dish_accepts_valid_price():
    dish = DishCreate(
        name="Pizza cuatro quesos",
        price=Decimal("9.50"),
        category_id=1,
        allergen_ids=[1, 2]
    )

    assert dish.price == Decimal("9.50")


def test_dish_requires_name():
    with pytest.raises(ValidationError):
        DishCreate(
            price=Decimal("9.50"),
            category_id=1,
            allergen_ids=[1, 2]
        )


def test_dish_requires_category():
    with pytest.raises(ValidationError):
        DishCreate(
            name="Pizza cuatro quesos",
            price=Decimal("9.50"),
            allergen_ids=[1, 2]
        )


def test_dish_update_rejects_null_name():
    with pytest.raises(ValidationError):
        DishUpdate(name=None)


def test_dish_update_rejects_null_category():
    with pytest.raises(ValidationError):
        DishUpdate(category_id=None)


def test_dish_update_rejects_null_allergen_ids():
    with pytest.raises(ValidationError):
        DishUpdate(allergen_ids=None)


def test_create_dish_rejects_duplicate_allergens_before_database_queries():
    class FakeDB:
        def rollback(self):
            pass

    dish_data = DishCreate(
        name="Pizza cuatro quesos",
        price=Decimal("9.50"),
        category_id=1,
        allergen_ids=[1, 1]
    )

    with pytest.raises(HTTPException) as error:
        create_dish(
            db=FakeDB(),
            dish_data=dish_data,
            restaurant_id=1
        )

    assert error.value.status_code == 422
    assert error.value.detail == "No se permiten alérgenos duplicados"


def test_create_dish_rejects_unknown_allergen_without_saving():
    class FakeResult:
        def first(self):
            return (1,)

    class FakeDB:
        def __init__(self):
            self.rollback_called = False
            self.add_called = False

        def execute(self, statement, parameters):
            if '"Category"' in str(statement):
                return FakeResult()

            return type(
                "EmptyResult",
                (),
                {"first": lambda self: None}
            )()

        def rollback(self):
            self.rollback_called = True

        def add(self, item):
            self.add_called = True

    db = FakeDB()

    dish_data = DishCreate(
        name="Pizza cuatro quesos",
        price=Decimal("9.50"),
        category_id=1,
        allergen_ids=[999]
    )

    with pytest.raises(HTTPException) as error:
        create_dish(
            db=db,
            dish_data=dish_data,
            restaurant_id=1
        )

    assert error.value.status_code == 422
    assert db.rollback_called is True
    assert db.add_called is False


def test_create_dish_saves_valid_dish_with_allergens():
    from app.models.dish_model import Dish
    from app.models.dish_allergen_model import DishAllergen

    class FakeResult:
        def first(self):
            return (1,)

    class FakeDB:
        def __init__(self):
            self.added_objects = []
            self.committed = False
            self.refreshed = False

        def execute(self, statement, parameters):
            return FakeResult()

        def add(self, item):
            self.added_objects.append(item)

        def flush(self):
            dish = self.added_objects[0]
            dish.id = 100
            dish.is_active = True
            dish.is_published = False
            dish.is_available = True

        def commit(self):
            self.committed = True

        def refresh(self, item):
            self.refreshed = True

        def rollback(self):
            pass

    db = FakeDB()

    dish_data = DishCreate(
        name="Pizza cuatro quesos",
        price=Decimal("9.50"),
        category_id=1,
        allergen_ids=[1, 2]
    )

    result = create_dish(
        db=db,
        dish_data=dish_data,
        restaurant_id=10
    )

    assert result["id"] == 100
    assert result["restaurant_id"] == 10
    assert result["category_id"] == 1
    assert result["name"] == "Pizza cuatro quesos"
    assert result["price"] == Decimal("9.50")
    assert result["allergen_ids"] == [1, 2]

    assert db.committed is True
    assert db.refreshed is False

    assert isinstance(db.added_objects[0], Dish)

    allergen_relations = [
        item for item in db.added_objects
        if isinstance(item, DishAllergen)
    ]

    assert len(allergen_relations) == 2
    assert allergen_relations[0].allergen_id == 1
    assert allergen_relations[1].allergen_id == 2


def test_get_dish_returns_dish_with_allergens():
    from types import SimpleNamespace

    class FakeQuery:
        def __init__(self, result):
            self.result = result

        def filter(self, *conditions):
            return self

        def first(self):
            return self.result

        def all(self):
            return self.result

    dish = SimpleNamespace(
        id=100,
        restaurant_id=10,
        category_id=1,
        name="Pizza cuatro quesos",
        description=None,
        price=Decimal("9.50"),
        is_active=True,
        is_published=False,
        is_available=True
    )

    class FakeDB:
        def __init__(self):
            self.query_count = 0

        def query(self, model):
            self.query_count += 1

            if self.query_count == 1:
                return FakeQuery(dish)

            return FakeQuery([(1,), (2,)])

    result = get_dish(
        db=FakeDB(),
        dish_id=100,
        restaurant_id=10
    )

    assert result["id"] == 100
    assert result["name"] == "Pizza cuatro quesos"
    assert result["price"] == Decimal("9.50")
    assert result["allergen_ids"] == [1, 2]


def test_get_dish_returns_404_when_dish_does_not_belong_to_restaurant():
    class FakeQuery:
        def filter(self, *conditions):
            return self

        def first(self):
            return None

    class FakeDB:
        def query(self, model):
            return FakeQuery()

    with pytest.raises(HTTPException) as error:
        get_dish(
            db=FakeDB(),
            dish_id=100,
            restaurant_id=20
        )

    assert error.value.status_code == 404
    assert error.value.detail == "Plato no encontrado"


def test_get_dishes_returns_only_restaurant_dishes_with_allergens():
    from types import SimpleNamespace

    dish_one = SimpleNamespace(
        id=100,
        restaurant_id=10,
        category_id=1,
        name="Pizza cuatro quesos",
        description=None,
        price=Decimal("9.50"),
        is_active=True,
        is_published=False,
        is_available=True
    )

    dish_two = SimpleNamespace(
        id=101,
        restaurant_id=10,
        category_id=2,
        name="Ensalada mixta",
        description="Ensalada fresca",
        price=Decimal("7.00"),
        is_active=True,
        is_published=True,
        is_available=True
    )

    class FakeQuery:
        def __init__(self, result):
            self.result = result

        def filter(self, *conditions):
            return self

        def order_by(self, *conditions):
            return self

        def all(self):
            return self.result

    class FakeDB:
        def __init__(self):
            self.query_count = 0

        def query(self, model):
            self.query_count += 1

            if self.query_count == 1:
                return FakeQuery([dish_one, dish_two])

            if self.query_count == 2:
                return FakeQuery([(1,), (2,)])

            return FakeQuery([(3,)])

    from app.controllers.dish_controller import get_dishes

    result = get_dishes(
        db=FakeDB(),
        restaurant_id=10
    )

    assert len(result) == 2
    assert result[0]["name"] == "Pizza cuatro quesos"
    assert result[0]["allergen_ids"] == [1, 2]
    assert result[1]["name"] == "Ensalada mixta"
    assert result[1]["allergen_ids"] == [3]



def test_update_dish_changes_name_and_price():
    from types import SimpleNamespace
    from app.controllers.dish_controller import update_dish

    dish = SimpleNamespace(
        id=100,
        restaurant_id=10,
        category_id=1,
        name="Pizza cuatro quesos",
        description=None,
        price=Decimal("9.50"),
        is_active=True,
        is_published=False,
        is_available=True
    )

    class FakeQuery:
        def __init__(self, result):
            self.result = result

        def filter(self, *conditions):
            return self

        def first(self):
            return self.result

        def all(self):
            return self.result

    class FakeDB:
        def __init__(self):
            self.committed = False
            self.refreshed = False
            self.query_count = 0

        def query(self, model):
            from app.models.dish_model import Dish
            from app.models.dish_allergen_model import DishAllergen

            if model is Dish:
                return FakeQuery(dish)

            if model is DishAllergen.allergen_id:
                return FakeQuery([(1,), (2,)])

            raise AssertionError("Consulta inesperada")

        def commit(self):
            self.committed = True

        def refresh(self, item):
            self.refreshed = True

        def rollback(self):
            pass

    db = FakeDB()

    changes = DishUpdate(
        name="Pizza especial",
        price=Decimal("12.00")
    )

    result = update_dish(
        db=db,
        dish_id=100,
        dish_data=changes,
        restaurant_id=10
    )

    assert result["name"] == "Pizza especial"
    assert result["price"] == Decimal("12.00")
    assert result["category_id"] == 1
    assert result["allergen_ids"] == [1, 2]
    assert db.committed is True
    assert db.refreshed is False


def test_update_dish_returns_404_for_another_restaurant():
    from app.controllers.dish_controller import update_dish

    class FakeQuery:
        def filter(self, *conditions):
            return self

        def first(self):
            return None

    class FakeDB:
        def __init__(self):
            self.committed = False
            self.rollback_called = False

        def query(self, model):
            return FakeQuery()

        def commit(self):
            self.committed = True

        def rollback(self):
            self.rollback_called = True

    db = FakeDB()

    changes = DishUpdate(
        name="Pizza modificada"
    )

    with pytest.raises(HTTPException) as error:
        update_dish(
            db=db,
            dish_id=100,
            dish_data=changes,
            restaurant_id=20
        )

    assert error.value.status_code == 404
    assert error.value.detail == "Plato no encontrado"
    assert db.committed is False
    assert db.rollback_called is True


def test_update_dish_rejects_unknown_allergen_without_committing():
    from types import SimpleNamespace
    from app.controllers.dish_controller import update_dish

    dish = SimpleNamespace(
        id=100,
        restaurant_id=10,
        category_id=1,
        name="Pizza cuatro quesos",
        description=None,
        price=Decimal("9.50"),
        is_active=True,
        is_published=False,
        is_available=True
    )

    class FakeResult:
        def first(self):
            return None

    class FakeQuery:
        def filter(self, *conditions):
            return self

        def first(self):
            return dish

    class FakeDB:
        def __init__(self):
            self.committed = False
            self.rollback_called = False

        def query(self, model):
            return FakeQuery()

        def execute(self, statement, parameters):
            return FakeResult()

        def commit(self):
            self.committed = True

        def rollback(self):
            self.rollback_called = True

    db = FakeDB()

    changes = DishUpdate(
        allergen_ids=[999]
    )

    with pytest.raises(HTTPException) as error:
        update_dish(
            db=db,
            dish_id=100,
            dish_data=changes,
            restaurant_id=10
        )

    assert error.value.status_code == 422
    assert error.value.detail == "El alérgeno 999 no existe"
    assert db.committed is False
    assert db.rollback_called is True



def test_update_dish_can_remove_all_allergens():
    from types import SimpleNamespace
    from app.controllers.dish_controller import update_dish
    from app.models.dish_model import Dish
    from app.models.dish_allergen_model import DishAllergen

    dish = SimpleNamespace(
        id=100,
        restaurant_id=10,
        category_id=1,
        name="Pizza cuatro quesos",
        description=None,
        price=Decimal("9.50"),
        is_active=True,
        is_published=False,
        is_available=True
    )

    class FakeQuery:
        def __init__(self, result):
            self.result = result

        def filter(self, *conditions):
            return self

        def first(self):
            return self.result

        def all(self):
            return self.result

        def delete(self, synchronize_session=False):
            return 2

    class FakeDB:
        def __init__(self):
            self.deleted = False
            self.committed = False

        def query(self, model):
            if model is Dish:
                return FakeQuery(dish)

            if model is DishAllergen:
                query = FakeQuery([])
                query.delete = self.delete_allergens
                return query

            if model is DishAllergen.allergen_id:
                return FakeQuery([])

            raise AssertionError("Consulta inesperada")

        def delete_allergens(self, synchronize_session=False):
            self.deleted = True
            return 2

        def execute(self, statement, parameters):
            raise AssertionError("No deben consultarse alérgenos")

        def add(self, item):
            raise AssertionError("No deben añadirse relaciones")

        def commit(self):
            self.committed = True

        def refresh(self, item):
            pass

        def rollback(self):
            pass

    db = FakeDB()

    result = update_dish(
        db=db,
        dish_id=100,
        dish_data=DishUpdate(allergen_ids=[]),
        restaurant_id=10
    )

    assert result["allergen_ids"] == []
    assert db.deleted is True
    assert db.committed is True


def test_update_dish_replaces_allergens():
    from types import SimpleNamespace
    from app.controllers.dish_controller import update_dish
    from app.models.dish_model import Dish
    from app.models.dish_allergen_model import DishAllergen

    dish = SimpleNamespace(
        id=100,
        restaurant_id=10,
        category_id=1,
        name="Pizza",
        description=None,
        price=Decimal("9.50"),
        is_active=True,
        is_published=False,
        is_available=True
    )

    class FakeQuery:
        def __init__(self, result):
            self.result = result

        def filter(self, *conditions):
            return self

        def first(self):
            return self.result

        def all(self):
            return self.result

        def delete(self, synchronize_session=False):
            return 1

    class FakeDB:
        def __init__(self):
            self.added = []
            self.committed = False

        def query(self, model):
            if model is Dish:
                return FakeQuery(dish)

            if model is DishAllergen:
                return FakeQuery([])

            if model is DishAllergen.allergen_id:
                return FakeQuery([(2,), (3,)])

            raise AssertionError("Consulta inesperada")

        def execute(self, statement, parameters):
            return FakeQuery(SimpleNamespace(id=parameters["allergen_id"]))

        def add(self, item):
            self.added.append(item)

        def commit(self):
            self.committed = True

        def refresh(self, item):
            pass

        def rollback(self):
            pass

    db = FakeDB()

    result = update_dish(
        db=db,
        dish_id=100,
        dish_data=DishUpdate(allergen_ids=[2, 3]),
        restaurant_id=10
    )

    assert result["allergen_ids"] == [2, 3]
    assert len(db.added) == 2
    assert db.committed is True

def test_update_dish_rejects_duplicate_allergens():
    from fastapi import HTTPException
    from types import SimpleNamespace
    from app.controllers.dish_controller import update_dish

    dish = SimpleNamespace(
        id=100,
        restaurant_id=10,
        category_id=1,
        name="Pizza",
        description=None,
        price=Decimal("9.50"),
        is_active=True,
        is_published=False,
        is_available=True
    )

    class FakeQuery:
        def filter(self, *conditions):
            return self

        def first(self):
            return dish

    class FakeDB:
        committed = False

        def query(self, model):
            return FakeQuery()

        def commit(self):
            self.committed = True

        def rollback(self):
            pass

    db = FakeDB()

    with pytest.raises(HTTPException) as error:
        update_dish(
            db,
            100,
            DishUpdate(allergen_ids=[2, 2]),
            10
        )

    assert error.value.status_code == 422
    assert db.committed is False

def test_create_dish_rejects_category_from_another_restaurant():
    from fastapi import HTTPException
    from app.controllers.dish_controller import create_dish

    class FakeResult:
        def first(self):
            return None

    class FakeDB:
        committed = False
        added = []

        def execute(self, statement, parameters):
            return FakeResult()

        def add(self, item):
            self.added.append(item)

        def commit(self):
            self.committed = True

        def rollback(self):
            pass

    db = FakeDB()

    with pytest.raises(HTTPException) as error:
        create_dish(
            db=db,
            dish_data=DishCreate(
                name="Pizza",
                price=Decimal("9.50"),
                category_id=999,
                allergen_ids=[]
            ),
            restaurant_id=10
        )

    assert error.value.status_code == 422
    assert db.added == []
    assert db.committed is False