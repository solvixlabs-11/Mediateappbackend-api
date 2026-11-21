"""Meetings business logic service."""

from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.modules.audit.service import AuditService
from app.modules.meetings.models import Meeting
from app.modules.meetings.schemas import (
    MeetingCreateRequest,
    MeetingResponse,
    MeetingSummaryResponse,
    MeetingUpdateRequest,
)
from app.modules.users.models import User


class MeetingService:
    """Service handling meeting workflow (Drafts, Applied, Received, View All)."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def _to_response(self, m: Meeting) -> MeetingResponse:
        return MeetingResponse(
            id=m.id,
            agenda=m.agenda,
            meeting_type=m.meeting_type,
            start_date=m.start_date,
            end_date=m.end_date,
            created_by_id=m.created_by_id,
            created_by_name=m.created_by_user.full_name if m.created_by_user else None,
            organiser_id=m.organiser_id,
            organiser_name=m.organiser_user.full_name if m.organiser_user else None,
            location=m.location,
            status=m.status,
            remarks=m.remarks,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    def get_summary(self, user: User) -> MeetingSummaryResponse:
        """Calculate tile counts for workflow inbox."""
        is_admin = bool(user.role and user.role.code in ["ADMIN", "ERP ADMIN"])

        # Drafts: created by user with status DRAFT
        drafts = (
            self.db.query(func.count(Meeting.id))
            .filter(
                Meeting.created_by_id == user.id,
                Meeting.status == "DRAFT",
                Meeting.is_active == True,
            )
            .scalar()
            or 0
        )

        # Applied: submitted by user with status APPLIED
        applied = (
            self.db.query(func.count(Meeting.id))
            .filter(
                Meeting.created_by_id == user.id,
                Meeting.status == "APPLIED",
                Meeting.is_active == True,
            )
            .scalar()
            or 0
        )

        # Received: waiting for user's action (as organiser, or all pending for admin)
        if is_admin:
            received = (
                self.db.query(func.count(Meeting.id))
                .filter(
                    Meeting.status == "APPLIED",
                    Meeting.created_by_id != user.id,
                    Meeting.is_active == True,
                )
                .scalar()
                or 0
            )
        else:
            received = (
                self.db.query(func.count(Meeting.id))
                .filter(
                    Meeting.organiser_id == user.id,
                    Meeting.created_by_id != user.id,
                    Meeting.status == "APPLIED",
                    Meeting.is_active == True,
                )
                .scalar()
                or 0
            )

        # Total accessible meetings
        total = (
            self.db.query(func.count(Meeting.id))
            .filter(Meeting.is_active == True)
            .scalar()
            or 0
        )

        return MeetingSummaryResponse(
            drafts=drafts,
            applied=applied,
            received=received,
            total=total,
        )

    def list_meetings(
        self,
        user: User,
        status_filter: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[MeetingResponse]:
        """Fetch list of meetings with optional status and search filters."""
        query = self.db.query(Meeting).filter(Meeting.is_active == True)

        if status_filter:
            sf = status_filter.upper().strip()
            if sf == "DRAFTS":
                query = query.filter(Meeting.created_by_id == user.id, Meeting.status == "DRAFT")
            elif sf == "APPLIED":
                query = query.filter(Meeting.created_by_id == user.id, Meeting.status == "APPLIED")
            elif sf == "RECEIVED":
                query = query.filter(Meeting.status == "APPLIED", Meeting.created_by_id != user.id)
            else:
                query = query.filter(Meeting.status == sf)

        if search:
            query = query.filter(Meeting.agenda.ilike(f"%{search.strip()}%"))

        query = query.order_by(Meeting.start_date.desc())
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return [self._to_response(m) for m in items]

    def create_meeting(self, payload: MeetingCreateRequest, user: User) -> MeetingResponse:
        """Create new meeting draft or applied."""
        meeting = Meeting(
            agenda=payload.agenda,
            meeting_type=payload.meeting_type or "CYCLE_MEETING",
            start_date=payload.start_date,
            end_date=payload.end_date,
            created_by_id=user.id,
            organiser_id=payload.organiser_id or user.id,
            location=payload.location,
            status=(payload.status or "DRAFT").upper(),
            remarks=payload.remarks,
        )
        self.db.add(meeting)
        self.db.commit()
        self.db.refresh(meeting)

        AuditService.record(
            self.db,
            user_id=user.id,
            module="MEETING",
            action="CREATE",
            entity_type="Meeting",
            entity_id=str(meeting.id),
            summary=f"Created meeting '{meeting.agenda}' ({meeting.status})",
            channel="WEB",
        )

        return self._to_response(meeting)

    def submit_meeting(self, meeting_id: int, user: User) -> MeetingResponse:
        """Submit draft meeting for review/approval."""
        meeting = self.db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Meeting with ID {meeting_id} not found.",
            )
        if meeting.created_by_id != user.id and not (user.role and user.role.code == "ADMIN"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the creator can submit this draft meeting.",
            )
        meeting.status = "APPLIED"
        meeting.updated_by = user.id

        AuditService.record(
            self.db,
            user_id=user.id,
            module="MEETING",
            action="SUBMIT",
            entity_type="Meeting",
            entity_id=str(meeting.id),
            summary=f"Submitted meeting '{meeting.agenda}' for approval",
            channel="WEB",
        )
        self.db.commit()
        self.db.refresh(meeting)
        return self._to_response(meeting)

    def decide_meeting(
        self, meeting_id: int, decision: str, user: User, remarks: str | None = None
    ) -> MeetingResponse:
        """Approve or Reject an applied meeting."""
        meeting = self.db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Meeting with ID {meeting_id} not found.",
            )
        decision_upper = decision.upper().strip()
        if decision_upper not in ["APPROVED", "REJECTED"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid meeting decision '{decision}'.",
            )
        meeting.status = decision_upper
        if remarks:
            meeting.remarks = remarks
        meeting.updated_by = user.id

        AuditService.record(
            self.db,
            user_id=user.id,
            module="MEETING",
            action=decision_upper,
            entity_type="Meeting",
            entity_id=str(meeting.id),
            summary=f"Marked meeting '{meeting.agenda}' as {decision_upper}",
            channel="WEB",
        )
        self.db.commit()
        self.db.refresh(meeting)
        return self._to_response(meeting)
