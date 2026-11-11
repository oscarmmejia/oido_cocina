"""Lectura y actualización de la configuración del restaurante."""

from datetime import time

from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors.codes import ErrorCode
from app.core.kernel.errors import AppError
from app.models import Restaurant
from app.modules.settings.schemas import RestaurantSettingsUpdate


def get_restaurant_settings(
    db: Session, restaurant_id: int, *, for_update: bool = False
) -> Restaurant:
    """Obtiene la configuración, con bloqueo y recarga opcionales para actualizar."""
    if for_update:
        restaurant = db.get(
            Restaurant, restaurant_id, with_for_update=True, populate_existing=True
        )
    else:
        restaurant = db.get(Restaurant, restaurant_id)
    if restaurant is None:
        raise AppError(
            code=ErrorCode.NOT_FOUND.value,
            message=f"El restaurante con identificador {restaurant_id} no existe",
            status_code=404,
        )
    return restaurant


def _minutes_since_midnight(value: time) -> float:
    """Minutos de hora local, conservando segundos y microsegundos."""
    return (
        value.hour * 60
        + value.minute
        + (value.second + value.microsecond / 1_000_000) / 60
    )


def _validate_schedule(settings: RestaurantSettingsUpdate) -> None:
    """Valida una jornada inferior a 24 horas con un único cruce de medianoche.

    Un cierre anterior a la apertura corresponde al día siguiente. Apertura y
    cierre iguales no representan un servicio de 24 horas. Sin apertura, ambos
    cierres se comparan dentro del mismo día. Los valores nulos se conservan.
    """
    if settings.close_time is None:
        return

    closing = _minutes_since_midnight(settings.close_time)
    opening = (
        _minutes_since_midnight(settings.open_time)
        if settings.open_time is not None
        else None
    )
    if opening is not None:
        if closing == opening:
            raise AppError(
                ErrorCode.VALIDATION_ERROR.value,
                "La hora de cierre debe ser posterior a la apertura; no pueden coincidir.",
                422,
            )
        if closing < opening:
            closing += 24 * 60

    if settings.kitchen_close_time is not None:
        kitchen_closing = _minutes_since_midnight(settings.kitchen_close_time)
        if opening is not None and kitchen_closing < opening:
            kitchen_closing += 24 * 60
        if kitchen_closing > closing:
            raise AppError(
                ErrorCode.VALIDATION_ERROR.value,
                "El cierre de cocina no puede ser posterior al cierre del local.",
                422,
            )


def update_restaurant_settings(
    db: Session, restaurant_id: int, settings: RestaurantSettingsUpdate
) -> Restaurant:
    """Actualiza los campos enviados para un restaurante previamente autorizado.

    El llamante debe obtener restaurant_id de la identidad autenticada.
    Este servicio no sustituye la comprobación de permisos de la futura ruta.
    """
    restaurant = get_restaurant_settings(db, restaurant_id, for_update=True)
    changes = settings.model_dump(exclude_unset=True)

    # Validar una copia completa antes de tocar atributos del objeto ORM.
    candidate_data = {
        field: getattr(restaurant, field)
        for field in RestaurantSettingsUpdate.model_fields
    }
    candidate_data.update(changes)
    try:
        candidate = RestaurantSettingsUpdate.model_validate(candidate_data)
    except ValidationError as error:
        fields = ", ".join(str(item["loc"][0]) for item in error.errors())
        raise AppError(
            ErrorCode.VALIDATION_ERROR.value,
            f"La configuración resultante contiene valores no válidos: {fields}.",
            422,
        ) from error
    _validate_schedule(candidate)

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
