"""Lectura y actualización de la configuración del restaurante."""

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors.codes import ErrorCode
from app.core.kernel.errors import AppError
from app.modules.settings.models.restaurant import Restaurant
from app.modules.settings.schemas import RestaurantSettingsUpdate


def get_restaurant_settings(db: Session, restaurant_id: int) -> Restaurant:
    """Devuelve el restaurante con su configuración o indica que no existe."""
    restaurant = db.get(Restaurant, restaurant_id)
    if restaurant is None:
        raise AppError(
            code=ErrorCode.NOT_FOUND.value,
            message=f"El restaurante con identificador {restaurant_id} no existe",
            status_code=404,
        )
    return restaurant


def update_restaurant_settings(
    db: Session, restaurant_id: int, settings: RestaurantSettingsUpdate
) -> Restaurant:
    """Actualiza los campos enviados para un restaurante previamente autorizado.

    El llamante debe obtener restaurant_id de la identidad autenticada.
    Este servicio no sustituye la comprobación de permisos de la futura ruta.
    """
    restaurant = get_restaurant_settings(db, restaurant_id)
    changes = settings.model_dump(exclude_unset=True)
    if not changes:
        return restaurant

    for field, value in changes.items():
        setattr(restaurant, field, value)

    try:
        db.commit()
        db.refresh(restaurant)
    except SQLAlchemyError:
        db.rollback()
        raise

    return restaurant
