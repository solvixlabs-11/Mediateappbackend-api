"""Dashboard service layer providing live field activity, MR KPI cards, and manager oversight."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time

from fastapi import HTTPException, status
from sqlalchemy import extract, func
from sqlalchemy.orm import Session, selectinload

from app.modules.approvals.models import ApprovalRequest
from app.modules.attendance.models import Attendance
from app.modules.customers.models import Chemist, Doctor, Stockist
from app.modules.dashboard.metrics import MetricHandlerContext, metric_registry
from app.modules.dashboard.schemas import (
    AdminLiveActivityResponse,
    EmployeeVisitSummaryItem,
    LiveActivitySummary,
    ManagerDashboardResponse,
    MetricCardRowItem,
    MetricDetailResponse,
    MrDashboardResponse,
    MrLiveActivityItem,
    PendingApprovalsSummary,
    VisitsSummaryResponse,
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

    def get_visits_summary(
        self,
        from_date: date,
        to_date: date,
        employee_ids: list[int] | None = None,
        state_id: int | None = None,
        territory_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> VisitsSummaryResponse:
        """Fetch aggregated visits summary per field employee within date range."""
        query = (
            self.db.query(User)
            .join(User.role)
            .filter(
                Role.code.in_(["MR", "MANAGER"]),
                User.is_active == True,  # noqa: E712
                User.is_deleted == False,  # noqa: E712
            )
        )

        if employee_ids:
            query = query.filter(User.id.in_(employee_ids))

        if territory_id:
            query = query.join(UserTerritoryAssignment).filter(
                UserTerritoryAssignment.territory_id == territory_id,
                UserTerritoryAssignment.unassigned_at.is_(None),
            )
        elif state_id:
            query = (
                query.join(UserTerritoryAssignment)
                .join(Territory, UserTerritoryAssignment.territory_id == Territory.id)
                .filter(
                    Territory.state_id == state_id,
                    UserTerritoryAssignment.unassigned_at.is_(None),
                )
            )

        user_id_query = query.with_entities(User.id).distinct()
        total_users = user_id_query.count()

        paged_user_ids = (
            user_id_query.order_by(User.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        user_ids = [u[0] for u in paged_user_ids]

        if not user_ids:
            return VisitsSummaryResponse(
                items=[], total=total_users, page=page, page_size=page_size
            )

        users = (
            self.db.query(User)
            .filter(User.id.in_(user_ids))
            .options(
                selectinload(User.territory_assignments).joinedload(
                    UserTerritoryAssignment.territory
                )
            )
            .order_by(User.id.asc())
            .all()
        )

        user_ids = [u.id for u in users]
        if not user_ids:
            return VisitsSummaryResponse(
                items=[], total=total_users, page=page, page_size=page_size
            )

        # Query DCR visits in date range
        visits = (
            self.db.query(DcrVisit)
            .filter(
                DcrVisit.user_id.in_(user_ids),
                DcrVisit.dcr_date >= from_date,
                DcrVisit.dcr_date <= to_date,
            )
            .all()
        )

        visits_by_user = defaultdict(list)
        for v in visits:
            visits_by_user[v.user_id].append(v)

        # Query attendances in date range
        attendances = (
            self.db.query(Attendance)
            .filter(
                Attendance.user_id.in_(user_ids),
                Attendance.date >= from_date,
                Attendance.date <= to_date,
            )
            .all()
        )

        att_by_user = defaultdict(list)
        for a in attendances:
            att_by_user[a.user_id].append(a)

        # Batch query newly created customers in date range
        start_dt = datetime.combine(from_date, time.min)
        end_dt = datetime.combine(to_date, time.max)

        new_chem_counts = dict(
            self.db.query(Chemist.created_by, func.count(Chemist.id))
            .filter(Chemist.created_by.in_(user_ids), Chemist.created_at >= start_dt, Chemist.created_at <= end_dt)
            .group_by(Chemist.created_by)
            .all()
        )
        new_doc_counts = dict(
            self.db.query(Doctor.created_by, func.count(Doctor.id))
            .filter(Doctor.created_by.in_(user_ids), Doctor.created_at >= start_dt, Doctor.created_at <= end_dt)
            .group_by(Doctor.created_by)
            .all()
        )
        new_stock_counts = dict(
            self.db.query(Stockist.created_by, func.count(Stockist.id))
            .filter(Stockist.created_by.in_(user_ids), Stockist.created_at >= start_dt, Stockist.created_at <= end_dt)
            .group_by(Stockist.created_by)
            .all()
        )

        # Batch active doctor territory mappings
        all_assigned_t_ids = {
            a.territory_id
            for u in users
            for a in getattr(u, "territory_assignments", [])
            if getattr(a, "unassigned_at", None) is None and a.territory_id
        }
        doc_terr_pairs = (
            self.db.query(Doctor.id, Doctor.territory_id)
            .filter(Doctor.territory_id.in_(all_assigned_t_ids), Doctor.is_active == True, Doctor.is_deleted == False)  # noqa: E712
            .all()
            if all_assigned_t_ids
            else []
        )

        items: list[EmployeeVisitSummaryItem] = []
        for user in users:
            u_visits = visits_by_user[user.id]
            u_atts = att_by_user[user.id]

            # Primary territory
            assignments = getattr(user, "territory_assignments", []) or []
            primary_assignment = next(
                (a for a in assignments if getattr(a, "unassigned_at", None) is None and getattr(a, "territory", None)),
                None,
            )
            terr = primary_assignment.territory if primary_assignment else None
            hq_name = (
                getattr(terr, "headquarters", None)
                or getattr(terr, "name", None)
                or getattr(terr, "hq_name", None)
                or "Headquarter (HQ)"
                if terr
                else "Headquarter (HQ)"
            )
            hq_code = getattr(terr, "code", "HQ") if terr else "HQ"

            # Counts from visits
            doctor_visits = sum(1 for v in u_visits if v.customer_type == "DOCTOR")
            chemist_visits = sum(1 for v in u_visits if v.customer_type == "CHEMIST")
            stockist_visits = sum(1 for v in u_visits if v.customer_type == "STOCKIST")

            # Morning (<14:00) vs Evening (>=14:00)
            morning_calls = sum(1 for v in u_visits if v.call_time and v.call_time.hour < 14)
            evening_calls = sum(1 for v in u_visits if v.call_time and v.call_time.hour >= 14)

            # Call times
            call_times = [v.call_time for v in u_visits if v.call_time]
            first_call = min(call_times).strftime("%H:%M") if call_times else None
            last_call = max(call_times).strftime("%H:%M") if call_times else None

            # Attendance times & duration
            check_ins = [a.check_in_time for a in u_atts if a.check_in_time]
            check_outs = [a.check_out_time for a in u_atts if a.check_out_time]
            punch_in_time = min(check_ins).strftime("%H:%M") if check_ins else None
            punch_out_time = max(check_outs).strftime("%H:%M") if check_outs else None
            work_duration = sum(a.total_work_minutes or 0 for a in u_atts) if u_atts else None

            # Working days attended
            working_days = len(u_atts) if u_atts else (1 if u_visits else 0)
            doc_avg = round(doctor_visits / working_days, 1) if working_days > 0 else 0.0

            # Missing doctors calculation
            user_terr_ids = [a.territory_id for a in assignments if getattr(a, "unassigned_at", None) is None and a.territory_id]
            visited_doc_ids = {v.doctor_id for v in u_visits if v.customer_type == "DOCTOR" and v.doctor_id}
            assigned_docs = [d_id for d_id, t_id in doc_terr_pairs if t_id in user_terr_ids]
            missing_docs_count = len(set(assigned_docs) - visited_doc_ids)

            # New customers counts
            new_chem = new_chem_counts.get(user.id, 0)
            new_doc = new_doc_counts.get(user.id, 0)
            new_stock = new_stock_counts.get(user.id, 0)

            # Build the 16 dynamic metric rows
            metric_rows = [
                MetricCardRowItem(
                    key="chemist_visits",
                    label="CHEMIST VISITS",
                    value=chemist_visits,
                    formatted_value=str(chemist_visits),
                    kind="TABLE",
                    color_group="primary",
                    status="AVAILABLE",
                ),
                MetricCardRowItem(
                    key="new_chemist_visits",
                    label="NEW CHEMIST VISITS",
                    value=new_chem,
                    formatted_value=str(new_chem),
                    kind="TABLE",
                    color_group="primary",
                    status="AVAILABLE",
                ),
                MetricCardRowItem(
                    key="doctor_visits",
                    label="DOCTOR VISITS",
                    value=doctor_visits,
                    formatted_value=str(doctor_visits),
                    kind="TABLE",
                    color_group="primary",
                    status="AVAILABLE",
                ),
                MetricCardRowItem(
                    key="new_doctor_visits",
                    label="NEW DOCTOR VISITS",
                    value=new_doc,
                    formatted_value=str(new_doc),
                    kind="TABLE",
                    color_group="primary",
                    status="AVAILABLE",
                ),
                MetricCardRowItem(
                    key="stockist_visits",
                    label="STOCKIST VISITS",
                    value=stockist_visits,
                    formatted_value=str(stockist_visits),
                    kind="TABLE",
                    color_group="primary",
                    status="AVAILABLE",
                ),
                MetricCardRowItem(
                    key="new_stockist_visits",
                    label="NEW STOCKIST VISITS",
                    value=new_stock,
                    formatted_value=str(new_stock),
                    kind="TABLE",
                    color_group="primary",
                    status="AVAILABLE",
                ),
                MetricCardRowItem(
                    key="doctor_call_average",
                    label="DOCTOR CALL AVERAGE",
                    value=doc_avg,
                    formatted_value=f"{doc_avg:.1f}",
                    kind="TABLE",
                    color_group="success",
                    status="AVAILABLE",
                ),
                MetricCardRowItem(
                    key="missing_doctor",
                    label="MISSING DOCTOR",
                    value=missing_docs_count,
                    formatted_value=str(missing_docs_count),
                    kind="TABLE",
                    color_group="success",
                    status="AVAILABLE",
                ),
                MetricCardRowItem(
                    key="punch_in_time",
                    label="PUNCHING IN TIME",
                    value=punch_in_time,
                    formatted_value=punch_in_time or "--:--",
                    kind="RECORD",
                    color_group="primary",
                    status="AVAILABLE" if punch_in_time else "EMPTY",
                ),
                MetricCardRowItem(
                    key="first_call_time",
                    label="FIRST CALL TIME",
                    value=first_call,
                    formatted_value=first_call or "--:--",
                    kind="RECORD",
                    color_group="primary",
                    status="AVAILABLE" if first_call else "EMPTY",
                ),
                MetricCardRowItem(
                    key="last_call_time",
                    label="LAST CALL TIME",
                    value=last_call,
                    formatted_value=last_call or "--:--",
                    kind="RECORD",
                    color_group="primary",
                    status="AVAILABLE" if last_call else "EMPTY",
                ),
                MetricCardRowItem(
                    key="punch_out_time",
                    label="PUNCHOUT TIME",
                    value=punch_out_time,
                    formatted_value=punch_out_time or "--:--",
                    kind="RECORD",
                    color_group="primary",
                    status="AVAILABLE" if punch_out_time else "EMPTY",
                ),
                MetricCardRowItem(
                    key="morning_calls",
                    label="MORNING CALL DETAILS",
                    value=morning_calls,
                    formatted_value=str(morning_calls),
                    kind="TABLE",
                    color_group="primary",
                    status="AVAILABLE",
                ),
                MetricCardRowItem(
                    key="evening_calls",
                    label="EVENING CALLS",
                    value=evening_calls,
                    formatted_value=str(evening_calls),
                    kind="TABLE",
                    color_group="primary",
                    status="AVAILABLE",
                ),
                MetricCardRowItem(
                    key="work_duration",
                    label="WORK DURATION",
                    value=work_duration,
                    formatted_value=f"{work_duration // 60:02d}:{work_duration % 60:02d}" if work_duration else "--:--",
                    kind="TIMELINE",
                    color_group="primary",
                    status="AVAILABLE",
                ),
                MetricCardRowItem(
                    key="total_pob",
                    label="TOTAL POB",
                    value=None,
                    formatted_value="-",
                    kind="TABLE",
                    color_group="danger",
                    status="COMING_SOON",
                    unavailable_reason="Order billing and POB processing module will be activated in Phase 8",
                ),
            ]

            items.append(
                EmployeeVisitSummaryItem(
                    id=str(user.id),
                    employee_id=str(user.id),
                    employee_code=getattr(user, "employee_code", f"EMP-{user.id:04d}"),
                    employee_name=user.full_name,
                    photo_url=getattr(user, "avatar_url", None),
                    hq_name=hq_name,
                    hq_code=hq_code,
                    division_name=None,
                    chemist_visits=chemist_visits,
                    new_chemist_visits=new_chem,
                    doctor_visits=doctor_visits,
                    new_doctor_visits=new_doc,
                    stockist_visits=stockist_visits,
                    new_stockist_visits=new_stock,
                    doctor_call_average=doc_avg,
                    missing_doctor=missing_docs_count,
                    punch_in_time=punch_in_time,
                    first_call_time=first_call,
                    last_call_time=last_call,
                    punch_out_time=punch_out_time,
                    morning_calls=morning_calls,
                    evening_calls=evening_calls,
                    work_duration_minutes=work_duration,
                    total_pob=None,
                    metrics=metric_rows,
                )
            )

        return VisitsSummaryResponse(
            items=items,
            total=total_users,
            page=page,
            page_size=page_size,
        )

    def get_metric_drilldown(
        self,
        employee_id: int,
        metric_key: str,
        from_date: date,
        to_date: date,
        division_ids: list[int] | None = None,
        state_id: int | None = None,
        territory_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> MetricDetailResponse:
        """Fetch detailed drilldown data for a specific employee and metric."""
        employee = (
            self.db.query(User)
            .filter(User.id == employee_id, User.is_deleted == False)  # noqa: E712
            .first()
        )
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee with ID {employee_id} not found",
            )

        handler = metric_registry.get(metric_key)
        if not handler:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown metric key '{metric_key}'. Available: {metric_registry.get_keys()}",
            )

        ctx = MetricHandlerContext(
            db=self.db,
            employee=employee,
            from_date=from_date,
            to_date=to_date,
            division_ids=division_ids,
            state_id=state_id,
            territory_id=territory_id,
            page=page,
            page_size=page_size,
        )
        return handler.get_detail(ctx)

    def export_metric_drilldown(
        self,
        employee_id: int,
        metric_key: str,
        from_date: date,
        to_date: date,
        division_ids: list[int] | None = None,
        state_id: int | None = None,
        territory_id: int | None = None,
    ) -> bytes:
        """Export metric drilldown table to XLSX spreadsheet bytes."""
        employee = (
            self.db.query(User)
            .filter(User.id == employee_id, User.is_deleted == False)  # noqa: E712
            .first()
        )
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee with ID {employee_id} not found",
            )

        handler = metric_registry.get(metric_key)
        if not handler:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown metric key '{metric_key}'",
            )

        if not handler.can_export or handler.status == "COMING_SOON":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Export not available for '{metric_key}' ({handler.unavailable_reason or 'No export format'})",
            )

        ctx = MetricHandlerContext(
            db=self.db,
            employee=employee,
            from_date=from_date,
            to_date=to_date,
            division_ids=division_ids,
            state_id=state_id,
            territory_id=territory_id,
            page=1,
            page_size=5000,
        )
        data = handler.export_xlsx(ctx)
        if not data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate XLSX spreadsheet export",
            )
        return data

