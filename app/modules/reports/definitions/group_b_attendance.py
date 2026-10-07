"""Group B: Attendance and daily work reports (Reports 4 to 6)."""

from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.attendance.models import Attendance
from app.modules.dcr.models import DcrVisit, PlannedVisit
from app.modules.leaves.models import LeaveRequest
from app.modules.reports.base import BaseReport, ReportRegistry
from app.modules.reports.schemas import ReportColumn, ReportFilterParams, ReportFilterSchema
from app.modules.reports.utils import utc_to_ist_date, utc_to_ist_time
from app.modules.territories.models import UserTerritoryAssignment
from app.modules.users.models import User


class MrDailyPunchingReport(BaseReport):
    """Report 4: MR Daily Punching (NOW).

    Columns: Date, MR, Punch-in time and place, Punch-out time and place, Hours, Late, Work type.
    """

    key = "mr_daily_punching"
    title = "MR Daily Punching"
    group = "Attendance and Daily Work"
    description = "Field check-in and check-out logs with geolocated timestamps, total operational hours, and late punching flags."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    report_number = 4
    status = "NOW"
    is_ready = True
    filter_schema = ReportFilterSchema(
        date_range=True,
        mr_picker=True,
        territory_picker=True,
        work_type_picker=True,
    )

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="date", label="Date", type="date", align="center"),
            ReportColumn(key="mr_name", label="MR", type="string"),
            ReportColumn(key="punch_in", label="Punch-in Time & Place", type="string"),
            ReportColumn(key="punch_out", label="Punch-out Time & Place", type="string"),
            ReportColumn(key="hours", label="Hours", type="number", align="right"),
            ReportColumn(key="late", label="Late", type="status", align="center"),
            ReportColumn(key="work_type", label="Work Type", type="string", align="center"),
        ]

    def run_query(
        self,
        db: Session,
        filters: ReportFilterParams,
        user_ids: list[int] | None,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> list[dict[str, Any]]:
        stmt = (
            select(Attendance)
            .options(selectinload(Attendance.user))
            .order_by(Attendance.date.desc(), Attendance.check_in_time.desc())
        )

        if user_ids is not None:
            stmt = stmt.where(Attendance.user_id.in_(user_ids))

        if filters.territory_id:
            terr_user_ids = db.execute(
                select(UserTerritoryAssignment.user_id).where(
                    UserTerritoryAssignment.territory_id == filters.territory_id
                )
            ).scalars().all()
            stmt = stmt.where(Attendance.user_id.in_(terr_user_ids))

        if start_utc and end_utc:
            s_d = start_utc.date()
            e_d = end_utc.date()
            stmt = stmt.where(Attendance.date >= s_d, Attendance.date <= e_d)

        if filters.work_type and filters.work_type != "All":
            stmt = stmt.where(func.lower(Attendance.status) == filters.work_type.lower())

        records = list(db.scalars(stmt).all())
        results: list[dict[str, Any]] = []

        for att in records:
            # Punch in formatting
            in_t = utc_to_ist_time(att.check_in_time) if att.check_in_time else "-"
            in_place = f" ({att.check_in_address})" if att.check_in_address else ""
            punch_in_str = f"{in_t}{in_place}" if in_t != "-" else "-"

            # Punch out formatting
            out_t = utc_to_ist_time(att.check_out_time) if att.check_out_time else "-"
            out_place = f" ({att.check_out_address})" if att.check_out_address else ""
            punch_out_str = f"{out_t}{out_place}" if out_t != "-" else "-"

            hrs = round((att.total_work_minutes or 0) / 60.0, 1)

            # Check late: if check_in_time after 09:30 AM IST (04:00 UTC)
            is_late = "No"
            if att.check_in_time:
                # 09:30 AM IST is 04:00 AM UTC
                in_hour_ist = (att.check_in_time.hour + 5 + (att.check_in_time.minute + 30) // 60) % 24
                in_min_ist = (att.check_in_time.minute + 30) % 60
                if (in_hour_ist > 9) or (in_hour_ist == 9 and in_min_ist > 30):
                    is_late = "Yes"

            results.append({
                "date": att.date.strftime("%d-%b-%Y"),
                "mr_name": att.user.full_name if att.user else f"MR #{att.user_id}",
                "punch_in": punch_in_str,
                "punch_out": punch_out_str,
                "hours": hrs,
                "late": is_late,
                "work_type": att.status.replace("_", " ").title(),
            })

        return results

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        total = len(items)
        late_cnt = sum(1 for it in items if it.get("late") == "Yes")
        total_hrs = sum(it.get("hours", 0) for it in items)
        avg_hrs = round(total_hrs / total, 1) if total else 0.0
        return {
            "total_punches": total,
            "late_punches": late_cnt,
            "average_work_hours": avg_hrs,
        }


class MrWiseAttendanceReport(BaseReport):
    """Report 5: MR Wise Attendance Report (NOW).

    Month matrix: MR rows, day columns with P (present), A (absent), L (leave), W (weekly off);
    totals present, absent, leave, late.
    Fits in landscape PDF and Excel with frozen first column.
    """

    key = "mr_wise_attendance_report"
    title = "MR Wise Attendance Report"
    group = "Attendance and Daily Work"
    description = "Monthly calendar matrix showing daily attendance status (P/A/L/W) and total working days per MR."
    landscape = True
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    report_number = 5
    status = "NOW"
    is_ready = True
    filter_schema = ReportFilterSchema(
        date_range=True,
        mr_picker=True,
        territory_picker=True,
    )

    def get_columns(self) -> list[ReportColumn]:
        cols = [
            ReportColumn(key="mr_name", label="MR Name", type="string"),
            ReportColumn(key="emp_code", label="Emp Code", type="string", align="center"),
        ]
        # Day 1 to Day 31
        for day in range(1, 32):
            cols.append(ReportColumn(key=f"d_{day}", label=f"{day:02d}", type="string", align="center"))

        cols.extend([
            ReportColumn(key="present", label="Present", type="number", align="right"),
            ReportColumn(key="absent", label="Absent", type="number", align="right"),
            ReportColumn(key="leave", label="Leave", type="number", align="right"),
            ReportColumn(key="late", label="Late", type="number", align="right"),
        ])
        return cols

    def run_query(
        self,
        db: Session,
        filters: ReportFilterParams,
        user_ids: list[int] | None,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> list[dict[str, Any]]:
        # Target month and year
        ref_date = start_utc.date() if start_utc else date.today()
        year = ref_date.year
        month = ref_date.month
        _, num_days = calendar.monthrange(year, month)

        # Users list
        u_stmt = select(User).order_by(User.full_name.asc())
        if user_ids is not None:
            u_stmt = u_stmt.where(User.id.in_(user_ids))
        if filters.territory_id:
            terr_user_ids = db.execute(
                select(UserTerritoryAssignment.user_id).where(
                    UserTerritoryAssignment.territory_id == filters.territory_id
                )
            ).scalars().all()
            u_stmt = u_stmt.where(User.id.in_(terr_user_ids))
        users = list(db.scalars(u_stmt).all())

        # Attendance map (user_id, day) -> att
        m_start = date(year, month, 1)
        m_end = date(year, month, num_days)
        att_records = list(
            db.scalars(
                select(Attendance).where(
                    Attendance.date >= m_start,
                    Attendance.date <= m_end,
                )
            ).all()
        )
        att_map: dict[tuple[int, int], Attendance] = {
            (a.user_id, a.date.day): a for a in att_records
        }

        # Leave requests map
        leaves = list(
            db.scalars(
                select(LeaveRequest).where(
                    LeaveRequest.status == "APPROVED",
                    LeaveRequest.start_date <= m_end,
                    LeaveRequest.end_date >= m_start,
                )
            ).all()
        )

        leave_set: set[tuple[int, int]] = set()
        for l in leaves:
            cur = max(l.start_date, m_start)
            fin = min(l.end_date, m_end)
            while cur <= fin:
                leave_set.add((l.user_id, cur.day))
                cur += timedelta(days=1)

        results: list[dict[str, Any]] = []
        today_date = date.today()

        for u in users:
            row: dict[str, Any] = {
                "mr_name": u.full_name,
                "emp_code": f"EMP-{u.id:04d}",
                "present": 0,
                "absent": 0,
                "leave": 0,
                "late": 0,
            }

            for d in range(1, 32):
                col_key = f"d_{d}"
                if d > num_days:
                    row[col_key] = "-"
                    continue

                day_date = date(year, month, d)
                is_sunday = day_date.weekday() == 6

                att = att_map.get((u.id, d))
                if att:
                    if att.status in ["PRESENT", "HALF_DAY"]:
                        row[col_key] = "P"
                        row["present"] += 1
                        # Check late
                        if att.check_in_time:
                            in_h = (att.check_in_time.hour + 5 + (att.check_in_time.minute + 30) // 60) % 24
                            in_m = (att.check_in_time.minute + 30) % 60
                            if (in_h > 9) or (in_h == 9 and in_m > 30):
                                row["late"] += 1
                    elif att.status == "LEAVE":
                        row[col_key] = "L"
                        row["leave"] += 1
                    else:
                        row[col_key] = "P"
                        row["present"] += 1
                elif (u.id, d) in leave_set:
                    row[col_key] = "L"
                    row["leave"] += 1
                elif is_sunday:
                    row[col_key] = "W"
                elif day_date <= today_date:
                    row[col_key] = "A"
                    row["absent"] += 1
                else:
                    row[col_key] = "-"

            results.append(row)

        return results

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "total_mrs": len(items),
            "total_present_days": sum(it.get("present", 0) for it in items),
            "total_absent_days": sum(it.get("absent", 0) for it in items),
            "total_leave_days": sum(it.get("leave", 0) for it in items),
            "total_late_events": sum(it.get("late", 0) for it in items),
        }


class DailyWorkReport(BaseReport):
    """Report 6: Daily Work Report (NOW).

    Columns: Date, MR, Work type, Planned visits, Doctor calls, Chemist calls,
    Stockist calls, Hospital calls, Total calls, DCR submitted, Hours, Remarks.
    """

    key = "daily_work_report"
    title = "Daily Work Report"
    group = "Attendance and Daily Work"
    description = "Consolidated daily activity showing work type, customer visits breakdown, and DCR submission status."
    landscape = True
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    report_number = 6
    status = "NOW"
    is_ready = True
    filter_schema = ReportFilterSchema(
        date_range=True,
        mr_picker=True,
        territory_picker=True,
        work_type_picker=True,
    )

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="date", label="Date", type="date", align="center"),
            ReportColumn(key="mr_name", label="MR", type="string"),
            ReportColumn(key="work_type", label="Work Type", type="string", align="center"),
            ReportColumn(key="planned_visits", label="Planned", type="number", align="right"),
            ReportColumn(key="doctor_calls", label="Doctor", type="number", align="right"),
            ReportColumn(key="chemist_calls", label="Chemist", type="number", align="right"),
            ReportColumn(key="stockist_calls", label="Stockist", type="number", align="right"),
            ReportColumn(key="hospital_calls", label="Hospital", type="number", align="right"),
            ReportColumn(key="total_calls", label="Total Calls", type="number", align="right"),
            ReportColumn(key="dcr_submitted", label="DCR Submitted", type="status", align="center"),
            ReportColumn(key="hours", label="Hours", type="number", align="right"),
            ReportColumn(key="remarks", label="Remarks", type="string"),
        ]

    def run_query(
        self,
        db: Session,
        filters: ReportFilterParams,
        user_ids: list[int] | None,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> list[dict[str, Any]]:
        # Fetch attendances
        att_stmt = (
            select(Attendance)
            .options(selectinload(Attendance.user))
            .order_by(Attendance.date.desc())
        )
        if user_ids is not None:
            att_stmt = att_stmt.where(Attendance.user_id.in_(user_ids))

        terr_user_ids = None
        if filters.territory_id:
            terr_user_ids = db.execute(
                select(UserTerritoryAssignment.user_id).where(
                    UserTerritoryAssignment.territory_id == filters.territory_id
                )
            ).scalars().all()
            att_stmt = att_stmt.where(Attendance.user_id.in_(terr_user_ids))

        if filters.work_type and filters.work_type != "All":
            att_stmt = att_stmt.where(func.lower(Attendance.status) == filters.work_type.lower())

        if start_utc and end_utc:
            att_stmt = att_stmt.where(Attendance.date >= start_utc.date(), Attendance.date <= end_utc.date())

        attendances = list(db.scalars(att_stmt).all())

        # Fetch Planned visits breakdown
        pv_stmt = select(
            PlannedVisit.user_id,
            PlannedVisit.plan_date,
            func.count(PlannedVisit.id),
        ).group_by(PlannedVisit.user_id, PlannedVisit.plan_date)
        if user_ids is not None:
            pv_stmt = pv_stmt.where(PlannedVisit.user_id.in_(user_ids))
        if terr_user_ids is not None:
            pv_stmt = pv_stmt.where(PlannedVisit.user_id.in_(terr_user_ids))
        if start_utc and end_utc:
            pv_stmt = pv_stmt.where(PlannedVisit.plan_date >= start_utc.date(), PlannedVisit.plan_date <= end_utc.date())

        planned_counts = {(uid, pdate): cnt for uid, pdate, cnt in db.execute(pv_stmt).all()}

        # Fetch DCR calls breakdown
        dcr_stmt = select(
            DcrVisit.user_id,
            DcrVisit.dcr_date,
            DcrVisit.customer_type,
            func.count(DcrVisit.id),
        ).group_by(DcrVisit.user_id, DcrVisit.dcr_date, DcrVisit.customer_type)
        if user_ids is not None:
            dcr_stmt = dcr_stmt.where(DcrVisit.user_id.in_(user_ids))
        if terr_user_ids is not None:
            dcr_stmt = dcr_stmt.where(DcrVisit.user_id.in_(terr_user_ids))
        if start_utc and end_utc:
            dcr_stmt = dcr_stmt.where(DcrVisit.dcr_date >= start_utc.date(), DcrVisit.dcr_date <= end_utc.date())

        dcr_rows = db.execute(dcr_stmt).all()
        call_breakdown: dict[tuple[int, date], dict[str, int]] = {}
        for uid, ddate, ctype, cnt in dcr_rows:
            entry = call_breakdown.setdefault((uid, ddate), {"DOCTOR": 0, "CHEMIST": 0, "STOCKIST": 0, "HOSPITAL": 0})
            if ctype in entry:
                entry[ctype] = cnt

        results: list[dict[str, Any]] = []
        for att in attendances:
            key = (att.user_id, att.date)
            calls = call_breakdown.get(key, {"DOCTOR": 0, "CHEMIST": 0, "STOCKIST": 0, "HOSPITAL": 0})
            doc = calls["DOCTOR"]
            chem = calls["CHEMIST"]
            stock = calls["STOCKIST"]
            hosp = calls["HOSPITAL"]
            tot = doc + chem + stock + hosp
            hrs = round((att.total_work_minutes or 0) / 60.0, 1)

            results.append({
                "date": att.date.strftime("%d-%b-%Y"),
                "mr_name": att.user.full_name if att.user else f"MR #{att.user_id}",
                "work_type": att.status.replace("_", " ").title(),
                "planned_visits": planned_counts.get(key, 0),
                "doctor_calls": doc,
                "chemist_calls": chem,
                "stockist_calls": stock,
                "hospital_calls": hosp,
                "total_calls": tot,
                "dcr_submitted": "Yes" if tot > 0 else "No",
                "hours": hrs,
                "remarks": att.remarks or "-",
            })

        return results

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        tot_days = len(items)
        tot_calls = sum(it.get("total_calls", 0) for it in items)
        avg = round(tot_calls / tot_days, 1) if tot_days else 0.0
        return {
            "total_work_days": tot_days,
            "total_calls": tot_calls,
            "doctor_calls": sum(it.get("doctor_calls", 0) for it in items),
            "chemist_calls": sum(it.get("chemist_calls", 0) for it in items),
            "average_calls_per_day": avg,
        }


ReportRegistry.register(MrDailyPunchingReport)
ReportRegistry.register(MrWiseAttendanceReport)
ReportRegistry.register(DailyWorkReport)
