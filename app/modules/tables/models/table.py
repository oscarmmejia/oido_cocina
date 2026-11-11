"""Compatibilidad temporal: el modelo vive en ``app.models``."""

from app.models.table_model import (
    LOCATION_BAR,
    LOCATION_EXTERIOR,
    LOCATION_INTERIOR,
    LOCATIONS,
    DiningTable,
)

__all__ = [
    "DiningTable",
    "LOCATION_BAR",
    "LOCATION_EXTERIOR",
    "LOCATION_INTERIOR",
    "LOCATIONS",
]
