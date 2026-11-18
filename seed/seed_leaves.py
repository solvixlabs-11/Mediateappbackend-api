"""Seeder for Leave Requests."""

from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.modules.leaves.models import LeaveBalance, LeaveRequest
from app.modules.users.models import User
from seed.base import SeedResult


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="leaves")
    if not dev:
        return result

    users = session.query(User).filter(User.is_active == True).limit(5).all()  # noqa: E712
    today = date.today()

    for u in users:
        # Check leave balance
        bal = session.query(LeaveBalance).filter(LeaveBalance.user_id == u.id).first()
        if not bal:
            bal = LeaveBalance(
                user_id=u.id,
                year=today.year,
                casual_leave_balance=10.0,
                sick_leave_balance=8.0,
                earned_leave_balance=15.0,
            )
            session.add(bal)
            result.created += 1

        # Check sample leave request
        existing = session.query(LeaveRequest).filter(LeaveRequest.user_id == u.id).first()
        if not existing:
            lr = LeaveRequest(
                user_id=u.id,
                leave_type="CASUAL",
                start_date=today + timedelta(days=14),
                end_date=today + timedelta(days=15),
                days_count=2.0,
                reason="Personal family commitment",
                status="PENDING",
                client_uuid=f"seed-leave-{u.id}-{today.isoformat()}",
            )
            session.add(lr)
            result.created += 1
        else:
            result.unchanged += 1

    session.flush()
    return result
