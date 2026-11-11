from datetime import time
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.kernel.identity import DEV_RESTAURANT_ID
from app.core.permissions import (
    ROLE_ADMIN,
    ROLE_HEAD_CHEF,
    ROLE_MANAGER,
    ROLE_SUPERADMIN,
    ROLE_WAITER,
)
from app.models.allergen_model import Allergen

DEMO_RESTAURANT_ID = DEV_RESTAURANT_ID
DEMO_RESTAURANT_NAME = "Oido Cocina"
DEMO_TIME_ZONE = "Europe/Madrid"
DEMO_PASSWORD = "Demo1234!"
SUPERADMIN_EMAIL = "superadmin@oidocina.local"

# Catálogo oficial de los catorce alérgenos de declaración obligatoria en la UE.
EU_ALLERGENS: list[dict[str, str]] = [
    {"code": "GLUTEN", "name": "Cereales que contienen gluten"},
    {"code": "CRUSTACEOS", "name": "Crustáceos y productos a base de crustáceos"},
    {"code": "HUEVOS", "name": "Huevos y productos a base de huevo"},
    {"code": "PESCADO", "name": "Pescado y productos a base de pescado"},
    {"code": "CACAHUETES", "name": "Cacahuetes y productos a base de cacahuetes"},
    {"code": "SOJA", "name": "Soja y productos a base de soja"},
    {"code": "LACTEOS", "name": "Leche y sus derivados (incluida la lactosa)"},
    {"code": "FRUTOS_DE_CASCARA", "name": "Frutos de cáscara"},
    {"code": "APIO", "name": "Apio y productos derivados"},
    {"code": "MOSTAZA", "name": "Mostaza y productos derivados"},
    {"code": "SESAMO", "name": "Granos de sésamo y productos derivados"},
    {"code": "SULFITOS", "name": "Dióxido de azufre y sulfitos"},
    {"code": "ALTRAMUCES", "name": "Altramuces y productos a base de altramuces"},
    {"code": "MOLUSCOS", "name": "Moluscos y productos a base de moluscos"},
]

# Horario demo por defecto. El equipo acordó que estos campos viven en
# restaurant, no en una tabla opening_hours.
DEFAULT_SCHEDULE: dict[str, object] = {
    "day_of_week": 1,
    "period": "morning",
    "open_time": time(13, 0),
    "close_time": time(16, 0),
    "kitchen_close_time": time(15, 30),
}

CATEGORIES: tuple[tuple[str, int], ...] = (
    ("Entrantes", 1),
    ("Principales", 2),
    ("Postres", 3),
)

TABLES: tuple[dict[str, object], ...] = (
    {
        "number": 1,
        "min_capacity": 2,
        "max_capacity": 4,
        "location": "interior",
        "adjustable_capacity": True,
    },
    {
        "number": 2,
        "min_capacity": 2,
        "max_capacity": 4,
        "location": "interior",
        "adjustable_capacity": False,
    },
    {
        "number": 3,
        "min_capacity": 4,
        "max_capacity": 6,
        "location": "interior",
        "adjustable_capacity": False,
    },
    {
        "number": 4,
        "min_capacity": 2,
        "max_capacity": 2,
        "location": "exterior",
        "adjustable_capacity": False,
    },
    {
        "number": 5,
        "min_capacity": 4,
        "max_capacity": 8,
        "location": "exterior",
        "adjustable_capacity": True,
    },
    {
        "number": 6,
        "min_capacity": 1,
        "max_capacity": 2,
        "location": "bar",
        "adjustable_capacity": False,
    },
)

DISHES: tuple[dict[str, object], ...] = (
    {
        "name": "Croquetas de jamón ibérico",
        "category": "Entrantes",
        "description": "Seis croquetas cremosas de jamón ibérico.",
        "price": Decimal("7.50"),
        "allergens": ("GLUTEN", "LACTEOS", "HUEVOS"),
    },
    {
        "name": "Ensalada de burrata",
        "category": "Entrantes",
        "description": "Burrata, tomate cherry, albahaca y aceite de oliva.",
        "price": Decimal("9.90"),
        "allergens": ("LACTEOS",),
    },
    {
        "name": "Paella de marisco",
        "category": "Principales",
        "description": "Arroz bomba, gambón, mejillón y calamar.",
        "price": Decimal("18.50"),
        "allergens": ("CRUSTACEOS", "MOLUSCOS", "PESCADO"),
    },
    {
        "name": "Solomillo a la pimienta",
        "category": "Principales",
        "description": "Solomillo de ternera con salsa de pimienta y patata.",
        "price": Decimal("22.00"),
        "allergens": ("LACTEOS", "MOSTAZA"),
    },
    {
        "name": "Tarta de queso al horno",
        "category": "Postres",
        "description": "Tarta cremosa con base de galleta y mermelada.",
        "price": Decimal("6.50"),
        "allergens": ("LACTEOS", "HUEVOS", "GLUTEN"),
    },
)

MENU_COLLECTIONS: tuple[dict[str, object], ...] = (
    {
        "name": "Menú del día",
        "type": "daily",
        "valid_from": None,
        "valid_to": None,
    },
    {
        "name": "Carta de temporada",
        "type": "seasonal",
        "valid_from": None,
        "valid_to": None,
    },
)

MENUS: tuple[dict[str, object], ...] = (
    {
        "collection": "Menú del día",
        "name": "Menú del día completo",
        "own_price": Decimal("15.90"),
        "dishes": (
            ("Croquetas de jamón ibérico", "starter", True, False),
            ("Paella de marisco", "main", True, False),
            ("Tarta de queso al horno", "dessert", True, False),
            ("Ensalada de burrata", "drink", False, True),
        ),
    },
    {
        "collection": "Carta de temporada",
        "name": "Menú degustación",
        "own_price": Decimal("28.00"),
        "dishes": (
            ("Ensalada de burrata", "starter", True, False),
            ("Solomillo a la pimienta", "main", True, False),
            ("Tarta de queso al horno", "dessert", True, False),
        ),
    },
)

USERS: tuple[dict[str, str], ...] = (
    {
        "email": SUPERADMIN_EMAIL,
        "name": "Superadministrador Demo",
        "role": ROLE_SUPERADMIN,
        "phone": "600000001",
        "job_position": "manager",
    },
    {
        "email": "admin@oidocina.local",
        "name": "Administrador Demo",
        "role": ROLE_ADMIN,
        "phone": "600000002",
        "job_position": "manager",
    },
    {
        "email": "gerente@oidocina.local",
        "name": "Gerente Demo",
        "role": ROLE_MANAGER,
        "phone": "600000003",
        "job_position": "manager",
    },
    {
        "email": "jefecocina@oidocina.local",
        "name": "Jefe de Cocina Demo",
        "role": ROLE_HEAD_CHEF,
        "phone": "600000004",
        "job_position": "cook",
    },
    {
        "email": "camarero@oidocina.local",
        "name": "Camarero Demo",
        "role": ROLE_WAITER,
        "phone": "600000005",
        "job_position": "waiter",
    },
)


def seed_allergens(db: Session) -> list[Allergen]:
    """Carga el catálogo oficial de alérgenos de forma idempotente."""

    existing = {row.code: row for row in db.scalars(select(Allergen))}

    # Compatibilidad con el código usado antes de unificar el catálogo.
    legacy = existing.get("FRUTOS_SECOS")
    if legacy is not None and "FRUTOS_DE_CASCARA" not in existing:
        legacy.code = "FRUTOS_DE_CASCARA"
        existing["FRUTOS_DE_CASCARA"] = existing.pop("FRUTOS_SECOS")

    seeded: list[Allergen] = []
    for item in EU_ALLERGENS:
        allergen = existing.get(item["code"])
        if allergen is None:
            allergen = Allergen(code=item["code"], name=item["name"])
            db.add(allergen)
            existing[item["code"]] = allergen
        else:
            allergen.name = item["name"]
        seeded.append(allergen)

    db.flush()
    return seeded
