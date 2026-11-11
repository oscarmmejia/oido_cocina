from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import MenuCollectionType


def check_validity_range(valid_from: date | None, valid_to: date | None) -> None:
    if valid_from is not None and valid_to is not None and valid_from > valid_to:
        raise ValueError("valid_from no puede ser posterior a valid_to")


class MenuCollectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    type: MenuCollectionType
    valid_from: date | None = None
    valid_to: date | None = None

    @model_validator(mode="after")
    def validate_range(self):
        check_validity_range(self.valid_from, self.valid_to)
        return self


class MenuCollectionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=150)
    type: MenuCollectionType | None = None
    valid_from: date | None = None
    valid_to: date | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_null_values(cls, values):
        if isinstance(values, dict):
            for field in ("name", "type"):
                if field in values and values[field] is None:
                    raise ValueError(f"{field} no puede ser null")
        return values

    @model_validator(mode="after")
    def validate_range(self):
        check_validity_range(self.valid_from, self.valid_to)
        return self


class MenuCollectionStatusUpdate(BaseModel):
    is_active: bool | None = None

    @field_validator("is_active", mode="before")
    @classmethod
    def reject_null_status(cls, value):
        if value is None:
            raise ValueError("Este campo no puede ser null")
        return value


class MenuCollectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: int
    name: str
    type: MenuCollectionType
    valid_from: date | None
    valid_to: date | None
    is_active: bool


class MenuSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    own_price: Decimal
    is_active: bool
    is_available: bool


class MenuCollectionPublicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: MenuCollectionType
    valid_from: date | None
    valid_to: date | None
    menus: list[MenuSummary] = Field(default_factory=list)