"""Pydantic schemas for Company Profile."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CompanyProfileResponse(BaseModel):
    """Company profile overview response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    company_name: str
    company_code: str
    area: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    phone_no: str | None = None
    mobile_no: str | None = None
    email: str | None = None
    website: str | None = None
    logo_file_id: int | None = None
    signature_file_id: int | None = None
    logo_url: str | None = None
    signature_url: str | None = None
    is_active: bool
    updated_at: datetime


class CompanyProfileUpdateRequest(BaseModel):
    """Payload to update company profile."""

    company_name: str = Field(..., max_length=150)
    company_code: str = Field(..., max_length=50)
    area: str | None = Field(default=None, max_length=100)
    address: str | None = None
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    pincode: str | None = Field(default=None, max_length=20)
    phone_no: str | None = Field(default=None, max_length=50)
    mobile_no: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=100)
    website: str | None = Field(default=None, max_length=100)
    logo_file_id: int | None = None
    signature_file_id: int | None = None
