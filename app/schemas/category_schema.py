from pydantic import BaseModel, ConfigDict, Field, model_validator


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1)
    sort_order: int = Field(default=0, ge=0)


class CategoryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1)
    sort_order: int | None = Field(default=None, ge=0)

    @model_validator(mode="before")
    @classmethod
    def reject_null_values(cls, values):
        if isinstance(values, dict):
            for field, value in values.items():
                if field in {"name", "sort_order"} and value is None:
                    raise ValueError(f"{field} no puede ser null")
        return values


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: int
    name: str
    sort_order: int
    is_active: bool
