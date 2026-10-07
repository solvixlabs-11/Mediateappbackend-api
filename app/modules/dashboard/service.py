"""Dashboard service layer providing live field activity, MR KPI cards, and manager oversight."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime

from sqlalchemy import extract, func
from sqlalchemy.orm import Session, selectinload

from app.modules.approvals.models import ApprovalRequest
from app.modules.attendance.models import Attendance
from app.modules.dashboard.schemas import (
    AdminLiveActivityResponse,
    LiveActivitySummary,
    ManagerDashboardResponse,
    MrDashboardResponse,
    MrLiveActivityItem,
    PendingApprovalsSummary,
)
from app.modules.dcr.models import DcrVisit, FollowUp
from app.modules.leaves.models import LeaveRequest
from app.modules.territories.models import Territory, UserTerritoryAssignment
from app.modules.users.models import ManagerMRAssignment, Role, User


class DashboardService:
    """Service generating real-time analytics and KPI rollups from live database state."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_admin_live_activity(self) -> AdminLiveActivityResponse:
        """Fetch real-time field activity summary and per-MR status (Section 8.2)."""
        today = date.today()
        now = datetime.utcnow()

        # 1. Fetch field MR users
        mr_users = (
            self.db.query(User)
            .join(User.role)
            .filter(Role.code == "MR", User.is_active == True, User.is_deleted == False)  # noqa: E712
            .all()
        )
        if not mr_users:
            # Fallback to non-admin users for development/test environments
            mr_users = (
                self.db.query(User)
                .join(User.role)
                .filter(Role.code != "ADMIN", User.is_active == True, User.is_deleted == False)  # noqa: E712
                .all()
            )

        mr_user_ids = [u.id for u in mr_users]

        # 2. Fetch today's attendances
        attendances = (
            self.db.query(Attendance)
            .filter(Attendance.date == today, Attendance.user_id.in_(mr_user_ids))
            .all()
            if mr_user_ids
            else []
        )
        attendance_by_user = {a.user_id: a for a in attendances}

        # 3. Fetch today's DCR visits
        visits = (
            self.db.query(DcrVisit)
            .options(
                selectinload(DcrVisit.doctor),
                selectinload(DcrVisit.chemist),
                selectinload(DcrVisit.hospital),
                selectinload(DcrVisit.stockist),
            )
            .filter(DcrVisit.dcr_date == today, DcrVisit.user_id.in_(mr_user_ids))
            .order_by(DcrVisit.call_time.desc())
            .all()
            if mr_user_ids
            else []
        )
        visits_by_user: dict[int, list[DcrVisit]] = defaultdict(list)
        for v in visits:
            visits_by_user[v.user_id].append(v)

        # 4. Fetch active territory assignments
        assignments = (
            self.db.query(UserTerritoryAssignment)
            .join(Territory)
            .filter(
                UserTerritoryAssignment.user_id.in_(mr_user_ids),
                UserTerritoryAssignment.unassigned_at.is_(None),
            )
            .all()
            if mr_user_ids
            else []
        )
        territory_by_user = {a.user_id: a.territory.name for a in assignments if a.territory}

        # 5. Fetch approved leaves for today
        active_leaves = (
            self.db.query(LeaveRequest)
            .filter(
                LeaveRequest.status == "APPROVED",
                LeaveRequest.start_date <= today,
                LeaveRequest.end_date >= today,
                LeaveRequest.user_id.in_(mr_user_ids),
            )
            .all()
            if mr_user_ids
            else []
        )
        on_leave_user_ids = {lv.user_id for lv in active_leaves}

        # 6. Fetch pending approvals
        pending_requests = (
            self.db.query(ApprovalRequest).filter(ApprovalRequest.status == "PENDING").all()
        )
        tours_count = sum(1 for r in pending_requests if r.entity_type == "TOUR")
        expenses_count = sum(1 for r in pending_requests if r.entity_type == "EXPENSE")
        leaves_count = sum(1 for r in pending_requests if r.entity_type == "LEAVE")
        total_pending = len(pending_requests)

        # 7. Build MR activity cards
        mr_activities: list[MrLiveActivityItem] = []
        checked_in_count = 0
        total_calls_today = len(visits)
        doctors_visited = sum(1 for v in visits if v.customer_type == "DOCTOR")
        chemists_visited = sum(1 for v in visits if v.customer_type == "CHEMIST")
        total_pob_today = float(sum(float(v.pob_amount or 0.0) for v in visits))

        for user in mr_users:
            att = attendance_by_user.get(user.id)
            user_visits = visits_by_user.get(user.id, [])
            user_calls_count = len(user_visits)
            user_doctors = sum(1 for v in user_visits if v.customer_type == "DOCTOR")
            user_chemists = sum(1 for v in user_visits if v.customer_type == "CHEMIST")

            is_checked_in = bool(att and att.check_in_time)
            if is_checked_in:
                checked_in_count += 1

            # Status determination
            if user.id in on_leave_user_ids:
                status_str = "ON_LEAVE"
            elif not is_checked_in:
                status_str = "NOT_CHECKED_IN"
            elif user_visits:
                latest_call = user_visits[0].call_time
                minutes_since_call = (
                    int((now - latest_call).total_seconds() / 60) if latest_call else 999
                )
                status_str = "VISITING" if minutes_since_call <= 120 else "IDLE"
            else:
                minutes_since_checkin = (
                    int((now - att.check_in_time).total_seconds() / 60)
                    if att and att.check_in_time
                    else 999
                )
                status_str = "CHECKED_IN" if minutes_since_checkin <= 120 else "IDLE"

            # Last activity information
            last_activity_text: str | None = None
            last_activity_time: datetime | None = None
            is_verified = True
            lat: float | None = None
            lng: float | None = None

            if user_visits:
                latest_visit = user_visits[0]
                cust_name = "Customer"
                if latest_visit.doctor:
                    cust_name = f"Dr. {latest_visit.doctor.full_name}"
                elif latest_visit.chemist:
                    cust_name = latest_visit.chemist.shop_name
                elif latest_visit.hospital:
                    cust_name = latest_visit.hospital.name
                elif latest_visit.stockist:
                    cust_name = latest_visit.stockist.agency_name

                last_activity_text = f"Visited {cust_name}"
                last_activity_time = latest_visit.call_time
                is_verified = latest_visit.is_geofence_verified
                lat = latest_visit.latitude
                lng = latest_visit.longitude
            elif att and att.check_in_time:
                last_activity_text = "Checked in for field duty"
                last_activity_time = att.check_in_time
                is_verified = not att.check_in_mock_flag
                lat = att.check_in_latitude
                lng = att.check_in_longitude
            else:
                last_activity_text = "Not checked in today"

            minutes_ago = (
                max(0, int((now - last_activity_time).total_seconds() / 60))
                if last_activity_time
                else None
            )

            mr_activities.append(
                MrLiveActivityItem(
                    user_id=user.id,
                    mr_name=user.full_name,
                    employee_code=f"EMP-{user.id:04d}",
                    profile_photo=None,
                    territory_name=territory_by_user.get(user.id),
                    status=status_str,
                    check_in_time=att.check_in_time if att else None,
                    calls_count=user_calls_count,
                    doctors_count=user_doctors,
                    chemists_count=user_chemists,
                    samples_count=0,
                    calls_target=12,
                    last_activity_text=last_activity_text,
                    last_activity_time=last_activity_time,
                    last_activity_minutes_ago=minutes_ago,
                    is_verified=is_verified,
                    latitude=lat,
                    longitude=lng,
                )
            )

        # Summary strip
        total_mrs = len(mr_users)
        not_checked_in_count = max(0, total_mrs - checked_in_count)
        attendance_pct = round((checked_in_count / total_mrs * 100), 1) if total_mrs > 0 else 0.0

        summary = LiveActivitySummary(
            checked_in_count=checked_in_count,
            total_mrs=total_mrs,
            total_calls_today=total_calls_today,
            doctors_visited=doctors_visited,
            chemists_visited=chemists_visited,
            total_pob_today=round(total_pob_today, 2),
            attendance_pct=attendance_pct,
            not_checked_in_count=not_checked_in_count,
        )

        pending_summary = PendingApprovalsSummary(
            tours_count=tours_count,
            expenses_count=expenses_count,
            leaves_count=leaves_count,
            total_pending=total_pending,
        )

        return AdminLiveActivityResponse(
            summary=summary,
            mr_activities=mr_activities,
            pending_approvals=pending_summary,
        )

    def get_mr_dashboard(self, user_id: int) -> MrDashboardResponse:
        """Fetch personal performance and KPI rollup for field MR."""
        today = date.today()

        # 1. Today's attendance
        att = (
            self.db.query(Attendance)
            .filter(Attendance.user_id == user_id, Attendance.date == today)
            .first()
        )
        if att and att.check_out_time:
            att_status = "CHECKED_OUT"
        elif att and att.check_in_time:
            att_status = "CHECKED_IN"
        else:
            att_status = "NOT_CHECKED_IN"

        # 2. Today's visits
        today_visits = (
            self.db.query(DcrVisit)
            .filter(DcrVisit.user_id == user_id, DcrVisit.dcr_date == today)
            .all()
        )
        visits_today = len(today_visits)
        doctors_visited = sum(1 for v in today_visits if v.customer_type == "DOCTOR")
        chemists_visited = sum(1 for v in today_visits if v.customer_type == "CHEMIST")
        pob_today = float(sum(float(v.pob_amount or 0.0) for v in today_visits))

        # 3. Monthly visits and POB
        month_visits = (
            self.db.query(DcrVisit)
            .filter(
                DcrVisit.user_id == user_id,
                extract("year", DcrVisit.dcr_date) == today.year,
                extract("month", DcrVisit.dcr_date) == today.month,
            )
            .all()
        )
        monthly_visits = len(month_visits)
        monthly_pob = float(sum(float(v.pob_amount or 0.0) for v in month_visits))

        # 4. Pending followups
        pending_followups = (
            self.db.query(func.count(FollowUp.id))
            .filter(
                FollowUp.user_id == user_id,
                FollowUp.status == "PENDING",
            )
            .scalar()
            or 0
        )

        return MrDashboardResponse(
            user_id=user_id,
            today_date=today,
            attendance_status=att_status,
            check_in_time=att.check_in_time if att else None,
            check_out_time=att.check_out_time if att else None,
            visits_today=visits_today,
            visits_target=12,
            doctors_visited=doctors_visited,
            chemists_visited=chemists_visited,
            pob_today=round(pob_today, 2),
            monthly_visits=monthly_visits,
            monthly_target=240,
            monthly_pob=round(monthly_pob, 2),
            pending_followups_count=int(pending_followups),
        )

    def get_manager_dashboard(self, manager_id: int) -> ManagerDashboardResponse:
        """Fetch team performance and pending approvals overview for Manager."""
        today = date.today()

        # 1. Fetch assigned MRs
        assigned_mrs = (
            self.db.query(ManagerMRAssignment)
            .filter(
                ManagerMRAssignment.manager_id == manager_id,
                ManagerMRAssignment.unassigned_at.is_(None),
            )
            .all()
        )
        mr_ids = [a.mr_id for a in assigned_mrs]
        if not mr_ids:
            # Fallback to all MR users if no explicit 1-1 assignment table rows
            mr_ids = [
                u.id
                for u in self.db.query(User)
                .join(User.role)
                .filter(Role.code == "MR", User.is_active == True)  # noqa: E712
                .all()
            ]

        team_size = len(mr_ids)
        if not mr_ids:
            return ManagerDashboardResponse()

        # 2. Checked in count today
        checked_in = (
            self.db.query(func.count(Attendance.id))
            .filter(
                Attendance.user_id.in_(mr_ids),
                Attendance.date == today,
                Attendance.check_in_time.isnot(None),
            )
            .scalar()
            or 0
        )

        # 3. Team visits today
        team_visits = (
            self.db.query(DcrVisit)
            .filter(DcrVisit.user_id.in_(mr_ids), DcrVisit.dcr_date == today)
            .all()
        )
        calls_today = len(team_visits)
        total_pob_today = float(sum(float(v.pob_amount or 0.0) for v in team_visits))

        # 4. Pending approvals count
        pending_approvals = (
            self.db.query(func.count(ApprovalRequest.id))
            .filter(
                ApprovalRequest.requester_id.in_(mr_ids),
                ApprovalRequest.status == "PENDING",
            )
            .scalar()
            or 0
        )

        # 5. Team coverage percentage (team calls vs target of 12 calls per MR)
        target_calls = team_size * 12
        coverage_pct = round((calls_today / target_calls * 100), 1) if target_calls > 0 else 0.0

        return ManagerDashboardResponse(
            team_size=team_size,
            checked_in_today=int(checked_in),
            calls_today=calls_today,
            total_pob_today=round(total_pob_today, 2),
            pending_approvals_count=int(pending_approvals),
            team_coverage_pct=min(100.0, coverage_pct),
        )
