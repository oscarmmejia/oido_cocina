import sys
from app.core.database_connection import SessionLocal
from app.database.seeders.catalog import seed_allergens


def run_seed():
    db = SessionLocal()
    try:
        allergens = seed_allergens(db)
        print(f"Sembrado completado: {len(allergens)} alérgenos presentes.")
    except Exception as e:
        print(f"Error durante el sembrado: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
