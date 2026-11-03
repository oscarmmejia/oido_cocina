from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TableLocation(str, Enum):
    interior = "interior"
    exterior = "exterior"


class TableCreate(BaseModel):
    # TEMPORAL: mientras no exista autenticación, el restaurante se puede indicar a mano.
    restaurant_id: int | None = None
    number: int
    min_capacity: int = Field(ge=1)
    max_capacity: int
    location: TableLocation
    is_active: bool = True
    adjustable_capacity: bool = False

    @model_validator(mode="after")
    def check_capacity_range(self) -> "TableCreate":
        if self.max_capacity < self.min_capacity:
            raise ValueError("max_capacity no puede ser menor que min_capacity")
        return self


class TableUpdate(BaseModel):
    number: int | None = None
    min_capacity: int | None = Field(default=None, ge=1)
    max_capacity: int | None = None
    location: TableLocation | None = None
    is_active: bool | None = None
    adjustable_capacity: bool | None = None


class TableRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: int
    number: int
    min_capacity: int
    max_capacity: int
    location: TableLocation
    is_active: bool
    adjustable_capacity: bool
