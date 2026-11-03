"""Importing this package registers every model in Base.metadata (needed by Alembic)."""

from app.models.dishes import Allergen, Category
from app.models.restaurant import OpeningHours, Restaurant, RestaurantSettings
from app.models.users import AuditLog, Permission, Role, RolePermission, User

__all__ = [
    "Allergen",
    "AuditLog",
    "Category",
    "OpeningHours",
    "Permission",
    "Restaurant",
    "RestaurantSettings",
    "Role",
    "RolePermission",
    "User",
]
