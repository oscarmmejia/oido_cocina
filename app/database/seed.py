"""CLI de seeders idempotentes.

Uso:
    python -m app.database.seed
    python -m app.database.seed --no-demo
    python -m app.database.seed --reset
"""

from __future__ import annotations

import argparse
import sys

from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.core.database_connection import engine
from app.database.seeders import reset_demo_data, seed_all
from app.database.seeders.catalog import DEMO_RESTAURANT_ID
from app.database.seeders.security import seed_restaurant
from app.models import (
    Allergen,
    Category,
    DiningTable,
    Dish,
    Employee,
    Menu,
    MenuCollection,
    Permission,
    Role,
    User,
)

REQUIRED_TABLES = {
    "allergens",
    "categories",
    "dishes",
    "dish_allergens",
    "employees",
    "menu_collections",
    "menu_dishes",
    "menus",
    "permissions",
    "restaurant",
    "role_permissions",
    "roles",
    "tables",
    "users",
}


def _check_schema() -> bool:
    existing = set(inspect(engine).get_table_names())
    missing = sorted(REQUIRED_TABLES - existing)
    if missing:
        print(
            "Faltan tablas: "
            + ", ".join(missing)
            + ". Ejecuta: python -m alembic upgrade head"
        )
        return False
    return True


def _counts(db: Session) -> dict[str, int]:
    return {
        "alérgenos": len(db.scalars(select(Allergen)).all()),
        "categorías": len(db.scalars(select(Category)).all()),
        "mesas": len(db.scalars(select(DiningTable)).all()),
        "platos": len(db.scalars(select(Dish)).all()),
        "colecciones": len(db.scalars(select(MenuCollection)).all()),
        "menús": len(db.scalars(select(Menu)).all()),
        "empleados": len(db.scalars(select(Employee)).all()),
        "permisos": len(db.scalars(select(Permission)).all()),
        "roles": len(db.scalars(select(Role)).all()),
        "usuarios": len(db.scalars(select(User)).all()),
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Carga los datos iniciales y de demostración."
    )
    parser.add_argument(
        "--no-demo",
        action="store_true",
        help="carga solo catálogos, restaurante, roles y permisos",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="borra los datos demo del restaurante antes de sembrar",
    )
    args = parser.parse_args()

    if not _check_schema():
        return 1

    with Session(engine) as db:
        try:
            if args.reset:
                restaurant = seed_restaurant(db)
                reset_demo_data(db, restaurant)
                db.flush()

            seed_all(db, include_demo=not args.no_demo)
            db.commit()
            counts = _counts(db)
        except Exception:
            db.rollback()
            raise

    print(f"Seed completado para el restaurante {DEMO_RESTAURANT_ID}.")
    print(" | ".join(f"{name}: {value}" for name, value in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
