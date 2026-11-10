import pytest
from fastapi import HTTPException
from types import SimpleNamespace

from app.controllers.category_controller import (
    create_category,
    get_category,
    get_categories,
    update_category,
    deactivate_category
)

from app.schemas.category_schema import (
    CategoryCreate,
    CategoryUpdate
)


def test_create_category_saves_valid_category():

    class FakeQuery:
        def filter(self, *conditions):
            return self

        def first(self):
            return None

    class FakeDB:
        def __init__(self):
            self.added = []
            self.committed = False

        def query(self, model):
            return FakeQuery()

        def add(self, item):
            self.added.append(item)

        def flush(self):
            self.added[0].id = 1

        def commit(self):
            self.committed = True

        def rollback(self):
            pass

    db = FakeDB()

    result = create_category(
        db=db,
        category_data=CategoryCreate(
            name="Pizzas",
            sort_order=1
        ),
        restaurant_id=10
    )

    assert result["id"] == 1
    assert result["restaurant_id"] == 10
    assert result["name"] == "Pizzas"
    assert result["sort_order"] == 1
    assert db.committed is True
    assert len(db.added) == 1
    
def test_get_category_returns_category_from_restaurant():
    category = SimpleNamespace(
        id=1,
        restaurant_id=10,
        name="Pizzas",
        sort_order=1,
        is_active=True
    )

    class FakeQuery:
        def filter(self, *conditions):
            return self

        def first(self):
            return category

    class FakeDB:
        def query(self, model):
            return FakeQuery()

    result = get_category(FakeDB(), 1, 10)

    assert result.name == "Pizzas"


def test_get_category_returns_404_for_another_restaurant():
    class FakeQuery:
        def filter(self, *conditions):
            return self

        def first(self):
            return None

    class FakeDB:
        def query(self, model):
            return FakeQuery()

    with pytest.raises(HTTPException) as error:
        get_category(FakeDB(), 1, 20)

    assert error.value.status_code == 404


def test_get_categories_returns_restaurant_categories():
    categories = [
        SimpleNamespace(name="Pizzas", sort_order=1),
        SimpleNamespace(name="Postres", sort_order=2)
    ]

    class FakeQuery:
        def filter(self, *conditions):
            return self

        def order_by(self, *conditions):
            return self

        def all(self):
            return categories

    class FakeDB:
        def query(self, model):
            return FakeQuery()

    result = get_categories(FakeDB(), 10)

    assert len(result) == 2
    assert result[0].name == "Pizzas"


def test_update_category_changes_name():
    category = SimpleNamespace(
        id=1,
        restaurant_id=10,
        name="Pizzas",
        sort_order=1,
        is_active=True
    )

    class FakeQuery:
        def __init__(self, result):
            self.result = result

        def filter(self, *conditions):
            return self

        def first(self):
            return self.result

    class FakeDB:
        def __init__(self):
            self.committed = False
            self.query_count = 0

        def query(self, model):
            self.query_count += 1

            if self.query_count == 1:
                return FakeQuery(category)

            return FakeQuery(None)

        def commit(self):
            self.committed = True

        def rollback(self):
            pass

    db = FakeDB()

    result = update_category(
        db,
        1,
        CategoryUpdate(name="Pastas"),
        10
    )

    assert result["name"] == "Pastas"
    assert category.name == "Pastas"
    assert db.committed is True

def test_deactivate_category_rejects_active_dishes():
    class FakeQuery:
        def __init__(self, result):
            self.result = result

        def filter(self, *conditions):
            return self

        def first(self):
            return self.result

    category = SimpleNamespace(is_active=True)

    class FakeDB:
        committed = False
        rollback_called = False
        query_count = 0

        def query(self, model):
            self.query_count += 1

            if self.query_count == 1:
                return FakeQuery(category)

            return FakeQuery(SimpleNamespace(id=5))

        def commit(self):
            self.committed = True

        def rollback(self):
            self.rollback_called = True

    db = FakeDB()

    with pytest.raises(HTTPException) as error:
        deactivate_category(db, 1, 10)

    assert error.value.status_code == 409
    assert db.committed is False
    assert db.rollback_called is True   