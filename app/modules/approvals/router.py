"""Approval engine REST API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.approvals.schemas import (
    ApprovalDecisionRequest,
    ApprovalRequestResponse,
)
from app.modules.approvals.service import ApprovalService
from app.modules.users.models import User

router = APIRouter(prefix="/approvals", tags=["Approvals"])


@router.get(
    "/inbox",
    response_model=list[ApprovalRequestResponse],
    summary="Get pending approvals inbox for manager or admin",
)
def get_inbox(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ApprovalRequestResponse]:
    """Fetch pending approvals scoped to the user."""
    service = ApprovalService(db)
    return service.get_inbox(current_user)


@router.get(
    "/{request_id}",
    response_model=ApprovalRequestResponse,
    summary="Get approval request detail with audit history",
)
def get_approval_detail(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApprovalRequestResponse:
    """Fetch approval details by request ID."""
    service = ApprovalService(db)
    return service.get_request_detail(request_id, current_user)


@router.post(
    "/{request_id}/decision",
    response_model=ApprovalRequestResponse,
    summary="Submit approve or reject decision (BR-08)",
)
def submit_decision(
    request_id: int,
    payload: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApprovalRequestResponse:
    """Approve or reject a request with audit log and entity callback."""
    service = ApprovalService(db)
    return service.process_decision(request_id, payload, current_user)
