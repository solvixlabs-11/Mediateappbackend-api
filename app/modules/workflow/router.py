"""Workflow Inbox REST API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.users.models import User
from app.modules.workflow.schemas import WorkflowItemResponse, WorkflowSummaryResponse
from app.modules.workflow.service import WorkflowService

router = APIRouter(prefix="/workflow", tags=["Workflow Inbox"])


@router.get(
    "/{module}/summary",
    response_model=WorkflowSummaryResponse,
    summary="Get 3-tile dynamic counts (Drafts, Applied, Received) for module",
)
def get_workflow_summary(
    module: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkflowSummaryResponse:
    """Return dynamic counts of Drafts, Applied, and Received items scoped to the caller."""
    service = WorkflowService(db)
    return service.get_summary(module=module, current_user=current_user)


@router.get(
    "/{module}",
    response_model=list[WorkflowItemResponse],
    summary="Get workflow inbox items by box (drafts, applied, received)",
)
def list_workflow_items(
    module: str,
    box: str = Query(default="received", description="'drafts', 'applied', or 'received'"),
    search: str | None = Query(default=None, description="Search across requester, title, details"),
    status: str | None = Query(default=None, description="Status filter e.g. PENDING, APPROVED, REJECTED"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[WorkflowItemResponse]:
    """Return items for the selected workflow box."""
    service = WorkflowService(db)
    return service.list_items(
        module=module,
        box=box,
        current_user=current_user,
        search=search,
        status_filter=status,
        skip=skip,
        limit=limit,
    )
