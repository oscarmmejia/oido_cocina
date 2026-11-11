from pydantic import BaseModel, ConfigDict, Field


class EmployeeCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    job_position: str = Field(min_length=1, max_length=50)
    user_id: int | None = None


class EmployeeUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    job_position: str | None = Field(default=None, min_length=1, max_length=50)
    user_id: int | None = None


class EmployeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: int
    user_id: int | None
    full_name: str
    job_position: str
    is_active: bool