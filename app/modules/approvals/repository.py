"""Approval engine database repository."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.approvals.models import ApprovalHistory, ApprovalRequest
from app.modules.users.models import ManagerMRAssignment


class ApprovalRepository:
    """Repository handling approval requests, history, and scope queries."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, request_id: int) -> ApprovalRequest | None:
        """Fetch approval request by primary key."""
        return self.db.query(ApprovalRequest).filter(ApprovalRequest.id == request_id).first()

    def get_by_entity(self, entity_type: str, entity_id: int) -> ApprovalRequest | None:
        """Fetch approval request by linked entity."""
        return (
            self.db.query(ApprovalRequest)
            .filter(
                ApprovalRequest.entity_type == entity_type,
                ApprovalRequest.entity_id == entity_id,
            )
            .first()
        )

    def create_request(
        self,
        entity_type: str,
        entity_id: int,
        requester_id: int,
        title: str,
        details: str | None = None,
        total_steps: int = 1,
    ) -> ApprovalRequest:
        """Create new pending approval request."""
        req = ApprovalRequest(
            entity_type=entity_type,
            entity_id=entity_id,
            requester_id=requester_id,
            status="PENDING",
            current_step=1,
            total_steps=total_steps,
            title=title,
            details=details,
        )
        self.db.add(req)
        self.db.flush()
        return req

    def add_history(
        self,
        request_id: int,
        approver_id: int,
        decision: str,
        comments: str | None = None,
    ) -> ApprovalHistory:
        """Record an approval decision in the history log."""
        hist = ApprovalHistory(
            request_id=request_id,
            approver_id=approver_id,
            decision=decision,
            comments=comments,
        )
        self.db.add(hist)
        self.db.flush()
        return hist

    def get_inbox_for_manager(self, manager_id: int) -> list[ApprovalRequest]:
        """Fetch pending approval requests for all MRs reporting to this manager."""
        subquery = (
            self.db.query(ManagerMRAssignment.mr_id)
            .filter(
                ManagerMRAssignment.manager_id == manager_id,
                ManagerMRAssignment.is_active.is_(True),
            )
            .subquery()
        )

        return (
            self.db.query(ApprovalRequest)
            .filter(
                ApprovalRequest.status == "PENDING",
                ApprovalRequest.requester_id.in_(subquery),
            )
            .order_by(ApprovalRequest.created_at.desc())
            .all()
        )

    def get_all_pending(self) -> list[ApprovalRequest]:
        """Admin view of all pending requests across organization."""
        return (
            self.db.query(ApprovalRequest)
            .filter(ApprovalRequest.status == "PENDING")
            .order_by(ApprovalRequest.created_at.desc())
            .all()
        )

    def get_my_requests(self, requester_id: int) -> list[ApprovalRequest]:
        """Fetch all requests created by this user."""
        return (
            self.db.query(ApprovalRequest)
            .filter(ApprovalRequest.requester_id == requester_id)
            .order_by(ApprovalRequest.created_at.desc())
            .all()
        )
