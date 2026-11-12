from app.modules.settings.models.opening_hours import OpeningHours
from app.modules.settings.models.restaurant import Restaurant
from app.modules.settings.models.restaurant_settings import RestaurantSettings

# Registers User and the menu models in the same declarative registry so the
# string-based relationships on Restaurant resolve even when this package is
# imported directly (for example, a test importing Restaurant on its own).
from app.models.dishes import Category, Dish  # noqa: E402,F401
from app.models.menu import MenuCollection  # noqa: E402,F401
from app.models.users import User  # noqa: E402,F401

__all__ = ["OpeningHours", "Restaurant", "RestaurantSettings"]
