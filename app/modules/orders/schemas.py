"""Pydantic schemas for Orders and Order Items."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class OrderItemCreate(BaseModel):
    """Payload to add an item to an order."""

    product_id: int
    quantity: int = Field(..., ge=1)
    unit_price: float = Field(..., ge=0)
    free_quantity: int = Field(default=0, ge=0)


class OrderItemResponse(BaseModel):
    """Line item representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    product_id: int
    product_name: str | None = None
    product_code: str | None = None
    quantity: int
    unit_price: float
    total_price: float
    free_quantity: int


class OrderCreate(BaseModel):
    """Payload to create and book a commercial order."""

    customer_type: str = Field(..., description="CHEMIST or STOCKIST")
    customer_id: int
    expected_delivery_date: date | None = None
    payment_terms: str | None = "Net 30 Days"
    notes: str | None = None
    items: list[OrderItemCreate] = Field(..., min_length=1)


class OrderResponse(BaseModel):
    """Full order details response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: str
    customer_type: str
    customer_id: int
    customer_name: str | None = None
    user_id: int
    user_name: str | None = None
    total_amount: float
    status: str
    expected_delivery_date: date | None = None
    payment_terms: str | None = None
    notes: str | None = None
    items: list[OrderItemResponse] = []
    created_at: datetime
    updated_at: datetime
