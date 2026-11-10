from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.database.seeders.catalog import (
    CATEGORIES,
    DISHES,
    MENU_COLLECTIONS,
    MENUS,
    TABLES,
)
from app.models import (
    Allergen,
    Category,
    DiningTable,
    Dish,
    DishAllergen,
    Employee,
    Menu,
    MenuCollection,
    MenuDish,
    Restaurant,
)


def seed_categories(
    db: Session,
    restaurant: Restaurant,
) -> dict[str, Category]:
    existing = {
        row.name: row
        for row in db.scalars(
            select(Category).where(Category.restaurant_id == restaurant.id)
        )
    }
    result: dict[str, Category] = {}
    for name, sort_order in CATEGORIES:
        category = existing.get(name)
        if category is None:
            category = Category(
                restaurant_id=restaurant.id,
                name=name,
                sort_order=sort_order,
                is_active=True,
            )
            db.add(category)
            existing[name] = category
        result[name] = category
    db.flush()
    return result


def seed_tables(
    db: Session,
    restaurant: Restaurant,
) -> dict[int, DiningTable]:
    existing = {
        row.number: row
        for row in db.scalars(
            select(DiningTable).where(
                DiningTable.restaurant_id == restaurant.id
            )
        )
    }
    result: dict[int, DiningTable] = {}
    for spec in TABLES:
        number = int(spec["number"])
        table = existing.get(number)
        if table is None:
            table = DiningTable(
                restaurant_id=restaurant.id,
                number=number,
                min_capacity=int(spec["min_capacity"]),
                max_capacity=int(spec["max_capacity"]),
                location=str(spec["location"]),
                is_active=True,
                adjustable_capacity=bool(spec["adjustable_capacity"]),
            )
            db.add(table)
        result[number] = table
    db.flush()
    return result


def seed_dishes(
    db: Session,
    restaurant: Restaurant,
    categories: dict[str, Category],
    allergens: dict[str, Allergen],
) -> dict[str, Dish]:
    existing = {
        row.name: row
        for row in db.scalars(
            select(Dish).where(Dish.restaurant_id == restaurant.id)
        )
    }
    result: dict[str, Dish] = {}
    for spec in DISHES:
        name = str(spec["name"])
        dish = existing.get(name)
        if dish is not None:
            result[name] = dish
            continue

        dish = Dish(
            restaurant_id=restaurant.id,
            category_id=categories[str(spec["category"])].id,
            name=name,
            description=str(spec["description"]),
            price=spec["price"],
            is_active=True,
            is_published=True,
            is_available=True,
        )
        db.add(dish)
        db.flush()
        existing[name] = dish

        for code in spec["allergens"]:
            db.add(
                DishAllergen(
                    dish_id=dish.id,
                    allergen_id=allergens[str(code)].id,
                )
            )
        result[name] = dish
    db.flush()
    return result


def seed_menu_collections(
    db: Session,
    restaurant: Restaurant,
) -> dict[str, MenuCollection]:
    existing = {
        row.name: row
        for row in db.scalars(
            select(MenuCollection).where(
                MenuCollection.restaurant_id == restaurant.id
            )
        )
    }
    result: dict[str, MenuCollection] = {}
    for spec in MENU_COLLECTIONS:
        name = str(spec["name"])
        collection = existing.get(name)
        if collection is None:
            collection = MenuCollection(
                restaurant_id=restaurant.id,
                name=name,
                type=str(spec["type"]),
                valid_from=spec["valid_from"],
                valid_to=spec["valid_to"],
                is_active=True,
            )
            db.add(collection)
        result[name] = collection
    db.flush()
    return result


def seed_menus(
    db: Session,
    collections: dict[str, MenuCollection],
    dishes: dict[str, Dish],
) -> list[Menu]:
    existing = {
        (row.collection_id, row.name): row
        for row in db.scalars(select(Menu))
    }
    result: list[Menu] = []
    for spec in MENUS:
        collection = collections[str(spec["collection"])]
        name = str(spec["name"])
        menu = existing.get((collection.id, name))
        if menu is not None:
            result.append(menu)
            continue

        menu = Menu(
            collection_id=collection.id,
            name=name,
            own_price=spec["own_price"],
            is_active=True,
            is_available=True,
        )
        db.add(menu)
        db.flush()
        existing[(collection.id, name)] = menu

        for dish_name, role, is_required, includes_drink in spec["dishes"]:
            db.add(
                MenuDish(
                    menu_id=menu.id,
                    dish_id=dishes[str(dish_name)].id,
                    role=str(role),
                    is_required=bool(is_required),
                    includes_drink=bool(includes_drink),
                )
            )
        result.append(menu)
    db.flush()
    return result


def reset_demo_data(db: Session, restaurant: Restaurant) -> None:
    menu_ids = select(Menu.id).join(MenuCollection).where(
        MenuCollection.restaurant_id == restaurant.id
    )
    db.execute(delete(MenuDish).where(MenuDish.menu_id.in_(menu_ids)))
    db.execute(
        delete(Menu).where(
            Menu.collection_id.in_(
                select(MenuCollection.id).where(
                    MenuCollection.restaurant_id == restaurant.id
                )
            )
        )
    )
    db.execute(
        delete(MenuCollection).where(
            MenuCollection.restaurant_id == restaurant.id
        )
    )
    dish_ids = select(Dish.id).where(Dish.restaurant_id == restaurant.id)
    db.execute(delete(DishAllergen).where(DishAllergen.dish_id.in_(dish_ids)))
    db.execute(delete(Dish).where(Dish.restaurant_id == restaurant.id))
    db.execute(
        delete(Category).where(Category.restaurant_id == restaurant.id)
    )
    db.execute(
        delete(DiningTable).where(
            DiningTable.restaurant_id == restaurant.id
        )
    )
    db.execute(
        delete(Employee).where(Employee.restaurant_id == restaurant.id)
    )
    db.flush()
