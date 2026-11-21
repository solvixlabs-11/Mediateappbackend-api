"""Seeder for Leave Requests (32 records across field staff)."""

from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from app.modules.approvals.models import ApprovalRequest
from app.modules.leaves.models import LeaveBalance, LeaveRequest
from app.modules.users.models import User
from seed.base import SeedResult


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="leaves")
    if not dev:
        return result

    users = session.query(User).filter(User.is_active == True).all()  # noqa: E712
    if not users:
        return result

    today = date.today()

    # Leave samples (32 varied entries across users)
    leave_types = ["CASUAL", "SICK", "EARNED"]
    reasons = [
        "Personal family commitment in hometown",
        "Viral fever and seasonal influenza",
        "Sister's wedding ceremony attendance",
        "Medical appointment and health checkup",
        "Family relocation and house shifting",
        "Urgent domestic work and personal errands",
        "Spouse medical emergency and hospital care",
        "Higher education examination attendance",
        "Religious festival observance at village",
        "Severe dental pain and root canal treatment",
    ]

    for idx in range(32):
        u = users[idx % len(users)]

        # Ensure leave balance exists
        bal = session.query(LeaveBalance).filter(LeaveBalance.user_id == u.id).first()
        if not bal:
            bal = LeaveBalance(
                user_id=u.id,
                year=today.year,
                casual_leave_balance=12.0,
                sick_leave_balance=8.0,
                earned_leave_balance=15.0,
            )
            session.add(bal)
            session.flush()

        # Status distribution: 14 PENDING, 12 APPROVED, 4 REJECTED, 2 CANCELLED
        if idx < 14:
            status = "PENDING"
        elif idx < 26:
            status = "APPROVED"
        elif idx < 30:
            status = "REJECTED"
        else:
            status = "CANCELLED"

        start_offset = (idx * 2) - 10
        start = today + timedelta(days=start_offset)
        days = 1.0 if idx % 3 == 0 else 2.0
        end = start + timedelta(days=int(days) - 1)
        l_type = leave_types[idx % len(leave_types)]
        reason = reasons[idx % len(reasons)]
        client_uuid = f"seed-leave-item-{idx + 1:03d}"

        existing = session.query(LeaveRequest).filter(LeaveRequest.client_uuid == client_uuid).first()
        if not existing:
            lr = LeaveRequest(
                user_id=u.id,
                leave_type=l_type,
                start_date=start,
                end_date=end,
                days_count=days,
                reason=reason,
                status=status,
                client_uuid=client_uuid,
            )
            session.add(lr)
            session.flush()

            # Create corresponding ApprovalRequest
            app_req = ApprovalRequest(
                entity_type="LEAVE",
                entity_id=lr.id,
                requester_id=u.id,
                status=status,
                current_step=1,
                total_steps=1,
                title=f"Leave: {l_type.title()} ({days} day{'s' if days > 1 else ''})",
                details=f"From {start} to {end} - {reason}",
            )
            session.add(app_req)
            session.flush()
            lr.approval_request_id = app_req.id
            result.created += 1
        else:
            result.unchanged += 1

    session.flush()
    return result
