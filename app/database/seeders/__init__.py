from typing import Any

from sqlalchemy.orm import Session

from app.database.seeders.catalog import seed_allergens
from app.database.seeders.demo import (
    reset_demo_data,
    seed_categories,
    seed_dishes,
    seed_menu_collections,
    seed_menus,
    seed_tables,
)
from app.database.seeders.security import (
    seed_employees,
    seed_permissions,
    seed_restaurant,
    seed_role_permissions,
    seed_roles,
    seed_users,
)

__all__ = [
    "reset_demo_data",
    "seed_all",
    "seed_demo",
    "seed_minimum",
]


def seed_minimum(db: Session) -> dict[str, Any]:
    """Catálogos y seguridad mínima para que la API arranque."""

    restaurant = seed_restaurant(db)
    permissions = seed_permissions(db)
    roles = seed_roles(db, restaurant)
    seed_role_permissions(db, roles, permissions)
    users = seed_users(db, restaurant, roles)
    allergen_rows = seed_allergens(db)
    allergens = {row.code: row for row in allergen_rows}
    categories = seed_categories(db, restaurant)
    return {
        "restaurant": restaurant,
        "permissions": permissions,
        "roles": roles,
        "users": users,
        "allergens": allergens,
        "categories": categories,
    }


def seed_demo(
    db: Session,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Datos de demostración: mesas, platos, menús y empleados."""

    if context is None:
        context = seed_minimum(db)

    restaurant = context["restaurant"]
    categories = context["categories"]
    allergens = context["allergens"]
    users = context["users"]

    tables = seed_tables(db, restaurant)
    dishes = seed_dishes(db, restaurant, categories, allergens)
    collections = seed_menu_collections(db, restaurant)
    menus = seed_menus(db, collections, dishes)
    employees = seed_employees(db, restaurant, users)
    return {
        **context,
        "tables": tables,
        "dishes": dishes,
        "collections": collections,
        "menus": menus,
        "employees": employees,
    }


def seed_all(db: Session, include_demo: bool = True) -> dict[str, Any]:
    """Ejecuta los seeders en orden y devuelve el contexto creado."""

    context = seed_minimum(db)
    if include_demo:
        context = seed_demo(db, context)
    return context
