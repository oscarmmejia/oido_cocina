from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class ScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: int
    period_start: date
    period_end: date
    status: str = Field(description="'borrador' (editable) o 'publicado' (inmutable).")
    responsible_id: int
    published_at: datetime | None = None
