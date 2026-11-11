"""Compatibilidad temporal: ``Employee`` vive en ``app.models.schedule_model``."""

from app.models.schedule_model import Employee

__all__ = ["Employee"]
