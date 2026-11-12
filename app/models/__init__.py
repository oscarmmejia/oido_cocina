"""Importing this package registers every model in Base.metadata (needed by Alembic).

Models live in their module (`app/modules/<module>/models/`) or, for now, in this package.
Everything is re-exported here so the rest of the code imports from `app.models`.
"""

from app.models.dishes import Allergen, Category, Dish, DishAllergen
from app.models.menu import Menu, MenuCollection, MenuDish
from app.models.users import AuditLog, Permission, Role, RolePermission, User
from app.modules.settings.models import OpeningHours, Restaurant, RestaurantSettings

__all__ = [
    "Allergen",
    "AuditLog",
    "Category",
    "Dish",
    "DishAllergen",
    "Menu",
    "MenuCollection",
    "MenuDish",
    "OpeningHours",
    "Permission",
    "Restaurant",
    "RestaurantSettings",
    "Role",
    "RolePermission",
    "User",
]
