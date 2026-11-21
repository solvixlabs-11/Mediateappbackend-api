"""Pydantic schemas for Sample Inventory & Stock Management."""

from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field


# ==================== SAMPLE INWARD SCHEMAS ====================


class SampleInwardCreate(BaseModel):
    """Payload to record new promotional sample stock inward at HO."""

    challan_number: str = Field(..., description="Supplier or manufacturing inward challan/invoice number")
    inward_date: date = Field(..., description="Date of physical arrival at depot")
    product_id: int = Field(..., description="Target pharmaceutical product ID")
    batch_number: str = Field(..., description="Batch number")
    mfg_date: date | None = Field(None, description="Manufacturing date")
    expiry_date: date = Field(..., description="Expiry date (must be in future)")
    quantity: int = Field(..., gt=0, description="Quantity inwarded in packs/units")
    unit_cost: float = Field(0.0, ge=0.0, description="Unit cost per sample")
    supplier_name: str | None = Field(None, description="Supplier / Manufacturing unit name")
    remarks: str | None = Field(None, description="Inspection or warehouse remarks")


class SampleInwardResponse(BaseModel):
    """Sample inward record output."""

    id: int
    challan_number: str
    inward_date: date
    product_id: int
    product_name: str | None = None
    product_code: str | None = None
    batch_number: str
    mfg_date: date | None = None
    expiry_date: date
    quantity: int
    unit_cost: float
    supplier_name: str | None = None
    remarks: str | None = None
    received_by_id: int | None = None
    received_by_name: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SampleInwardListResponse(BaseModel):
    """Paginated list of sample inward records."""

    items: list[SampleInwardResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==================== SAMPLE ALLOCATION SCHEMAS ====================


class SampleAllocationCreate(BaseModel):
    """Payload to create or update monthly sample quota for an employee."""

    user_id: int = Field(..., description="Target field representative user ID")
    product_id: int = Field(..., description="Product ID")
    month: int = Field(..., ge=1, le=12, description="Allocation calendar month")
    year: int = Field(..., ge=2024, le=2035, description="Allocation calendar year")
    allocated_quantity: int = Field(..., ge=0, description="Target quota in units")


class SampleAllocationBulkItem(BaseModel):
    user_id: int
    product_id: int
    allocated_quantity: int


class SampleAllocationBulkCreate(BaseModel):
    """Bulk monthly sample allocation payload."""

    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2024, le=2035)
    allocations: list[SampleAllocationBulkItem]


class SampleAllocationResponse(BaseModel):
    """Sample monthly allocation output."""

    id: int
    user_id: int
    user_name: str | None = None
    employee_code: str | None = None
    product_id: int
    product_name: str | None = None
    product_code: str | None = None
    month: int
    year: int
    allocated_quantity: int
    issued_quantity: int
    distributed_quantity: int
    balance_quantity: int
    allocated_by_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SampleAllocationListResponse(BaseModel):
    """Paginated list of sample allocations."""

    items: list[SampleAllocationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==================== SAMPLE ISSUE SCHEMAS ====================


class SampleIssueCreate(BaseModel):
    """Payload to physically issue samples to field representative."""

    user_id: int = Field(..., description="Field representative recipient user ID")
    product_id: int = Field(..., description="Product ID")
    batch_number: str = Field(..., description="Selected available stock batch number")
    quantity: int = Field(..., gt=0, description="Quantity to dispatch")
    dispatch_mode: str = Field("COURIER", description="HANDOVER, COURIER, DEPOT_PICKUP")
    tracking_reference: str | None = Field(None, description="Courier docket / tracking number")
    remarks: str | None = Field(None, description="Dispatch instructions or notes")


class SampleIssueAcknowledgeRequest(BaseModel):
    """Field representative acknowledgment of receipt."""

    received_date: date = Field(..., description="Date samples physically received")
    remarks: str | None = Field(None, description="Condition on arrival notes")


class SampleIssueResponse(BaseModel):
    """Sample dispatch / issue record output."""

    id: int
    issue_number: str
    issue_date: date
    user_id: int
    user_name: str | None = None
    employee_code: str | None = None
    product_id: int
    product_name: str | None = None
    product_code: str | None = None
    batch_number: str
    quantity: int
    dispatch_mode: str
    tracking_reference: str | None = None
    status: str
    received_date: date | None = None
    remarks: str | None = None
    issued_by_name: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SampleIssueListResponse(BaseModel):
    """Paginated list of sample issue dispatches."""

    items: list[SampleIssueResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==================== SAMPLE BATCH & BALANCE SCHEMAS ====================


class SampleBatchResponse(BaseModel):
    """Available batch inventory at Head Office depot."""

    id: int
    product_id: int
    product_name: str | None = None
    batch_number: str
    mfg_date: date | None = None
    expiry_date: date
    quantity_received: int
    quantity_allocated: int
    quantity_issued: int
    quantity_balance: int
    days_to_expiry: int
    expiry_status: str  # ACTIVE, NEAR_EXPIRY (<=90d), EXPIRED

    model_config = ConfigDict(from_attributes=True)


class SampleStockBalanceResponse(BaseModel):
    """High-level sample stock balance report item."""

    product_id: int
    product_name: str
    product_code: str
    category: str
    packaging: str
    ho_balance: int
    total_allocated: int
    total_issued: int
    total_sampled_dcr: int
    mr_holding_balance: int
    active_batches_count: int
