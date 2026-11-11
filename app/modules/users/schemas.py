from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=150)
    email: EmailStr = Field(max_length=255)
    password: SecretStr = Field(min_length=1)
    role_id: int = Field(gt=0)
    phone_number: str | None = Field(default=None, max_length=30)

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: int
    role_id: int
    name: str
    email: str
    phone_number: str | None
    is_active: bool


class UserPagination(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class UserPage(BaseModel):
    items: list[UserRead]
    total: int
    page: int
    page_size: int


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=150)
    email: EmailStr | None = Field(default=None, max_length=255)
    password: SecretStr | None = Field(default=None, min_length=1)
    phone_number: str | None = Field(default=None, max_length=30)

    @field_validator("name", "email", "password")
    @classmethod
    def reject_explicit_null(cls, value):
        if value is None:
            raise ValueError("El campo no admite null.")
        return value

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, value):
        return UserCreate.normalize_email(value)


class UserRoleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role_id: int = Field(gt=0)


class UserStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_active: bool
