"""Modularizer creating individual app/modules/reports/definitions/<key>.py for all 32 NOW reports."""

from pathlib import Path

BASE_DIR = Path("E:/Mediate/Mediateappbackend-api/app/modules/reports/definitions")
BASE_DIR.mkdir(parents=True, exist_ok=True)

# 1. daily_call_report.py
(BASE_DIR / "daily_call_report.py").write_text('''"""Daily Call Report (MR Wise Call Summary) / Daily Work Report."""

from datetime import datetime, date
from typing import Any
import calendar
from sqlalchemy import func, select, or_
from sqlalchemy.orm import Session
from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn
from app.modules.dcr.models import DcrVisit
from app.modules.users.models import User
from app.modules.territories.models import Territory, UserTerritoryAssignment


class DailyCallReport(BaseReport):
    key = "daily_call_report"
    title = "Daily Call Report (MR Wise Call Summary) / Daily Work Report"
    group = "Field Activity"
    description = "Per employee per day: doctor, chemist, stockist calls, new customers, first and last call time, hours."
    landscape = True
    allowed_roles = ["ADMIN", "MANAGER", "MR"]

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="date", label="Date", type="date", align="center"),
            ReportColumn(key="employee", label="Employee", type="string"),
            ReportColumn(key="designation", label="Designation", type="string"),
            ReportColumn(key="territory", label="Territory", type="string"),
            ReportColumn(key="doctor_calls", label="Doctor Calls", type="number", align="right"),
            ReportColumn(key="chemist_calls", label="Chemist Calls", type="number", align="right"),
            ReportColumn(key="stockist_calls", label="Stockist Calls", type="number", align="right"),
            ReportColumn(key="total_calls", label="Total Calls", type="number", align="right"),
            ReportColumn(key="first_call", label="First Call", type="string", align="center"),
            ReportColumn(key="last_call", label="Last Call", type="string", align="center"),
            ReportColumn(key="field_hours", label="Hours", type="number", align="right"),
            ReportColumn(key="status", label="Status", type="status", align="center"),
        ]

    def run_query(self, db: Session, filters: Any, user_ids: list[int] | None, start_utc: datetime | None, end_utc: datetime | None) -> list[dict[str, Any]]:
        f_dict = filters if isinstance(filters, dict) else (filters.__dict__ if hasattr(filters, "__dict__") else {})
        month = f_dict.get("month")
        year = f_dict.get("year", datetime.utcnow().year)
        
        q = select(DcrVisit)
        if user_ids:
            q = q.where(DcrVisit.user_id.in_(user_ids))
        if month:
            try:
                m_int = int(month)
                y_int = int(year)
                _, last_day = calendar.monthrange(y_int, m_int)
                d_start = date(y_int, m_int, 1)
                d_end = date(y_int, m_int, last_day)
                q = q.where(DcrVisit.dcr_date >= d_start, DcrVisit.dcr_date <= d_end)
            except Exception:
                pass
        elif start_utc and end_utc:
            q = q.where(DcrVisit.call_time >= start_utc, DcrVisit.call_time <= end_utc)

        visits = db.execute(q).scalars().all()
        grouped: dict[tuple[date, int], list[DcrVisit]] = {}
        for v in visits:
            grouped.setdefault((v.dcr_date, v.user_id), []).append(v)

        rows = []
        user_cache = {u.id: u for u in db.execute(select(User)).scalars().all()}

        for (d_date, u_id), day_visits in sorted(grouped.items(), key=lambda x: (x[0][0], x[0][1]), reverse=True):
            user = user_cache.get(u_id)
            doc_calls = sum(1 for v in day_visits if v.customer_type == "DOCTOR")
            chm_calls = sum(1 for v in day_visits if v.customer_type == "CHEMIST")
            stk_calls = sum(1 for v in day_visits if v.customer_type in ("STOCKIST", "HOSPITAL"))
            call_times = [v.call_time for v in day_visits if v.call_time]
            
            first_c = min(call_times).strftime("%H:%M") if call_times else "-"
            last_c = max(call_times).strftime("%H:%M") if call_times else "-"
            hours = round((max(call_times) - min(call_times)).total_seconds() / 3600.0, 1) if len(call_times) > 1 else 1.0

            rows.append({
                "date": d_date.isoformat(),
                "employee": user.full_name if user else f"User #{u_id}",
                "designation": getattr(user, "designation", "MR") or "MR",
                "territory": getattr(user, "headquarters", "Central") or "Central",
                "doctor_calls": doc_calls,
                "chemist_calls": chm_calls,
                "stockist_calls": stk_calls,
                "total_calls": len(day_visits),
                "first_call": first_c,
                "last_call": last_c,
                "field_hours": hours,
                "status": "APPROVED",
            })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        total_calls = sum(int(i.get("total_calls", 0)) for i in items)
        total_docs = sum(int(i.get("doctor_calls", 0)) for i in items)
        total_chms = sum(int(i.get("chemist_calls", 0)) for i in items)
        avg_calls = round(total_calls / len(items), 1) if items else 0.0
        return {
            "total_records": len(items),
            "total_calls": total_calls,
            "total_doctor_calls": total_docs,
            "total_chemist_calls": total_chms,
            "avg_calls_per_day": avg_calls,
        }

ReportEngineRegistry.register(DailyCallReport)
''', encoding="utf-8")

# 2. mr_wise_visit_detail.py
(BASE_DIR / "mr_wise_visit_detail.py").write_text('''"""MR Wise Visit Detail / MR Wise Visits."""

from datetime import datetime, date
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn
from app.modules.dcr.models import DcrVisit
from app.modules.users.models import User
from app.modules.customers.models import Doctor, Chemist, Stockist, Hospital


class MrWiseVisitDetailReport(BaseReport):
    key = "mr_wise_visit_detail"
    title = "MR Wise Visit Detail / MR Wise Visits"
    group = "Field Activity"
    description = "Every visit with its details, grouped by employee and date."
    landscape = True
    allowed_roles = ["ADMIN", "MANAGER", "MR"]

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="date", label="Date", type="date", align="center"),
            ReportColumn(key="employee", label="Employee", type="string"),
            ReportColumn(key="time", label="Call Time", type="string", align="center"),
            ReportColumn(key="customer_name", label="Customer Name", type="string"),
            ReportColumn(key="customer_type", label="Type", type="string", align="center"),
            ReportColumn(key="speciality", label="Speciality / Details", type="string"),
            ReportColumn(key="verified", label="Geofence Verified", type="status", align="center"),
            ReportColumn(key="pob_amount", label="POB Amount (₹)", type="currency", align="right"),
            ReportColumn(key="remarks", label="Remarks", type="string"),
        ]

    def run_query(self, db: Session, filters: Any, user_ids: list[int] | None, start_utc: datetime | None, end_utc: datetime | None) -> list[dict[str, Any]]:
        q = select(DcrVisit)
        if user_ids:
            q = q.where(DcrVisit.user_id.in_(user_ids))
        if start_utc and end_utc:
            q = q.where(DcrVisit.call_time >= start_utc, DcrVisit.call_time <= end_utc)

        visits = db.execute(q).scalars().all()
        user_cache = {u.id: u for u in db.execute(select(User)).scalars().all()}
        doc_cache = {d.id: d for d in db.execute(select(Doctor)).scalars().all()}
        chm_cache = {c.id: c for c in db.execute(select(Chemist)).scalars().all()}
        stk_cache = {s.id: s for s in db.execute(select(Stockist)).scalars().all()}
        hosp_cache = {h.id: h for h in db.execute(select(Hospital)).scalars().all()}

        rows = []
        for v in visits:
            u = user_cache.get(v.user_id)
            c_name = "Unknown Customer"
            spec = "-"
            if v.customer_type == "DOCTOR" and v.doctor_id in doc_cache:
                doc = doc_cache[v.doctor_id]
                c_name = doc.full_name
                spec = f"{doc.specialization or ''} ({doc.category or 'A'})"
            elif v.customer_type == "CHEMIST" and v.chemist_id in chm_cache:
                c_name = chm_cache[v.chemist_id].shop_name
            elif v.customer_type == "STOCKIST" and v.stockist_id in stk_cache:
                c_name = stk_cache[v.stockist_id].agency_name
            elif v.customer_type == "HOSPITAL" and v.hospital_id in hosp_cache:
                c_name = hosp_cache[v.hospital_id].name

            rows.append({
                "date": v.dcr_date.isoformat(),
                "employee": u.full_name if u else f"User #{v.user_id}",
                "time": v.call_time.strftime("%H:%M") if v.call_time else "-",
                "customer_name": c_name,
                "customer_type": v.customer_type,
                "speciality": spec,
                "verified": "VERIFIED" if v.is_geofence_verified else "UNVERIFIED",
                "pob_amount": float(v.pob_amount or 0.0),
                "remarks": v.remarks or "-",
            })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        total_pob = sum(float(i.get("pob_amount", 0.0)) for i in items)
        verified_cnt = sum(1 for i in items if i.get("verified") == "VERIFIED")
        v_pct = round((verified_cnt / len(items)) * 100, 1) if items else 0.0
        return {
            "total_visits": len(items),
            "verified_percentage": f"{v_pct}%",
            "total_pob_amount": round(total_pob, 2),
        }

ReportEngineRegistry.register(MrWiseVisitDetailReport)
''', encoding="utf-8")

# 3. mr_daily_punching.py
(BASE_DIR / "mr_daily_punching.py").write_text('''"""MR_DailyPunching."""

from datetime import datetime, date
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn
from app.modules.attendance.models import Attendance
from app.modules.users.models import User


class MrDailyPunchingReport(BaseReport):
    key = "mr_daily_punching"
    title = "MR_DailyPunching"
    group = "Field Activity"
    description = "Punch in and punch out time and place per day."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER", "MR"]

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="date", label="Date", type="date", align="center"),
            ReportColumn(key="employee", label="Employee", type="string"),
            ReportColumn(key="punch_in", label="Punch-in Time & Place", type="string"),
            ReportColumn(key="punch_out", label="Punch-out Time & Place", type="string"),
            ReportColumn(key="hours", label="Hours", type="number", align="right"),
            ReportColumn(key="late", label="Late Status", type="status", align="center"),
            ReportColumn(key="work_type", label="Work Type", type="string", align="center"),
        ]

    def run_query(self, db: Session, filters: Any, user_ids: list[int] | None, start_utc: datetime | None, end_utc: datetime | None) -> list[dict[str, Any]]:
        q = select(Attendance)
        if user_ids:
            q = q.where(Attendance.user_id.in_(user_ids))
        if start_utc and end_utc:
            q = q.where(Attendance.check_in_time >= start_utc, Attendance.check_in_time <= end_utc)

        records = db.execute(q).scalars().all()
        user_cache = {u.id: u for u in db.execute(select(User)).scalars().all()}
        rows = []
        for r in records:
            u = user_cache.get(r.user_id)
            pin = f"{r.check_in_time.strftime('%H:%M')} ({r.check_in_address or 'Field'})" if r.check_in_time else "-"
            pout = f"{r.check_out_time.strftime('%H:%M')} ({r.check_out_address or 'Field'})" if r.check_out_time else "-"
            hrs = round(float(r.working_hours or 0.0), 1)
            rows.append({
                "date": r.attendance_date.isoformat(),
                "employee": u.full_name if u else f"User #{r.user_id}",
                "punch_in": pin,
                "punch_out": pout,
                "hours": hrs,
                "late": "LATE" if r.is_late else "ON_TIME",
                "work_type": r.work_type or "FIELD",
            })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        total_p = len(items)
        late_c = sum(1 for i in items if i.get("late") == "LATE")
        avg_h = round(sum(float(i.get("hours", 0)) for i in items) / total_p, 1) if total_p else 0.0
        return {
            "total_punch_ins": total_p,
            "late_count": late_c,
            "on_time_pct": f"{round(((total_p - late_c) / total_p) * 100, 1) if total_p else 100}%",
            "average_working_hours": avg_h,
        }

ReportEngineRegistry.register(MrDailyPunchingReport)
''', encoding="utf-8")

print("Created first 3 report definitions...")
