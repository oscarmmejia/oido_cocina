from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.controllers.dish_controller import (
    deactivate_dish,
    get_public_dish,
    get_public_dishes,
)


def make_dish(**kwargs):
    defaults = dict(
        id=1,
        restaurant_id=10,
        category_id=1,
        name="Pizza",
        description=None,
        price=Decimal("9.50"),
        is_active=True,
        is_published=True,
        is_available=True,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class FakeQuery:
    def __init__(self, result):
        self._result = result

    def filter(self, *args):
        return self

    def offset(self, n):
        return self

    def limit(self, n):
        return self

    def order_by(self, *args):
        return self

    def count(self):
        if isinstance(self._result, list):
            return len(self._result)
        return 0 if self._result is None else 1

    def first(self):
        if isinstance(self._result, list):
            return self._result[0] if self._result else None
        return self._result

    def all(self):
        if isinstance(self._result, list):
            return self._result
        return [self._result] if self._result is not None else []

    def subquery(self):
        return self

    def in_(self, subquery):
        return True


def test_public_menu_hides_unpublished_dishes():
    class FakeDB:
        def query(self, model):
            from app.models.dish_model import Dish
            if model is Dish:
                return FakeQuery([])
            return FakeQuery([])

    result = get_public_dishes(db=FakeDB(), restaurant_id=10)
    assert result["total"] == 0
    assert result["items"] == []


def test_public_menu_shows_unavailable_dishes_with_flag():
    dish = make_dish(is_available=False)

    class FakeDB:
        def query(self, model):
            from app.models.dish_model import Dish
            from app.models.dish_allergen_model import DishAllergen
            if model is Dish:
                return FakeQuery([dish])
            if model is DishAllergen.allergen_id:
                return FakeQuery([])
            return FakeQuery([])

    result = get_public_dishes(db=FakeDB(), restaurant_id=10)
    assert result["total"] == 1
    assert result["items"][0]["is_available"] is False


def test_public_menu_filters_by_category():
    dish = make_dish(category_id=5)

    class FakeDB:
        def query(self, model):
            from app.models.dish_model import Dish
            from app.models.dish_allergen_model import DishAllergen
            if model is Dish:
                return FakeQuery([dish])
            if model is DishAllergen.allergen_id:
                return FakeQuery([])
            return FakeQuery([])

    result = get_public_dishes(db=FakeDB(), restaurant_id=10, category_id=5)
    assert result["total"] == 1
    assert result["items"][0]["category_id"] == 5


def test_public_menu_filters_by_allergen():
    dish = make_dish()

    class FakeDB:
        def query(self, model):
            from app.models.dish_model import Dish
            from app.models.dish_allergen_model import DishAllergen
            if model is Dish:
                return FakeQuery([dish])
            if model is DishAllergen.dish_id:
                return FakeQuery([dish.id])
            if model is DishAllergen.allergen_id:
                return FakeQuery([(1,)])
            return FakeQuery([])

    result = get_public_dishes(db=FakeDB(), restaurant_id=10, allergen_id=1)
    assert result["total"] == 1
    assert 1 in result["items"][0]["allergen_ids"]


def test_public_menu_pagination():
    dishes = [make_dish(id=i) for i in range(1, 6)]

    class FakeDB:
        def query(self, model):
            from app.models.dish_model import Dish
            from app.models.dish_allergen_model import DishAllergen
            if model is Dish:
                return FakeQuery(dishes)
            if model is DishAllergen.allergen_id:
                return FakeQuery([])
            return FakeQuery([])

    result = get_public_dishes(db=FakeDB(), restaurant_id=10, page=1, page_size=5)
    assert result["total"] == 5
    assert result["page"] == 1
    assert result["page_size"] == 5
    assert result["total_pages"] == 1


def test_deactivate_dish_sets_is_active_false():
    dish = make_dish(is_active=True)

    class FakeDB:
        committed = False

        def query(self, model):
            return FakeQuery(dish)

        def commit(self):
            self.committed = True

        def rollback(self):
            pass

    db = FakeDB()
    result = deactivate_dish(db=db, dish_id=1, restaurant_id=10)

    assert dish.is_active is False
    assert db.committed is True
    assert result["id"] == 1


def test_deactivate_dish_returns_404_for_other_restaurant():
    class FakeDB:
        def query(self, model):
            return FakeQuery(None)

        def rollback(self):
            pass

    with pytest.raises(HTTPException) as error:
        deactivate_dish(db=FakeDB(), dish_id=1, restaurant_id=99)

    assert error.value.status_code == 404


def test_deactivate_already_inactive_dish_returns_409():
    dish = make_dish(is_active=False)

    class FakeDB:
        def query(self, model):
            return FakeQuery(dish)

        def rollback(self):
            pass

    with pytest.raises(HTTPException) as error:
        deactivate_dish(db=FakeDB(), dish_id=1, restaurant_id=10)

    assert error.value.status_code == 409
    assert error.value.detail == "El plato ya está desactivado"


def test_get_public_dish_returns_dish():
    dish = make_dish()

    class FakeDB:
        def query(self, model):
            from app.models.dish_model import Dish
            from app.models.dish_allergen_model import DishAllergen
            if model is Dish:
                return FakeQuery(dish)
            if model is DishAllergen.allergen_id:
                return FakeQuery([(1,), (2,)])
            return FakeQuery([])

    result = get_public_dish(db=FakeDB(), dish_id=1, restaurant_id=10)
    assert result["id"] == 1
    assert result["allergen_ids"] == [1, 2]


def test_get_public_dish_returns_404_if_not_published():
    class FakeDB:
        def query(self, model):
            return FakeQuery(None)

        def rollback(self):
            pass

    with pytest.raises(HTTPException) as error:
        get_public_dish(db=FakeDB(), dish_id=1, restaurant_id=10)

    assert error.value.status_code == 404

