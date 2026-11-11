from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ScheduleCreate(BaseModel):
    period_start: date = Field(
        description="Primer día del periodo (inclusive).", examples=["2026-11-09"]
    )
    period_end: date = Field(
        description="Último día del periodo (inclusive). No puede ser anterior a period_start.",
        examples=["2026-11-15"],
    )
    responsible_id: int = Field(
        gt=0, description="ID del empleado responsable del cuadrante.", examples=[1]
    )

    @model_validator(mode="after")
    def validate_period_dates(self) -> "ScheduleCreate":
        if self.period_start > self.period_end:
            raise ValueError(
                "La fecha de inicio del periodo no puede ser posterior a la fecha de fin."
            )
        return self


class ScheduleUpdate(BaseModel):
    period_start: date | None = None
    period_end: date | None = None
    responsible_id: int | None = Field(default=None, gt=0)

    @model_validator(mode="before")
    @classmethod
    def reject_explicit_nulls(cls, data: object) -> object:
        if isinstance(data, dict):
            nulls = sorted(key for key, value in data.items() if value is None)
            if nulls:
                raise ValueError(f"Estos campos no admiten null: {', '.join(nulls)}")
        return data

    @model_validator(mode="after")
    def validate_period_dates(self) -> "ScheduleUpdate":
        if (
            self.period_start is not None
            and self.period_end is not None
            and self.period_start > self.period_end
        ):
            raise ValueError(
                "La fecha de inicio del periodo no puede ser posterior a la fecha de fin."
            )
        return self


class ScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: int
    period_start: date
    period_end: date
    status: str = Field(description="'borrador' (editable) o 'publicado' (inmutable).")
    responsible_id: int | None = None
    published_at: datetime | None = None

    @field_validator("status", mode="before")
    @classmethod
    def expose_api_status(cls, value: str) -> str:
        """Traduce los estados persistidos a los valores públicos de la API."""
        return {"draft": "borrador", "published": "publicado"}.get(value, value)
