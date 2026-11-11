from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class WorkShiftCreate(BaseModel):
    employee_id: int = Field(
        gt=0,
        description="Empleado asignado. Debe estar activo y pertenecer al restaurante.",
        examples=[3],
    )
    starts_at: datetime = Field(
        description="Inicio del turno con zona horaria (ISO 8601).",
        examples=["2026-11-09T20:00:00+01:00"],
    )
    ends_at: datetime = Field(
        description=(
            "Fin del turno con zona horaria. En un turno nocturno que cruza la "
            "medianoche, es el día siguiente."
        ),
        examples=["2026-11-10T01:00:00+01:00"],
    )

    @model_validator(mode="after")
    def validate_times(self) -> "WorkShiftCreate":
        if self.starts_at.tzinfo is None or self.ends_at.tzinfo is None:
            raise ValueError("Las fechas deben incluir zona horaria, por ejemplo +01:00.")
        if self.ends_at <= self.starts_at:
            raise ValueError("El fin del turno debe ser posterior al inicio.")
        return self


class WorkShiftRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    schedule_id: int
    employee_id: int
    starts_at: datetime = Field(validation_alias="start_at")
    ends_at: datetime = Field(validation_alias="end_at")
