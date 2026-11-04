"""Bootstrap de desarrollo. TEMPORAL: se borra cuando Alembic esté en dev."""

from sqlalchemy import select

from app.core.database_connection import Base, SessionLocal, engine
from app.modules.shared.models.restaurant import DEMO_RESTAURANT_NAME, Restaurant
from app.modules.tables.models.table import DiningTable  # noqa: F401  (registra la tabla en Base)


def bootstrap() -> None:
    """Crea el esquema y siembra los datos mínimos de forma idempotente.

    ``create_all`` solo crea las tablas de los modelos ya importados: los imports de
    arriba son parte del contrato, no decoración.
    """
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        restaurant_id = db.scalar(
            select(Restaurant.id).where(Restaurant.name == DEMO_RESTAURANT_NAME)
        )
        if restaurant_id is None:
            db.add(Restaurant(name=DEMO_RESTAURANT_NAME))
            db.commit()


if __name__ == "__main__":
    bootstrap()
