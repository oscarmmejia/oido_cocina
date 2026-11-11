"""API de cuadrantes sobre el modelo canónico de ``app.models``.

``ScheduleStatus`` conserva los valores que expone la API (``borrador`` y
``publicado``). El modelo compartido almacena ``draft`` y ``published``; la
traducción se hace en la capa de servicio/esquema.
"""

from enum import StrEnum

from app.models.schedule_model import Schedule


class ScheduleStatus(StrEnum):
    BORRADOR = "borrador"
    PUBLICADO = "publicado"


__all__ = ["Schedule", "ScheduleStatus"]
