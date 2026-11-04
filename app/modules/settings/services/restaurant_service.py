"""Lectura centralizada de la configuración del restaurante."""

from sqlalchemy.orm import Session

from app.core.errors.codes import ErrorCode
from app.core.kernel.errors import AppError
from app.modules.settings.models.restaurant import Restaurant


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
