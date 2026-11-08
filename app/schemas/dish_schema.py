from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DishCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    price: Decimal = Field(ge=0, decimal_places=2)
    category_id: int
    allergen_ids: list[int] = Field(default_factory=list)


class DishUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    category_id: int | None = None
    allergen_ids: list[int] | None = None
    is_published: bool | None = None
    is_available: bool | None = None

    @field_validator(
        "name",
        "category_id",
        "price",
        "allergen_ids",
        mode="before"
    )
    @classmethod
    def reject_null_required_fields(cls, value):
        if value is None:
            raise ValueError("Este campo no puede ser null")
        return value


class DishResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: int
    category_id: int
    name: str
    description: str | None
    price: Decimal
    is_active: bool
    is_published: bool
    is_available: bool
    allergen_ids: list[int] = Field(default_factory=list)


class DishPublicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    name: str
    description: str | None
    price: Decimal
    is_available: bool
    allergen_ids: list[int] = Field(default_factory=list)


class PaginatedDishesResponse(BaseModel):
    items: list[DishPublicResponse]
    total: int
    page: int
    page_size: int
    total_pages: int