"""Mobile registration API router."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, require_permission
from app.modules.mobile_registrations.schemas import (
    MobileRegistrationBulkActionRequest,
    MobileRegistrationBulkActionResponse,
    MobileRegistrationListResponse,
)
from app.modules.mobile_registrations.service import MobileRegistrationService
from app.modules.users.models import User

router = APIRouter(prefix="/mobile-registrations", tags=["Mobile Registrations"])


@router.get(
    "",
    response_model=MobileRegistrationListResponse,
    summary="List mobile device registrations with filters and pagination",
)
def list_mobile_registrations(
    status: str | None = Query(default=None, description="Filter by status (PENDING, APPROVED, REJECTED, ALL)"),
    search: str | None = Query(default=None, description="Search employee name, code, model"),
    state_id: list[int] | None = Query(default=None, description="Filter by employee state IDs"),
    city_id: list[int] | None = Query(default=None, description="Filter by employee city IDs"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users:read")),
) -> MobileRegistrationListResponse:
    service = MobileRegistrationService(db)
    return service.list_registrations(
        status=status,
        search=search,
        state_ids=state_id,
        city_ids=city_id,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/approve",
    response_model=MobileRegistrationBulkActionResponse,
    summary="Bulk approve mobile device registrations and activate accounts",
)
def bulk_approve_registrations(
    payload: MobileRegistrationBulkActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users:write")),
) -> MobileRegistrationBulkActionResponse:
    service = MobileRegistrationService(db)
    return service.approve_registrations(payload, admin_user=current_user)


@router.post(
    "/reject",
    response_model=MobileRegistrationBulkActionResponse,
    summary="Bulk reject mobile device registrations",
)
def bulk_reject_registrations(
    payload: MobileRegistrationBulkActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users:write")),
) -> MobileRegistrationBulkActionResponse:
    service = MobileRegistrationService(db)
    return service.reject_registrations(payload, admin_user=current_user)
