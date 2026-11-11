"""Compatibilidad temporal: el modelo vive en ``app.models``."""

from app.models.restaurant_model import Restaurant

__all__ = ["Restaurant"]
