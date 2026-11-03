from sqlalchemy.orm import Session

from app.database.seeders._helpers import insert_if_missing
from app.models import Allergen, Category

# The 14 EU allergens of mandatory declaration. `code` is the stable natural key.
ALLERGENS = [
    ("gluten", "Gluten"),
    ("crustaceans", "Crustáceos"),
    ("eggs", "Huevo"),
    ("fish", "Pescado"),
    ("peanuts", "Cacahuete"),
    ("soybeans", "Soja"),
    ("milk", "Leche"),
    ("tree_nuts", "Frutos de cáscara"),
    ("celery", "Apio"),
    ("mustard", "Mostaza"),
    ("sesame", "Sésamo"),
    ("sulphites", "Sulfitos"),
    ("lupin", "Altramuces"),
    ("molluscs", "Moluscos"),
]

# Initial categories, in carta order. Natural key: (restaurant_id, name).
CATEGORIES = ["Entrantes", "Primeros", "Segundos", "Bebidas", "Postres"]


def seed_allergens(session: Session) -> dict[str, int]:
    rows = [{"code": code, "name": name} for code, name in ALLERGENS]
    return {"allergens": insert_if_missing(session, Allergen, rows, natural_key=["code"])}


def seed_categories(session: Session, restaurant_id: int) -> dict[str, int]:
    rows = [
        {"restaurant_id": restaurant_id, "name": name, "sort_order": position}
        for position, name in enumerate(CATEGORIES, start=1)
    ]
    return {
        "categories": insert_if_missing(
            session, Category, rows, natural_key=["restaurant_id", "name"]
        )
    }
