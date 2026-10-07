"""Pydantic schemas for Products and Visual Aids."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductVisualAidResponse(BaseModel):
    """Visual aid slide response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    title: str
    image_url: str | None = None
    slide_order: int
    key_talk_points: str | None = None
    created_at: datetime


class ProductResponse(BaseModel):
    """Full pharmaceutical product response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    brand: str
    category: str
    composition: str | None = None
    strength: str | None = None
    packaging: str
    mrp: float
    ptr: float
    pts: float
    gst_rate: float
    indications: str | None = None
    dosage_guidelines: str | None = None
    is_sample_available: bool
    is_active: bool
    visual_aids: list[ProductVisualAidResponse] = []
    created_at: datetime
    updated_at: datetime


class ProductCreate(BaseModel):
    """Payload to add a new product."""

    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=150)
    brand: str = Field(default="Mediate Pharma")
    category: str = Field(...)
    composition: str | None = None
    strength: str | None = None
    packaging: str = Field(default="10x10 Tablets")
    mrp: float = Field(ge=0)
    ptr: float = Field(ge=0)
    pts: float = Field(ge=0)
    gst_rate: float = Field(default=12.0)
    indications: str | None = None
    dosage_guidelines: str | None = None
    is_sample_available: bool = True


class VisualAidCreate(BaseModel):
    """Payload to add visual aid slide."""

    title: str = Field(..., min_length=2, max_length=150)
    image_url: str | None = None
    slide_order: int = Field(default=1, ge=1)
    key_talk_points: str | None = None
