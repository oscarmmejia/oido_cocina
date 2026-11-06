from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, model_validator, ConfigDict
import enum


class ShiftType(str, enum.Enum):
    NORMAL = "normal"
    NOCTURNO = "nocturno"
    PARTO = "partido"


class ShiftBase(BaseModel):
    schedule_id: int
    employee_id: int
    start_at: datetime
    end_at: datetime

    @model_validator(mode="after")
    def validate_shift_times(self) -> "ShiftBase":
        if self.end_at <= self.start_at:
            raise ValueError("El fin del turno debe ser posterior al inicio.")
        return self


class ShiftCreate(ShiftBase):
    type: ShiftType = ShiftType.NORMAL


class ShiftUpdate(BaseModel):
    employee_id: Optional[int] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    type: Optional[ShiftType] = None

    @model_validator(mode="after")
    def validate_shift_times(self) -> "ShiftUpdate":
        if self.end_at is not None and self.start_at is not None and self.end_at <= self.start_at:
            raise ValueError("El fin del turno debe ser posterior al inicio.")
        return self


class ShiftRead(ShiftBase):
    id: int
    type: ShiftType
    status: str

    model_config = ConfigDict(from_attributes=True)

class ScheduleBase(BaseModel):
    period_start: date
    period_end: date

    @model_validator(mode="after")
    def validate_period_dates(self) -> "ScheduleBase":

        if self.period_start > self.period_end:
            raise ValueError("La fecha de inicio del periodo no puede ser posterior a la fecha de fin.")
        return self

class ScheduleCreate(ScheduleBase):
    responsible_id: int

class ScheduleResponse(ScheduleBase):
    id: int
    status: str
    responsible_id: int
    published_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ScheduleUpdate(BaseModel):
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    responsible_id: Optional[int] = None

    @model_validator(mode="after")
    def validate_period_dates(self) -> "ScheduleUpdate":
        if self.period_start is not None and self.period_end is not None and self.period_start > self.period_end:
            raise ValueError("La fecha de inicio del periodo no puede ser posterior a la fecha de fin.")
        return self

    model_config = ConfigDict(from_attributes=True)