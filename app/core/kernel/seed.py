from sqlalchemy.orm import Session

from app.database.seeders import seed_minimum


def seed_minimum_data(db: Session) -> None:
    """Siembra los datos mínimos que necesita el kernel.

    Es idempotente: se puede invocar en cada arranque sin duplicar filas.
    """

    seed_minimum(db)
