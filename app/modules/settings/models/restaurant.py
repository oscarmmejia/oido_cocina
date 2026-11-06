"""Compatibilidad temporal: el modelo vive en ``app.models``."""

from app.models.restaurant_model import OpeningHours, Restaurant

__all__ = ["OpeningHours", "Restaurant"]
