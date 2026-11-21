"""Meetings REST API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.meetings.schemas import (
    MeetingCreateRequest,
    MeetingResponse,
    MeetingSummaryResponse,
    MeetingUpdateRequest,
)
from app.modules.meetings.service import MeetingService
from app.modules.users.models import User

router = APIRouter(prefix="/meetings", tags=["Meetings"])


@router.get(
    "/summary",
    response_model=MeetingSummaryResponse,
    summary="Get workflow inbox summary tiles (Drafts, Applied, Received)",
)
def get_meetings_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MeetingSummaryResponse:
    """Fetch counts for Drafts (with +), Applied, Received, and Total."""
    service = MeetingService(db)
    return service.get_summary(current_user)


@router.get(
    "",
    response_model=list[MeetingResponse],
    summary="List meetings with workflow filters",
)
def list_meetings(
    status: str | None = Query(
        default=None, description="Status filter: DRAFTS, APPLIED, RECEIVED, APPROVED, REJECTED"
    ),
    search: str | None = Query(default=None, description="Search by agenda"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MeetingResponse]:
    """Fetch meetings matching filter."""
    service = MeetingService(db)
    return service.list_meetings(
        user=current_user,
        status_filter=status,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.post(
    "",
    response_model=MeetingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create meeting draft or application",
)
def create_meeting(
    payload: MeetingCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MeetingResponse:
    """Create a new cycle meeting or review."""
    service = MeetingService(db)
    return service.create_meeting(payload, current_user)


@router.post(
    "/{meeting_id}/submit",
    response_model=MeetingResponse,
    summary="Submit draft meeting",
)
def submit_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MeetingResponse:
    """Submit draft meeting."""
    service = MeetingService(db)
    return service.submit_meeting(meeting_id, current_user)


@router.post(
    "/{meeting_id}/approve",
    response_model=MeetingResponse,
    summary="Approve meeting",
)
def approve_meeting(
    meeting_id: int,
    remarks: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MeetingResponse:
    """Approve applied meeting."""
    service = MeetingService(db)
    return service.decide_meeting(meeting_id, "APPROVED", current_user, remarks)


@router.post(
    "/{meeting_id}/reject",
    response_model=MeetingResponse,
    summary="Reject meeting",
)
def reject_meeting(
    meeting_id: int,
    remarks: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MeetingResponse:
    """Reject applied meeting."""
    service = MeetingService(db)
    return service.decide_meeting(meeting_id, "REJECTED", current_user, remarks)
