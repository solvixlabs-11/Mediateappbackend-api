"""Pydantic schemas for Financial Year master."""

from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field, model_validator


class FinancialYearBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Display name e.g. FY 2026-2027")
    code: str = Field(..., min_length=4, max_length=20, description="Code e.g. 2026-2027")
    start_date: date = Field(..., description="Start date of fiscal year e.g. 2026-04-01")
    end_date: date = Field(..., description="End date of fiscal year e.g. 2027-03-31")
    is_current: bool = Field(False, description="Flag indicating active current fiscal year")
    is_active: bool = Field(True, description="Active status")
    description: str | None = Field(None, max_length=255, description="Notes / description")

    @model_validator(mode="after")
    def validate_dates(self) -> "FinancialYearBase":
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be strictly before end_date")
        return self


class FinancialYearCreate(FinancialYearBase):
    pass


class FinancialYearUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)
    code: str | None = Field(None, min_length=4, max_length=20)
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool | None = None
    is_active: bool | None = None
    description: str | None = Field(None, max_length=255)

    @model_validator(mode="after")
    def validate_dates(self) -> "FinancialYearUpdate":
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValueError("start_date must be strictly before end_date")
        return self


class FinancialYearResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    start_date: date
    end_date: date
    is_current: bool
    is_active: bool
    description: str | None = None
    created_at: datetime
    updated_at: datetime


class FinancialYearListResponse(BaseModel):
    items: list[FinancialYearResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
