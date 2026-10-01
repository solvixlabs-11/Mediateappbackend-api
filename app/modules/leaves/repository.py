"""Leave Management database repository."""

from __future__ import annotations

from datetime import date

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.modules.leaves.models import LeaveBalance, LeaveRequest


class LeaveRepository:
    """Repository handling leave balances, applications, and overlap checks."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_create_balance(self, user_id: int, year: int) -> LeaveBalance:
        """Fetch or initialize annual leave balance for user."""
        balance = (
            self.db.query(LeaveBalance)
            .filter(LeaveBalance.user_id == user_id, LeaveBalance.year == year)
            .first()
        )
        if not balance:
            balance = LeaveBalance(
                user_id=user_id,
                year=year,
                casual_leave_balance=12.0,
                sick_leave_balance=8.0,
                earned_leave_balance=15.0,
            )
            self.db.add(balance)
            self.db.flush()
        return balance

    def get_by_id(self, leave_id: int) -> LeaveRequest | None:
        return self.db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()

    def get_by_client_uuid(self, client_uuid: str) -> LeaveRequest | None:
        return self.db.query(LeaveRequest).filter(LeaveRequest.client_uuid == client_uuid).first()

    def has_overlapping_leave(
        self,
        user_id: int,
        start_date: date,
        end_date: date,
        exclude_id: int | None = None,
    ) -> bool:
        """Check if active leave request already overlaps this window (BR-09)."""
        query = self.db.query(LeaveRequest).filter(
            LeaveRequest.user_id == user_id,
            LeaveRequest.status.in_(("PENDING", "APPROVED")),
            or_(
                LeaveRequest.start_date.between(start_date, end_date),
                LeaveRequest.end_date.between(start_date, end_date),
                (LeaveRequest.start_date <= start_date) & (LeaveRequest.end_date >= end_date),
            ),
        )
        if exclude_id:
            query = query.filter(LeaveRequest.id != exclude_id)
        return query.first() is not None

    def create(
        self,
        user_id: int,
        leave_type: str,
        start_date: date,
        end_date: date,
        days_count: float,
        reason: str,
        client_uuid: str | None = None,
    ) -> LeaveRequest:
        req = LeaveRequest(
            user_id=user_id,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            days_count=days_count,
            reason=reason,
            client_uuid=client_uuid,
            status="PENDING",
        )
        self.db.add(req)
        self.db.flush()
        return req

    def list_leaves(self, user_id: int | None = None) -> list[LeaveRequest]:
        query = self.db.query(LeaveRequest)
        if user_id:
            query = query.filter(LeaveRequest.user_id == user_id)
        return query.order_by(LeaveRequest.start_date.desc()).all()
