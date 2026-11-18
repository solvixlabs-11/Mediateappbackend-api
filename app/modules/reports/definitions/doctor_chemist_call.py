"""MR_Wise_Doctor_Chemist_Call."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.dcr.models import DcrVisit
from app.modules.reports.base import BaseReport
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.schemas import ReportColumn
from app.modules.users.models import User


class MrWiseDoctorChemistCallReport(BaseReport):
    key = "doctor_chemist_call"
    title = "MR_Wise_Doctor_Chemist_Call"
    group = "Field Activity"
    description = "Doctor, chemist and stockist calls per employee."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER", "MR"]

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="employee", label="Employee", type="string"),
            ReportColumn(key="emp_code", label="Emp Code", type="string", align="center"),
            ReportColumn(key="doctor_calls", label="Doctor Calls", type="number", align="right"),
            ReportColumn(key="chemist_calls", label="Chemist Calls", type="number", align="right"),
            ReportColumn(key="stockist_calls", label="Stockist Calls", type="number", align="right"),
            ReportColumn(key="total_calls", label="Total Calls", type="number", align="right"),
            ReportColumn(key="ratio", label="Dr : Chm Ratio", type="string", align="center"),
        ]

    def run_query(self, db: Session, filters: Any, user_ids: list[int] | None, start_utc: datetime | None, end_utc: datetime | None) -> list[dict[str, Any]]:
        users_q = select(User).where(User.is_active == True)
        if user_ids:
            users_q = users_q.where(User.id.in_(user_ids))
        users = db.execute(users_q).scalars().all()

        rows = []
        for u in users:
            vq = select(DcrVisit).where(DcrVisit.user_id == u.id)
            if start_utc and end_utc:
                vq = vq.where(DcrVisit.call_time >= start_utc, DcrVisit.call_time <= end_utc)
            visits = db.execute(vq).scalars().all()
            d_c = sum(1 for v in visits if v.customer_type == "DOCTOR")
            c_c = sum(1 for v in visits if v.customer_type == "CHEMIST")
            s_c = sum(1 for v in visits if v.customer_type in ("STOCKIST", "HOSPITAL"))
            tot = len(visits)
            ratio = f"{round(d_c / c_c, 1)} : 1" if c_c else f"{d_c} : 0"

            rows.append({
                "employee": u.full_name,
                "emp_code": u.employee_code,
                "doctor_calls": d_c,
                "chemist_calls": c_c,
                "stockist_calls": s_c,
                "total_calls": tot,
                "ratio": ratio,
            })
        return rows

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "total_employees": len(items),
            "total_doctor_calls": sum(int(i.get("doctor_calls", 0)) for i in items),
            "total_chemist_calls": sum(int(i.get("chemist_calls", 0)) for i in items),
            "total_calls": sum(int(i.get("total_calls", 0)) for i in items),
        }

ReportEngineRegistry.register(MrWiseDoctorChemistCallReport)
