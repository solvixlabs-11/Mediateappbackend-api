"""Employee Territory & Customer Mapping Wizard REST API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.mappings.schemas import (
    MappingBatchDetailResponse,
    MappingBatchResponse,
    MappingCapabilitiesResponse,
    MappingPreviewRequest,
    MappingPreviewResponse,
)
from app.modules.mappings.service import MappingService
from app.modules.users.models import User

router = APIRouter(prefix="/mappings", tags=["Mapping Wizard"])


def _check_mappings_write_access(current_user: User) -> None:
    if not current_user.role or current_user.role.code not in ["ADMIN", "MANAGER", "ERP ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Modifying mappings requires Manager or Administrator privileges.",
        )


@router.get(
    "/capabilities",
    response_model=MappingCapabilitiesResponse,
    summary="Get mapping wizard capabilities and constraints",
)
def get_mapping_capabilities() -> MappingCapabilitiesResponse:
    """Fetch supported modes, beat readiness (beats=false), and batch constraints."""
    return MappingCapabilitiesResponse()


@router.post(
    "/preview",
    response_model=MappingPreviewResponse,
    summary="Create a dry-run preview and draft mapping batch",
)
def preview_mapping(
    payload: MappingPreviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MappingPreviewResponse:
    """Preview candidate assignments, conflict resolutions, and item counts."""
    _check_mappings_write_access(current_user)
    service = MappingService(db)
    return service.preview(payload, current_user)


@router.post(
    "/{batch_id}/apply",
    response_model=MappingBatchResponse,
    summary="Apply a draft mapping batch in an atomic transaction",
)
def apply_mapping(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MappingBatchResponse:
    """Execute bulk assignments and record audit logs."""
    _check_mappings_write_access(current_user)
    service = MappingService(db)
    return service.apply(batch_id, current_user)


@router.post(
    "/{batch_id}/revert",
    response_model=MappingBatchResponse,
    summary="Revert an applied batch restoring prior assignments",
)
def revert_mapping(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MappingBatchResponse:
    """Undo applied batch assignments."""
    _check_mappings_write_access(current_user)
    service = MappingService(db)
    return service.revert(batch_id, current_user)


@router.get(
    "",
    response_model=list[MappingBatchResponse],
    summary="List past mapping batches history",
)
def list_mappings(
    mode: str | None = Query(default=None),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MappingBatchResponse]:
    """Fetch history of applied and reverted mapping batches."""
    service = MappingService(db)
    return service.list_batches(mode=mode, status=status, page=page, page_size=page_size)


@router.get(
    "/{batch_id}",
    response_model=MappingBatchDetailResponse,
    summary="Get mapping batch detail and assigned items",
)
def get_mapping_detail(
    batch_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MappingBatchDetailResponse:
    """Fetch batch details and item records."""
    service = MappingService(db)
    return service.get_batch_detail(batch_id, page=page, page_size=page_size)
