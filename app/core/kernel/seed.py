from sqlalchemy.orm import Session

from app.core.kernel.identity import DEV_RESTAURANT_ID, DEV_USER_ID  # noqa: F401

# TODO: PENDIENTE (CA3): cuando existan los modelos de restaurante y usuario
# TODO: (HU-AUT-02), crear aquí el restaurante DEV_RESTAURANT_ID y el usuario
# TODO: DEV_USER_ID de forma idempotente (comprobar antes de insertar).


def seed_minimum_data(db: Session) -> None:
    """Placeholder: no hace nada hasta que existan los modelos."""
    pass