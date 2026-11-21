"""Router for Admin Visits Operations (Delete My Visits & Restore)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_permission
from app.modules.dcr.admin_visits_schemas import (
    DeleteVisitsExecuteRequest,
    DeleteVisitsExecuteResponse,
    DeleteVisitsPreviewRequest,
    DeleteVisitsPreviewResponse,
    RestoreVisitsRequest,
    RestoreVisitsResponse,
)
from app.modules.dcr.admin_visits_service import AdminVisitsService
from app.modules.users.models import User

router = APIRouter(prefix="/admin/visits", tags=["Admin Visits Management"])


@router.post(
    "/delete-preview",
    response_model=DeleteVisitsPreviewResponse,
    summary="Preview matching visits for bulk deletion with security token",
)
def preview_delete_visits(
    payload: DeleteVisitsPreviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("visits:delete")),
) -> DeleteVisitsPreviewResponse:
    """Generate preview and secure token for visits deletion (Admin only)."""
    service = AdminVisitsService(db)
    return service.get_delete_preview(payload, admin_user=current_user)


@router.post(
    "/delete",
    response_model=DeleteVisitsExecuteResponse,
    summary="Execute transactional soft delete with side-effect rollback (Admin only)",
)
def execute_delete_visits(
    payload: DeleteVisitsExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("visits:delete")),
) -> DeleteVisitsExecuteResponse:
    """Soft delete up to 5,000 visits with atomic rollback of planned visits and follow-ups."""
    service = AdminVisitsService(db)
    return service.execute_delete(payload, admin_user=current_user)


@router.post(
    "/restore",
    response_model=RestoreVisitsResponse,
    summary="Restore soft-deleted visits within retention window (Admin only)",
)
def restore_visits(
    payload: RestoreVisitsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("visits:delete")),
) -> RestoreVisitsResponse:
    """Restore soft deleted visits by batch token or explicit IDs."""
    service = AdminVisitsService(db)
    return service.restore_visits(payload, admin_user=current_user)
