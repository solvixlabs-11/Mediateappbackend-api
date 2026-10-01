"""Approval engine business logic service."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.approvals.models import ApprovalRequest
from app.modules.approvals.repository import ApprovalRepository
from app.modules.approvals.schemas import (
    ApprovalDecisionRequest,
    ApprovalHistoryResponse,
    ApprovalRequestResponse,
)
from app.modules.expenses.models import Expense
from app.modules.leaves.models import LeaveBalance, LeaveRequest
from app.modules.tours.models import TourProgram
from app.modules.users.models import User


class ApprovalService:
    """Service handling multi-step approvals for Tours, Expenses, and Leaves."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ApprovalRepository(db)

    def _to_response(self, req: ApprovalRequest) -> ApprovalRequestResponse:
        """Map ORM ApprovalRequest to Pydantic response."""
        history_list = [
            ApprovalHistoryResponse(
                id=h.id,
                request_id=h.request_id,
                approver_id=h.approver_id,
                approver_name=h.approver.full_name if h.approver else None,
                decision=h.decision,
                comments=h.comments,
                decided_at=h.decided_at,
            )
            for h in req.history
        ]

        return ApprovalRequestResponse(
            id=req.id,
            entity_type=req.entity_type,
            entity_id=req.entity_id,
            requester_id=req.requester_id,
            requester_name=req.requester.full_name if req.requester else None,
            requester_email=req.requester.email if req.requester else None,
            status=req.status,
            current_step=req.current_step,
            total_steps=req.total_steps,
            title=req.title,
            details=req.details,
            created_at=req.created_at,
            updated_at=req.updated_at,
            history=history_list,
        )

    def get_inbox(self, current_user: User) -> list[ApprovalRequestResponse]:
        """Fetch pending approval requests within user's role scope."""
        role_code = current_user.role.code if current_user.role else "MR"

        if role_code == "ADMIN":
            requests = self.repo.get_all_pending()
        elif role_code == "MANAGER":
            requests = self.repo.get_inbox_for_manager(current_user.id)
        else:
            # MR: view their own pending submissions
            requests = self.repo.get_my_requests(current_user.id)

        return [self._to_response(r) for r in requests]

    def get_request_detail(self, request_id: int, current_user: User) -> ApprovalRequestResponse:
        """Fetch single approval request details."""
        req = self.repo.get_by_id(request_id)
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approval request {request_id} not found.",
            )
        return self._to_response(req)

    def process_decision(
        self,
        request_id: int,
        payload: ApprovalDecisionRequest,
        approver: User,
    ) -> ApprovalRequestResponse:
        """Process manager/admin decision (Approve / Reject) with business rules (BR-08, BR-10)."""
        req = self.repo.get_by_id(request_id)
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approval request {request_id} not found.",
            )

        if req.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Approval request is already finalized as {req.status}.",
            )

        decision = payload.decision.upper().strip()
        if decision not in ("APPROVED", "REJECTED"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Decision must be either 'APPROVED' or 'REJECTED'.",
            )

        # BR-08: Rejection requires a mandatory comment/reason
        if decision == "REJECTED" and not payload.comments:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A comment or reason is required when rejecting a request.",
            )

        # Record history
        self.repo.add_history(
            request_id=req.id,
            approver_id=approver.id,
            decision=decision,
            comments=payload.comments,
        )

        req.status = decision

        # Callback into target entity
        if req.entity_type == "TOUR":
            tour = self.db.query(TourProgram).filter(TourProgram.id == req.entity_id).first()
            if tour:
                tour.status = decision
                tour.rejection_reason = payload.comments if decision == "REJECTED" else None

        elif req.entity_type == "EXPENSE":
            exp = self.db.query(Expense).filter(Expense.id == req.entity_id).first()
            if exp:
                exp.status = decision
                exp.rejection_reason = payload.comments if decision == "REJECTED" else None

        elif req.entity_type == "LEAVE":
            leave = self.db.query(LeaveRequest).filter(LeaveRequest.id == req.entity_id).first()
            if leave:
                leave.status = decision
                leave.rejection_reason = payload.comments if decision == "REJECTED" else None

                # BR-10: Deduct leave balance upon approval
                if decision == "APPROVED":
                    balance = (
                        self.db.query(LeaveBalance)
                        .filter(
                            LeaveBalance.user_id == leave.user_id,
                            LeaveBalance.year == leave.start_date.year,
                        )
                        .first()
                    )
                    if balance:
                        if leave.leave_type == "CASUAL":
                            balance.casual_leave_balance = max(
                                0.0, balance.casual_leave_balance - leave.days_count
                            )
                        elif leave.leave_type == "SICK":
                            balance.sick_leave_balance = max(
                                0.0, balance.sick_leave_balance - leave.days_count
                            )
                        elif leave.leave_type == "EARNED":
                            balance.earned_leave_balance = max(
                                0.0, balance.earned_leave_balance - leave.days_count
                            )

        self.db.commit()
        self.db.refresh(req)
        return self._to_response(req)
