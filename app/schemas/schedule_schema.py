from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, model_validator, ConfigDict

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