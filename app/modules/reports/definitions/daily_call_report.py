"""Daily Call Report (MR Wise Call Summary) / Daily Work Report."""

import calendar
from datetime import date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.dcr.models import DcrVisit
from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn
from app.modules.users.models import User


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
