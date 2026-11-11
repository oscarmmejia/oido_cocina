"""Esquemas de lectura y actualización de la configuración existente."""

from datetime import time

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RestaurantSettingsResponse(BaseModel):
    """Representación del restaurante; no determina los campos modificables."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    time_zone: str
    is_active: bool
    courtesy_minutes: int
    slot_minutes: int
    min_break_between_shifts: int | None
    day_of_week: int | None
    period: str | None
    open_time: time | None
    close_time: time | None
    kitchen_close_time: time | None
    direction: str | None


class RestaurantSettingsUpdate(BaseModel):
    """Campos autorizados para PATCH, con las restricciones de Restaurant."""

    model_config = ConfigDict(extra="forbid")

    time_zone: str | None = Field(default=None, max_length=64)
    courtesy_minutes: int | None = Field(default=None, ge=0)
    slot_minutes: int | None = Field(default=None, gt=0)
    min_break_between_shifts: int | None = Field(default=None, ge=0)
    day_of_week: int | None = Field(default=None, ge=1, le=7)
    period: str | None = Field(default=None, max_length=16)
    open_time: time | None = None
    close_time: time | None = None
    kitchen_close_time: time | None = None

    @field_validator("time_zone", "courtesy_minutes", "slot_minutes")
    @classmethod
    def reject_explicit_null(cls, value: str | int | None) -> str | int:
        if value is None:
            raise ValueError("El campo no admite null")
        return value
