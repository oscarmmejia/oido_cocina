from decimal import Decimal

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dish_routes import router
from app.controllers.dish_controller import deactivate_dish
from app.core.database_connection import Base, get_db
from app.core.kernel.identity import CurrentUser, get_current_user
from app.models.allergen_model import Allergen
from app.models.category_model import Category
from app.models.dish_allergen_model import DishAllergen
from app.models.dish_model import Dish

RESTAURANT_ID = 10


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add_all([
        Category(id=1, restaurant_id=RESTAURANT_ID, name="Mains"),
        Category(id=2, restaurant_id=RESTAURANT_ID, name="Desserts"),
        Allergen(id=1, code="GLUTEN", name="Gluten"),
        Allergen(id=2, code="EGG", name="Egg"),
    ])
    session.commit()
    yield session
    session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(db):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=1,
        restaurant_id=RESTAURANT_ID,
        email="dish-manager@example.com",
        role="manager",
        permissions={"dish:deactivate"},
    )
    return TestClient(app)


def add_dish(db, name="Pizza", **overrides):
    values = {
        "restaurant_id": RESTAURANT_ID,
        "category_id": 1,
        "name": name,
        "price": Decimal("9.50"),
        "is_active": True,
        "is_published": True,
        "is_available": True,
    }
    values.update(overrides)
    dish = Dish(**values)
    db.add(dish)
    db.commit()
    return dish


def get_public(client, **params):
    return client.get(
        "/dishes/public",
        params={"restaurant_id": RESTAURANT_ID, **params},
    )


def test_public_menu_hides_unpublished_dishes(client, db):
    add_dish(db, "Visible")
    add_dish(db, "Hidden", is_published=False)

    body = get_public(client).json()

    assert body["total"] == 1
    assert [item["name"] for item in body["items"]] == ["Visible"]


def test_public_menu_hides_inactive_dishes(client, db):
    add_dish(db, "Visible")
    add_dish(db, "Removed", is_active=False)

    body = get_public(client).json()

    assert [item["name"] for item in body["items"]] == ["Visible"]


def test_public_menu_shows_unavailable_dishes_as_unavailable(client, db):
    add_dish(db, "Sold out", is_available=False)

    body = get_public(client).json()

    assert body["total"] == 1
    assert body["items"][0]["is_available"] is False


def test_public_menu_filters_by_category(client, db):
    add_dish(db, "Steak", category_id=1)
    add_dish(db, "Cake", category_id=2)

    body = get_public(client, category_id=2).json()

    assert [item["name"] for item in body["items"]] == ["Cake"]


def test_public_menu_filters_by_availability(client, db):
    add_dish(db, "Available")
    add_dish(db, "Sold out", is_available=False)

    body = get_public(client, is_available="false").json()

    assert [item["name"] for item in body["items"]] == ["Sold out"]


def test_public_menu_filters_by_allergen(client, db):
    with_gluten = add_dish(db, "Bread")
    add_dish(db, "Salad")
    db.add(DishAllergen(dish_id=with_gluten.id, allergen_id=1))
    db.commit()

    body = get_public(client, allergen_id=1).json()

    assert [item["name"] for item in body["items"]] == ["Bread"]
    assert body["items"][0]["allergen_ids"] == [1]


def test_public_menu_paginates_results_in_stable_order(client, db):
    for number in range(1, 6):
        add_dish(db, f"Dish {number}")

    body = get_public(client, page=2, page_size=2).json()

    assert [item["name"] for item in body["items"]] == ["Dish 3", "Dish 4"]
    assert body["total"] == 5
    assert body["page"] == 2
    assert body["total_pages"] == 3


def test_public_menu_only_shows_dishes_of_the_requested_restaurant(client, db):
    add_dish(db, "Mine")
    add_dish(db, "Other", restaurant_id=99)

    body = get_public(client).json()

    assert [item["name"] for item in body["items"]] == ["Mine"]


@pytest.mark.parametrize(
    "params",
    [{"page": 0}, {"page_size": 0}, {"page_size": 101}],
)
def test_public_menu_rejects_invalid_pagination(client, params):
    assert get_public(client, **params).status_code == 422


def test_public_dish_detail_returns_dish_with_allergens(client, db):
    dish = add_dish(db, "Tortilla")
    db.add_all([
        DishAllergen(dish_id=dish.id, allergen_id=1),
        DishAllergen(dish_id=dish.id, allergen_id=2),
    ])
    db.commit()

    response = client.get(
        f"/dishes/public/{dish.id}",
        params={"restaurant_id": RESTAURANT_ID},
    )

    assert response.status_code == 200
    assert sorted(response.json()["allergen_ids"]) == [1, 2]


def test_public_dish_detail_hides_unpublished_dish(client, db):
    dish = add_dish(db, "Hidden", is_published=False)

    response = client.get(
        f"/dishes/public/{dish.id}",
        params={"restaurant_id": RESTAURANT_ID},
    )

    assert response.status_code == 404


def test_deactivated_dish_is_kept_but_hidden_from_public_menu(client, db):
    dish = add_dish(db)

    deactivate_dish(db, dish.id, RESTAURANT_ID)

    assert db.query(Dish).count() == 1
    assert get_public(client).json()["total"] == 0


def test_deactivating_an_inactive_dish_returns_409(db):
    dish = add_dish(db, is_active=False)

    with pytest.raises(HTTPException) as error:
        deactivate_dish(db, dish.id, RESTAURANT_ID)

    assert error.value.status_code == 409


def test_deactivating_a_dish_of_another_restaurant_returns_404(db):
    dish = add_dish(db, restaurant_id=99)

    with pytest.raises(HTTPException) as error:
        deactivate_dish(db, dish.id, RESTAURANT_ID)

    assert error.value.status_code == 404
    
def update_status(client, dish_id, body, restaurant_id=RESTAURANT_ID):
    return client.patch(
        f"/dishes/{dish_id}/status",
        params={"restaurant_id": restaurant_id},
        json=body,
    )


def test_status_update_publishes_dish_and_shows_it_in_public_menu(client, db):
    dish = add_dish(db, is_published=False)

    response = update_status(client, dish.id, {"is_published": True})

    assert response.status_code == 200
    assert response.json()["is_published"] is True
    assert get_public(client).json()["total"] == 1


def test_status_update_marks_dish_as_unavailable(client, db):
    dish = add_dish(db)

    response = update_status(client, dish.id, {"is_available": False})

    assert response.json()["is_available"] is False
    assert response.json()["is_published"] is True


def test_status_update_rejects_null_values(client, db):
    dish = add_dish(db)

    assert update_status(client, dish.id, {"is_published": None}).status_code == 422


def test_status_update_rejects_empty_body(client, db):
    dish = add_dish(db)

    assert update_status(client, dish.id, {}).status_code == 422


def test_status_update_of_another_restaurant_returns_404(client, db):
    dish = add_dish(db, restaurant_id=99)

    assert update_status(client, dish.id, {"is_published": False}).status_code == 404
