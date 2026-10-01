"""Leave Management business logic service."""

from __future__ import annotations

from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.approvals.repository import ApprovalRepository
from app.modules.leaves.models import LeaveRequest
from app.modules.leaves.repository import LeaveRepository
from app.modules.leaves.schemas import (
    LeaveApplyRequest,
    LeaveBalanceResponse,
    LeaveResponse,
)
from app.modules.users.models import User


class LeaveService:
    """Service enforcing BR-09 (no overlap) and BR-10 (balance restoration on cancel)."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = LeaveRepository(db)
        self.approval_repo = ApprovalRepository(db)

    def _to_response(self, leave: LeaveRequest) -> LeaveResponse:
        return LeaveResponse(
            id=leave.id,
            user_id=leave.user_id,
            user_name=leave.user.full_name if leave.user else None,
            leave_type=leave.leave_type,
            start_date=leave.start_date,
            end_date=leave.end_date,
            days_count=leave.days_count,
            reason=leave.reason,
            status=leave.status,
            approval_request_id=leave.approval_request_id,
            rejection_reason=leave.rejection_reason,
            created_at=leave.created_at,
            updated_at=leave.updated_at,
        )

    def get_balances(self, user: User, year: int | None = None) -> LeaveBalanceResponse:
        """Fetch current annual leave balances."""
        target_year = year or date.today().year
        bal = self.repo.get_or_create_balance(user.id, target_year)
        self.db.commit()
        self.db.refresh(bal)
        total = bal.casual_leave_balance + bal.sick_leave_balance + bal.earned_leave_balance
        return LeaveBalanceResponse(
            year=bal.year,
            casual_leave_balance=bal.casual_leave_balance,
            sick_leave_balance=bal.sick_leave_balance,
            earned_leave_balance=bal.earned_leave_balance,
            total_balance=total,
        )

    def apply_leave(self, payload: LeaveApplyRequest, user: User) -> LeaveResponse:
        """Apply for leave with BR-09 overlap check and balance validation."""
        # Idempotency check with client_uuid
        if payload.client_uuid:
            existing = self.repo.get_by_client_uuid(payload.client_uuid)
            if existing:
                return self._to_response(existing)

        if payload.end_date < payload.start_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Leave end date cannot precede start date.",
            )

        # BR-09: Overlap prevention
        if self.repo.has_overlapping_leave(user.id, payload.start_date, payload.end_date):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A leave request already exists overlapping this date window.",
            )

        # Validate leave type and balance
        l_type = payload.leave_type.upper().strip()
        if l_type not in ("CASUAL", "SICK", "EARNED"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Leave type must be 'CASUAL', 'SICK', or 'EARNED'.",
            )

        bal = self.repo.get_or_create_balance(user.id, payload.start_date.year)
        available = (
            bal.casual_leave_balance
            if l_type == "CASUAL"
            else bal.sick_leave_balance
            if l_type == "SICK"
            else bal.earned_leave_balance
        )

        if payload.days_count > available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient {l_type} leave balance. Available: {available} days.",
            )

        leave = self.repo.create(
            user_id=user.id,
            leave_type=l_type,
            start_date=payload.start_date,
            end_date=payload.end_date,
            days_count=payload.days_count,
            reason=payload.reason,
            client_uuid=payload.client_uuid,
        )

        # Dispatch approval request into the manager's inbox
        approval_req = self.approval_repo.create_request(
            entity_type="LEAVE",
            entity_id=leave.id,
            requester_id=user.id,
            title=f"Leave: {l_type} ({leave.days_count} days from {leave.start_date})",
            details=f"Reason: {leave.reason}",
        )
        leave.approval_request_id = approval_req.id

        self.db.commit()
        self.db.refresh(leave)
        return self._to_response(leave)

    def cancel_leave(self, leave_id: int, user: User) -> LeaveResponse:
        """Cancel a leave request and restore balance if already approved (BR-10)."""
        leave = self.repo.get_by_id(leave_id)
        if not leave:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Leave request {leave_id} not found.",
            )

        if leave.user_id != user.id and (user.role and user.role.code != "ADMIN"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cancel your own leave requests.",
            )

        if leave.status == "CANCELLED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Leave request is already cancelled.",
            )

        was_approved = leave.status == "APPROVED"
        leave.status = "CANCELLED"

        # BR-10: Restore deducted balance on cancel
        if was_approved:
            bal = self.repo.get_or_create_balance(leave.user_id, leave.start_date.year)
            if leave.leave_type == "CASUAL":
                bal.casual_leave_balance += leave.days_count
            elif leave.leave_type == "SICK":
                bal.sick_leave_balance += leave.days_count
            elif leave.leave_type == "EARNED":
                bal.earned_leave_balance += leave.days_count

        self.db.commit()
        self.db.refresh(leave)
        return self._to_response(leave)

    def list_leaves(self, current_user: User) -> list[LeaveResponse]:
        """List leaves scoped to user."""
        role_code = current_user.role.code if current_user.role else "MR"
        user_id = None if role_code in ("ADMIN", "MANAGER") else current_user.id
        leaves = self.repo.list_leaves(user_id=user_id)
        return [self._to_response(item) for item in leaves]
