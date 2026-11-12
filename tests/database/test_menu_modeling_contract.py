"""Contract of the menu schema: dishes, allergens, collections and menus.

The metadata and relationship checks run without a database. Every test whose
name starts with `test_postgres_` runs against the configured PostgreSQL
database and is rolled back by the `session` fixture.
"""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import CheckConstraint, delete, func, insert, select
from sqlalchemy.exc import IntegrityError

from app.database.base import Base
from app.models import (
    Allergen,
    Category,
    Dish,
    DishAllergen,
    Menu,
    MenuCollection,
    MenuDish,
    Restaurant,
)


# ---------------------------------------------------------------------------
# Metadata contracts (no database)
# ---------------------------------------------------------------------------


def test_metadata_registers_the_seven_menu_tables():
    expected = {
        "allergens",
        "categories",
        "dishes",
        "dish_allergens",
        "menu_collections",
        "menus",
        "menu_dishes",
    }

    assert expected <= set(Base.metadata.tables)


def test_dish_allergens_has_a_composite_primary_key():
    primary_key = tuple(c.name for c in DishAllergen.__table__.primary_key.columns)

    assert primary_key == ("dish_id", "allergen_id")


def test_menu_dishes_has_a_composite_primary_key():
    primary_key = tuple(c.name for c in MenuDish.__table__.primary_key.columns)

    assert primary_key == ("menu_id", "dish_id")


def test_is_required_lives_only_in_menu_dishes():
    assert "is_required" in MenuDish.__table__.columns
    assert "is_required" not in DishAllergen.__table__.columns


def test_dish_price_check_is_declared():
    names = {
        constraint.name
        for constraint in Dish.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert "ck_dishes_price_non_negative" in names


def test_menu_collection_type_and_validity_checks_are_declared():
    names = {
        constraint.name
        for constraint in MenuCollection.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert {"ck_menu_collections_type", "ck_menu_collections_valid_range"} <= names


def test_menu_price_and_role_checks_are_declared():
    menu_names = {
        constraint.name
        for constraint in Menu.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }
    menu_dish_names = {
        constraint.name
        for constraint in MenuDish.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert "ck_menus_own_price_non_negative" in menu_names
    assert "ck_menu_dishes_role" in menu_dish_names


def test_menu_relationships_are_bidirectional():
    restaurant = Restaurant(name="contract-menu", timezone="Europe/Madrid")
    category = Category(name="Entrantes", restaurant=restaurant)
    dish = Dish(
        name="Tortilla",
        price=Decimal("9.50"),
        restaurant=restaurant,
        category=category,
    )
    allergen = Allergen(code="contract-gluten", name="Gluten")
    dish.allergens.append(allergen)

    collection = MenuCollection(name="Diario", type="daily", restaurant=restaurant)
    menu = Menu(name="Menú del día", own_price=Decimal("15.00"), collection=collection)
    link = MenuDish(
        menu=menu,
        dish=dish,
        role="main",
        is_required=True,
        includes_drink=False,
    )

    assert category.restaurant is restaurant
    assert dish.restaurant is restaurant
    assert dish.category is category
    assert dish.allergens == [allergen]
    assert allergen.dishes == [dish]
    assert collection.restaurant is restaurant
    assert menu.collection is collection
    assert link.menu is menu
    assert link.dish is dish
    assert menu.dish_links == [link]
    assert dish.menu_links == [link]
    assert restaurant.categories == [category]
    assert restaurant.dishes == [dish]
    assert restaurant.menu_collections == [collection]


# ---------------------------------------------------------------------------
# PostgreSQL integrity contracts (rolled back by the session fixture)
# ---------------------------------------------------------------------------


def make_restaurant(session, name="contract-menu-restaurant"):
    restaurant = Restaurant(name=name, timezone="Europe/Madrid")
    session.add(restaurant)
    session.flush()
    return restaurant


def make_category(session, restaurant, name="Entrantes"):
    category = Category(restaurant_id=restaurant.id, name=name)
    session.add(category)
    session.flush()
    return category


def make_dish(session, restaurant, category, name="Tortilla", price=Decimal("9.50")):
    dish = Dish(
        restaurant_id=restaurant.id,
        category_id=category.id,
        name=name,
        price=price,
    )
    session.add(dish)
    session.flush()
    return dish


def make_collection(session, restaurant, name="Diario"):
    collection = MenuCollection(
        restaurant_id=restaurant.id,
        name=name,
        type="daily",
    )
    session.add(collection)
    session.flush()
    return collection


def make_menu(session, collection, name="Menú del día"):
    menu = Menu(
        collection_id=collection.id,
        name=name,
        own_price=Decimal("15.00"),
    )
    session.add(menu)
    session.flush()
    return menu


def test_postgres_rejects_a_negative_dish_price(session):
    restaurant = make_restaurant(session)
    category = make_category(session, restaurant)

    with pytest.raises(IntegrityError) as error:
        with session.begin_nested():
            session.execute(
                insert(Dish).values(
                    restaurant_id=restaurant.id,
                    category_id=category.id,
                    name="Negativo",
                    price=Decimal("-1.00"),
                )
            )

    assert error.value.orig.sqlstate == "23514"


def test_postgres_rejects_a_negative_menu_price(session):
    restaurant = make_restaurant(session)
    collection = make_collection(session, restaurant)

    with pytest.raises(IntegrityError) as error:
        with session.begin_nested():
            session.execute(
                insert(Menu).values(
                    collection_id=collection.id,
                    name="Negativo",
                    own_price=Decimal("-1.00"),
                )
            )

    assert error.value.orig.sqlstate == "23514"


def test_postgres_rejects_an_invalid_menu_dish_role(session):
    restaurant = make_restaurant(session)
    category = make_category(session, restaurant)
    dish = make_dish(session, restaurant, category)
    collection = make_collection(session, restaurant)
    menu = make_menu(session, collection)

    with pytest.raises(IntegrityError) as error:
        with session.begin_nested():
            session.execute(
                insert(MenuDish).values(
                    menu_id=menu.id,
                    dish_id=dish.id,
                    role="invalid",
                )
            )

    assert error.value.orig.sqlstate == "23514"


def test_postgres_rejects_a_validity_range_that_ends_before_it_starts(session):
    restaurant = make_restaurant(session)

    with pytest.raises(IntegrityError) as error:
        with session.begin_nested():
            session.execute(
                insert(MenuCollection).values(
                    restaurant_id=restaurant.id,
                    name="Rango inválido",
                    type="seasonal",
                    valid_from=date(2026, 1, 10),
                    valid_to=date(2026, 1, 9),
                )
            )

    assert error.value.orig.sqlstate == "23514"


def test_postgres_accepts_a_single_day_validity(session):
    restaurant = make_restaurant(session)

    session.add(
        MenuCollection(
            restaurant_id=restaurant.id,
            name="Un solo día",
            type="daily",
            valid_from=date(2026, 1, 10),
            valid_to=date(2026, 1, 10),
        )
    )
    session.flush()

    assert (
        session.scalar(
            select(func.count())
            .select_from(MenuCollection)
            .where(MenuCollection.name == "Un solo día")
        )
        == 1
    )


def test_postgres_allows_overlapping_active_collections(session):
    restaurant = make_restaurant(session)

    session.add_all(
        [
            MenuCollection(
                restaurant_id=restaurant.id,
                name="Temporada A",
                type="seasonal",
                valid_from=date(2026, 1, 1),
                valid_to=date(2026, 3, 31),
                is_active=True,
            ),
            MenuCollection(
                restaurant_id=restaurant.id,
                name="Temporada B",
                type="seasonal",
                valid_from=date(2026, 3, 1),
                valid_to=date(2026, 5, 31),
                is_active=True,
            ),
        ]
    )
    session.flush()

    assert (
        session.scalar(
            select(func.count())
            .select_from(MenuCollection)
            .where(MenuCollection.restaurant_id == restaurant.id)
        )
        == 2
    )


def test_postgres_rejects_a_duplicate_dish_allergen(session):
    restaurant = make_restaurant(session)
    category = make_category(session, restaurant)
    dish = make_dish(session, restaurant, category)
    allergen = Allergen(code="contract-gluten", name="Gluten")
    session.add(allergen)
    session.flush()

    session.add(DishAllergen(dish_id=dish.id, allergen_id=allergen.id))
    session.flush()

    with pytest.raises(IntegrityError) as error:
        with session.begin_nested():
            session.execute(
                insert(DishAllergen).values(
                    dish_id=dish.id,
                    allergen_id=allergen.id,
                )
            )

    assert error.value.orig.sqlstate == "23505"


def test_postgres_rejects_a_duplicate_menu_dish(session):
    restaurant = make_restaurant(session)
    category = make_category(session, restaurant)
    dish = make_dish(session, restaurant, category)
    collection = make_collection(session, restaurant)
    menu = make_menu(session, collection)

    session.add(MenuDish(menu_id=menu.id, dish_id=dish.id, role="main"))
    session.flush()

    with pytest.raises(IntegrityError) as error:
        with session.begin_nested():
            session.execute(
                insert(MenuDish).values(
                    menu_id=menu.id,
                    dish_id=dish.id,
                    role="dessert",
                )
            )

    assert error.value.orig.sqlstate == "23505"


def test_postgres_rejects_a_duplicate_collection_name_per_restaurant(session):
    restaurant = make_restaurant(session)
    make_collection(session, restaurant, name="Diario")

    with pytest.raises(IntegrityError) as error:
        with session.begin_nested():
            session.execute(
                insert(MenuCollection).values(
                    restaurant_id=restaurant.id,
                    name="Diario",
                    type="fixed",
                )
            )

    assert error.value.orig.sqlstate == "23505"


def test_postgres_rejects_a_duplicate_menu_name_per_collection(session):
    restaurant = make_restaurant(session)
    collection = make_collection(session, restaurant)
    make_menu(session, collection, name="Menú del día")

    with pytest.raises(IntegrityError) as error:
        with session.begin_nested():
            session.execute(
                insert(Menu).values(
                    collection_id=collection.id,
                    name="Menú del día",
                    own_price=Decimal("18.00"),
                )
            )

    assert error.value.orig.sqlstate == "23505"


def test_postgres_cascades_associations_when_a_dish_is_deleted(session):
    restaurant = make_restaurant(session)
    category = make_category(session, restaurant)
    dish = make_dish(session, restaurant, category)
    allergen = Allergen(code="contract-gluten", name="Gluten")
    session.add(allergen)
    session.flush()
    session.add(DishAllergen(dish_id=dish.id, allergen_id=allergen.id))

    collection = make_collection(session, restaurant)
    menu = make_menu(session, collection)
    session.add(MenuDish(menu_id=menu.id, dish_id=dish.id, role="main"))
    session.flush()

    session.execute(delete(Dish).where(Dish.id == dish.id))
    session.flush()

    assert session.scalar(select(func.count()).select_from(DishAllergen)) == 0
    assert session.scalar(select(func.count()).select_from(MenuDish)) == 0


def test_postgres_rejects_deleting_a_restaurant_with_dishes(session):
    restaurant = make_restaurant(session)
    category = make_category(session, restaurant)
    make_dish(session, restaurant, category)

    with pytest.raises(IntegrityError) as error:
        with session.begin_nested():
            session.execute(delete(Restaurant).where(Restaurant.id == restaurant.id))

    assert error.value.orig.sqlstate == "23503"


def test_postgres_rejects_deleting_a_collection_with_menus(session):
    restaurant = make_restaurant(session)
    collection = make_collection(session, restaurant)
    make_menu(session, collection)

    with pytest.raises(IntegrityError) as error:
        with session.begin_nested():
            session.execute(
                delete(MenuCollection).where(MenuCollection.id == collection.id)
            )

    assert error.value.orig.sqlstate == "23503"
