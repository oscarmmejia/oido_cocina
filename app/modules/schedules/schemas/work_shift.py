from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import ShiftStatus, ShiftType


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
    type: ShiftType = Field(
        default=ShiftType.MORNING,
        description="Tipo de turno.",
        examples=["morning"],
    )

    @model_validator(mode="after")
    def validate_times(self) -> "WorkShiftCreate":
        if self.starts_at.tzinfo is None or self.ends_at.tzinfo is None:
            raise ValueError("Las fechas deben incluir zona horaria, por ejemplo +01:00.")
        if self.ends_at <= self.starts_at:
            raise ValueError("El fin del turno debe ser posterior al inicio.")
        return self


class WorkShiftUpdate(BaseModel):
    employee_id: int | None = Field(default=None, gt=0)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    type: ShiftType | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_explicit_nulls(cls, data: object) -> object:
        if isinstance(data, dict):
            nulls = sorted(key for key, value in data.items() if value is None)
            if nulls:
                raise ValueError(f"Estos campos no admiten null: {', '.join(nulls)}")
        return data

    @model_validator(mode="after")
    def validate_times(self) -> "WorkShiftUpdate":
        for value in (self.starts_at, self.ends_at):
            if value is not None and value.tzinfo is None:
                raise ValueError(
                    "Las fechas deben incluir zona horaria, por ejemplo +01:00."
                )
        if (
            self.starts_at is not None
            and self.ends_at is not None
            and self.ends_at <= self.starts_at
        ):
            raise ValueError("El fin del turno debe ser posterior al inicio.")
        return self


class WorkShiftRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    schedule_id: int
    employee_id: int
    starts_at: datetime = Field(validation_alias="start_at")
    ends_at: datetime = Field(validation_alias="end_at")
    type: ShiftType
    status: ShiftStatus
