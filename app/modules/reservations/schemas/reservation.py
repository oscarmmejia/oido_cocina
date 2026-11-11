"""Esquemas Pydantic del agregado de reserva.

Los nombres de campo siguen el esquema compartido de HU-AUT-02:
``phone``, ``email``, ``previous_status``, ``new_status``, etc.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import ReservationStatus, ReservationTableStatus


class ReservationCreate(BaseModel):
    # end_at, status, created_by_user_id, created_at y updated_at los fija
    # el servidor: no forman parte del contrato de entrada.
    model_config = ConfigDict(extra="forbid")

    customer_name: str = Field(min_length=1, max_length=150)
    phone: str = Field(min_length=1, max_length=30)
    email: str | None = Field(default=None, max_length=255)
    party_size: int = Field(ge=1)
    start_at: datetime
    table_ids: list[int] = Field(default_factory=list)
    combination_id: int | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_table_selection(self) -> "ReservationCreate":
        if not self.table_ids and self.combination_id is None:
            raise ValueError("Debes indicar table_ids o combination_id")
        if len(self.table_ids) != len(set(self.table_ids)):
            raise ValueError("table_ids no puede contener mesas repetidas")
        return self


class ReservationUpdate(BaseModel):
    # Los campos derivados o inmutables se rechazan explícitamente con 422.
    model_config = ConfigDict(extra="forbid")

    customer_name: str | None = Field(default=None, min_length=1, max_length=150)
    phone: str | None = Field(default=None, min_length=1, max_length=30)
    email: str | None = Field(default=None, max_length=255)
    party_size: int | None = Field(default=None, ge=1)
    start_at: datetime | None = None
    table_ids: list[int] | None = None
    combination_id: int | None = None
    notes: str | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_explicit_nulls(cls, data: object) -> object:
        if isinstance(data, dict):
            required = {"customer_name", "phone", "party_size", "start_at", "table_ids"}
            nulls = sorted(
                key for key, value in data.items() if value is None and key in required
            )
            if nulls:
                raise ValueError(f"Estos campos no admiten null: {', '.join(nulls)}")
        return data

    @model_validator(mode="after")
    def validate_table_ids(self) -> "ReservationUpdate":
        if self.table_ids is not None and len(self.table_ids) != len(
            set(self.table_ids)
        ):
            raise ValueError("table_ids no puede contener mesas repetidas")
        return self


class ReservationTableCreate(BaseModel):
    table_id: int = Field(gt=0)
    start_at: datetime
    end_at: datetime
    status: ReservationTableStatus = ReservationTableStatus.ACTIVE

    @model_validator(mode="after")
    def validate_time_range(self) -> "ReservationTableCreate":
        if self.end_at <= self.start_at:
            raise ValueError("end_at debe ser posterior a start_at")
        return self


class ReservationTableRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reservation_id: int
    table_id: int
    start_at: datetime
    end_at: datetime
    status: ReservationTableStatus


class ReservationStatusHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reservation_id: int
    previous_status: ReservationStatus | None
    new_status: ReservationStatus
    changed_by_user_id: int | None
    reason: str | None
    changed_at: datetime


class ReservationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: int
    created_by_user_id: int | None
    combination_id: int | None
    customer_name: str
    phone: str
    email: str | None
    party_size: int
    start_at: datetime
    end_at: datetime
    status: ReservationStatus
    notes: str | None
    created_at: datetime
    updated_at: datetime


class ReservationDetailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reservation: ReservationRead
    tables: list[ReservationTableRead]
    history: list[ReservationStatusHistoryRead]


class ReservationList(BaseModel):
    items: list[ReservationRead]
    total: int
    page: int
    page_size: int


class ReservationTransition(BaseModel):
    reason: str | None = Field(default=None, max_length=255)
