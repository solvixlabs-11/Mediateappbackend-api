"""Sample Inventory, Allocations, Issues & Stock Ledger REST API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.modules.stock.schemas import (
    SampleAllocationBulkCreate,
    SampleAllocationCreate,
    SampleAllocationListResponse,
    SampleAllocationResponse,
    SampleBatchResponse,
    SampleInwardCreate,
    SampleInwardListResponse,
    SampleInwardResponse,
    SampleIssueAcknowledgeRequest,
    SampleIssueCreate,
    SampleIssueListResponse,
    SampleIssueResponse,
    SampleStockBalanceResponse,
)
from app.modules.stock.service import SampleStockService
from app.modules.users.models import User

router = APIRouter(prefix="/stock/samples", tags=["Sample Stock Management"])


# ==================== SAMPLE INWARD ====================


@router.get(
    "/inward",
    response_model=SampleInwardListResponse,
    summary="List sample inward shipments received at Head Office",
)
def list_sample_inwards(
    product_id: int | None = Query(None, description="Filter by product ID"),
    batch_number: str | None = Query(None, description="Filter by batch number"),
    search: str | None = Query(None, description="Search challan, product, supplier"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SampleInwardListResponse:
    service = SampleStockService(db)
    return service.list_inwards(
        product_id=product_id,
        batch_number=batch_number,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/inward",
    response_model=SampleInwardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record sample stock inward arrival at Head Office depot",
)
def record_sample_inward(
    payload: SampleInwardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SampleInwardResponse:
    service = SampleStockService(db)
    return service.record_inward(payload, current_user)


# ==================== SAMPLE ALLOCATION ====================


@router.get(
    "/allocations",
    response_model=SampleAllocationListResponse,
    summary="List monthly sample quotas allocated to representatives",
)
def list_sample_allocations(
    user_id: int | None = Query(None, description="Filter by employee ID"),
    product_id: int | None = Query(None, description="Filter by product ID"),
    month: int | None = Query(None, ge=1, le=12, description="Filter by calendar month"),
    year: int | None = Query(None, ge=2024, le=2035, description="Filter by calendar year"),
    page: int = Query(1, ge=1),
    page_size: int = Query(15, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SampleAllocationListResponse:
    service = SampleStockService(db)
    return service.list_allocations(
        user_id=user_id,
        product_id=product_id,
        month=month,
        year=year,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/allocations",
    response_model=SampleAllocationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign or update monthly sample quota for an employee",
)
def create_sample_allocation(
    payload: SampleAllocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SampleAllocationResponse:
    service = SampleStockService(db)
    return service.create_or_update_allocation(payload, current_user)


@router.post(
    "/allocations/bulk",
    summary="Bulk assign monthly sample quotas across representatives",
)
def bulk_sample_allocation(
    payload: SampleAllocationBulkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SampleStockService(db)
    return service.bulk_allocate(payload, current_user)


# ==================== SAMPLE ISSUE ====================


@router.get(
    "/issues",
    response_model=SampleIssueListResponse,
    summary="List sample dispatches and issue orders",
)
def list_sample_issues(
    user_id: int | None = Query(None, description="Filter by recipient user ID"),
    product_id: int | None = Query(None, description="Filter by product ID"),
    status: str | None = Query(None, description="Filter by dispatch status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SampleIssueListResponse:
    service = SampleStockService(db)
    return service.list_issues(
        user_id=user_id,
        product_id=product_id,
        status=status,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/issues",
    response_model=SampleIssueResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Issue samples to field representative and deduct stock",
)
def create_sample_issue(
    payload: SampleIssueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SampleIssueResponse:
    service = SampleStockService(db)
    return service.create_issue(payload, current_user)


@router.post(
    "/issues/{issue_id}/acknowledge",
    response_model=SampleIssueResponse,
    summary="Field staff acknowledgment of sample receipt",
)
def acknowledge_sample_issue(
    issue_id: int,
    payload: SampleIssueAcknowledgeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SampleIssueResponse:
    service = SampleStockService(db)
    return service.acknowledge_issue(issue_id, payload, current_user)


# ==================== BATCHES & BALANCE ====================


@router.get(
    "/batches",
    response_model=list[SampleBatchResponse],
    summary="List active sample batches with expiry status",
)
def get_sample_batches(
    product_id: int | None = Query(None, description="Filter by product ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SampleBatchResponse]:
    service = SampleStockService(db)
    return service.get_batches(product_id=product_id)


@router.get(
    "/balance",
    response_model=list[SampleStockBalanceResponse],
    summary="Product-wise sample stock balance ledger (HO vs Field)",
)
def get_sample_stock_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SampleStockBalanceResponse]:
    service = SampleStockService(db)
    return service.get_sample_stock_balance_report()
