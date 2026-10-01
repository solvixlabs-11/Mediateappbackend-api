"""Pydantic schemas for Master items, States, Cities, and Areas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MasterItemResponse(BaseModel):
    """Generic business master item response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    code: str
    name: str
    description: str | None = None
    sort_order: int
    is_active: bool
    created_at: datetime


class MasterItemCreate(BaseModel):
    """Payload to create a generic master item."""

    type: str = Field(..., max_length=50, description="e.g. SPECIALIZATION, CUSTOMER_CATEGORY")
    code: str = Field(..., max_length=50, description="Unique code within type")
    name: str = Field(..., max_length=100)
    description: str | None = Field(default=None, max_length=255)
    sort_order: int = 0


class MasterItemUpdate(BaseModel):
    """Payload to update a generic master item."""

    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    sort_order: int | None = None
    is_active: bool | None = None


class StateResponse(BaseModel):
    """State / Province response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    is_active: bool


class StateCreate(BaseModel):
    """Payload to create a State."""

    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=10)


class CityResponse(BaseModel):
    """City / District response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    state_id: int
    name: str
    code: str | None = None
    is_active: bool


class CityCreate(BaseModel):
    """Payload to create a City."""

    state_id: int
    name: str = Field(..., max_length=100)
    code: str | None = Field(default=None, max_length=10)


class AreaResponse(BaseModel):
    """Area / Locality response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    city_id: int
    name: str
    pincode: str | None = None
    is_active: bool


class AreaCreate(BaseModel):
    """Payload to create an Area."""

    city_id: int
    name: str = Field(..., max_length=100)
    pincode: str | None = Field(default=None, max_length=10)


class MasterBulkDropdownsResponse(BaseModel):
    """Combined masters response for offline cache & dropdowns."""

    specializations: list[MasterItemResponse]
    categories: list[MasterItemResponse]
    priorities: list[MasterItemResponse]
    states: list[StateResponse]
