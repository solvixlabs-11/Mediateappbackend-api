"""Group D: Doctor analysis reports (Reports 13 to 17)."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.customers.models import Doctor
from app.modules.dcr.models import DcrVisit
from app.modules.reports.base import BaseReport, ReportRegistry
from app.modules.reports.schemas import ReportColumn, ReportFilterParams, ReportFilterSchema
from app.modules.territories.models import Territory, UserTerritoryAssignment
from app.modules.users.models import User


class MrDoctorWiseMonthlySummaryReport(BaseReport):
    """Report 13: MR Doctor Wise Monthly Summary (NOW).

    Columns: MR, Doctor, Category, Specialization, visit count per day/week,
    Month total, Last visit, Required frequency, Frequency met.
    """

    key = "mr_doctor_wise_monthly_summary"
    title = "MR Doctor Wise Monthly Summary"
    group = "Doctor Analysis"
    description = "Monthly doctor call frequency analysis, tracking required contact frequency vs actual visits achieved."
    landscape = True
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    report_number = 13
    status = "NOW"
    is_ready = True
    filter_schema = ReportFilterSchema(
        date_range=True,
        mr_picker=True,
        territory_picker=True,
        category_picker=True,
    )

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="mr_name", label="MR", type="string"),
            ReportColumn(key="doctor", label="Doctor", type="string"),
            ReportColumn(key="category", label="Cat", type="string", align="center"),
            ReportColumn(key="specialization", label="Specialization", type="string"),
            ReportColumn(key="month_total", label="Month Visits", type="number", align="right"),
            ReportColumn(key="last_visit", label="Last Visit", type="date", align="center"),
            ReportColumn(key="required_frequency", label="Req Freq", type="number", align="right"),
            ReportColumn(key="frequency_met", label="Frequency Met", type="status", align="center"),
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
            select(
                DcrVisit.user_id,
                DcrVisit.doctor_id,
                func.count(DcrVisit.id).label("visit_count"),
                func.max(DcrVisit.dcr_date).label("last_visit_date"),
            )
            .where(DcrVisit.doctor_id.isnot(None))
            .group_by(DcrVisit.user_id, DcrVisit.doctor_id)
        )

        if user_ids is not None:
            stmt = stmt.where(DcrVisit.user_id.in_(user_ids))

        if filters.territory_id:
            stmt = stmt.where(DcrVisit.doctor.has(Doctor.territory_id == filters.territory_id))

        if start_utc and end_utc:
            stmt = stmt.where(DcrVisit.dcr_date >= start_utc.date(), DcrVisit.dcr_date <= end_utc.date())

        rows = db.execute(stmt).all()
        if not rows:
            return []

        doc_ids = {r.doctor_id for r in rows if r.doctor_id}
        user_id_set = {r.user_id for r in rows}

        docs = {
            d.id: d
            for d in db.scalars(select(Doctor).where(Doctor.id.in_(doc_ids))).all()
        }
        users = {
            u.id: u.full_name
            for u in db.scalars(select(User).where(User.id.in_(user_id_set))).all()
        }

        results: list[dict[str, Any]] = []
        for uid, did, cnt, last_d in rows:
            doc = docs.get(did)
            if not doc:
                continue

            if filters.category and filters.category != "All" and doc.category != filters.category.upper():
                continue

            req_freq = 3 if doc.category == "A" else (2 if doc.category == "B" else 1)
            is_met = "Yes" if cnt >= req_freq else "No"

            results.append({
                "mr_name": users.get(uid, f"MR #{uid}"),
                "doctor": doc.full_name if doc.full_name.lower().startswith("dr") else f"Dr. {doc.full_name}",
                "category": doc.category or "A",
                "specialization": doc.specialization or "General",
                "month_total": cnt,
                "last_visit": last_d.strftime("%d-%b-%Y") if last_d else "-",
                "required_frequency": req_freq,
                "frequency_met": is_met,
            })

        return results

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        tot = len(items)
        met = sum(1 for it in items if it.get("frequency_met") == "Yes")
        rate = round(met / tot, 3) if tot else 0.0
        return {
            "total_doctors_called": tot,
            "frequency_met_count": met,
            "frequency_adherence_rate": rate,
        }


class MrWiseNotSeenDoctorReport(BaseReport):
    """Report 14: MR Wise Not Seen Doctor (NOW).

    Columns: MR, Doctor, Category, Specialization, Territory, Last visit date,
    Days since last visit, Required frequency.
    """

    key = "mr_wise_not_seen_doctor"
    title = "MR Wise Not Seen Doctor"
    group = "Doctor Analysis"
    description = "Defaulter and unvisited doctor list highlighting accounts exceeding contact periodicity thresholds."
    landscape = True
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    report_number = 14
    status = "NOW"
    is_ready = True
    filter_schema = ReportFilterSchema(
        date_range=False,
        mr_picker=True,
        territory_picker=True,
        category_picker=True,
        days_not_seen_picker=True,
    )

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="mr_name", label="MR", type="string"),
            ReportColumn(key="doctor", label="Doctor", type="string"),
            ReportColumn(key="category", label="Cat", type="string", align="center"),
            ReportColumn(key="specialization", label="Specialization", type="string"),
            ReportColumn(key="territory", label="Territory", type="string"),
            ReportColumn(key="last_visit", label="Last Visit Date", type="date", align="center"),
            ReportColumn(key="days_since_last_visit", label="Days Not Seen", type="number", align="right"),
            ReportColumn(key="required_frequency", label="Req Freq", type="number", align="right"),
        ]

    def run_query(
        self,
        db: Session,
        filters: ReportFilterParams,
        user_ids: list[int] | None,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> list[dict[str, Any]]:
        # Map user territory assignments
        a_stmt = select(UserTerritoryAssignment).options(
            selectinload(UserTerritoryAssignment.user),
            selectinload(UserTerritoryAssignment.territory),
        )
        if user_ids is not None:
            a_stmt = a_stmt.where(UserTerritoryAssignment.user_id.in_(user_ids))
        if filters.territory_id:
            a_stmt = a_stmt.where(UserTerritoryAssignment.territory_id == filters.territory_id)

        assignments = list(db.scalars(a_stmt).all())
        if not assignments:
            return []

        terr_ids = [a.territory_id for a in assignments]
        terr_mr_map = {a.territory_id: a.user.full_name for a in assignments if a.user}

        # Query all doctors in territories
        d_stmt = select(Doctor).options(selectinload(Doctor.territory)).where(Doctor.territory_id.in_(terr_ids))
        if filters.category and filters.category != "All":
            d_stmt = d_stmt.where(Doctor.category == filters.category.upper())

        doctors = list(db.scalars(d_stmt).all())

        # Query last visit date per doctor
        v_stmt = select(DcrVisit.doctor_id, func.max(DcrVisit.dcr_date)).where(
            DcrVisit.doctor_id.in_([d.id for d in doctors])
        ).group_by(DcrVisit.doctor_id)
        last_visit_map = dict(db.execute(v_stmt).all())

        today_d = date.today()
        threshold_days = filters.days_not_seen or 20

        results: list[dict[str, Any]] = []
        for doc in doctors:
            last_d = last_visit_map.get(doc.id)
            days_unseen = (today_d - last_d).days if last_d else 999

            if days_unseen >= threshold_days:
                mr_name = terr_mr_map.get(doc.territory_id, "Unassigned")
                req_freq = 3 if doc.category == "A" else (2 if doc.category == "B" else 1)
                results.append({
                    "mr_name": mr_name,
                    "doctor": doc.full_name if doc.full_name.lower().startswith("dr") else f"Dr. {doc.full_name}",
                    "category": doc.category or "A",
                    "specialization": doc.specialization or "General",
                    "territory": doc.territory.name if doc.territory else "-",
                    "last_visit": last_d.strftime("%d-%b-%Y") if last_d else "Never Visited",
                    "days_since_last_visit": days_unseen if last_d else "> 90",
                    "required_frequency": req_freq,
                })

        results.sort(key=lambda r: int(r["days_since_last_visit"]) if isinstance(r["days_since_last_visit"], int) else 999, reverse=True)
        return results

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "total_unvisited_doctors": len(items),
            "category_a_unvisited": sum(1 for it in items if it.get("category") == "A"),
            "category_b_unvisited": sum(1 for it in items if it.get("category") == "B"),
        }


class MrWiseDocSpWiseStatsReport(BaseReport):
    """Report 15: MR Wise Doctor Specialization Wise Stats (NOW).

    Columns: MR, Specialization, Doctors assigned, Doctors visited, Total visits, Coverage %, Average visits per doctor.
    """

    key = "mr_wise_doc_sp_wise_stats"
    title = "MR Wise DocSp Wise Stats"
    group = "Doctor Analysis"
    description = "Medical specialty breakdown measuring representative coverage and visit intensity across therapeutic areas."
    landscape = True
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    report_number = 15
    status = "NOW"
    is_ready = True
    filter_schema = ReportFilterSchema(
        date_range=True,
        mr_picker=True,
        territory_picker=True,
        specialization_picker=True,
    )

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="mr_name", label="MR", type="string"),
            ReportColumn(key="specialization", label="Specialization", type="string"),
            ReportColumn(key="doctors_assigned", label="Assigned", type="number", align="right"),
            ReportColumn(key="doctors_visited", label="Visited", type="number", align="right"),
            ReportColumn(key="total_visits", label="Total Calls", type="number", align="right"),
            ReportColumn(key="coverage_pct", label="Coverage %", type="percent", align="right"),
            ReportColumn(key="avg_visits_per_doc", label="Avg Calls / Doctor", type="number", align="right"),
        ]

    def run_query(
        self,
        db: Session,
        filters: ReportFilterParams,
        user_ids: list[int] | None,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> list[dict[str, Any]]:
        # Fetch user territory assignments
        a_stmt = select(UserTerritoryAssignment).options(selectinload(UserTerritoryAssignment.user))
        if user_ids is not None:
            a_stmt = a_stmt.where(UserTerritoryAssignment.user_id.in_(user_ids))
        if filters.territory_id:
            a_stmt = a_stmt.where(UserTerritoryAssignment.territory_id == filters.territory_id)

        assigns = list(db.scalars(a_stmt).all())
        results: list[dict[str, Any]] = []

        for a in assigns:
            u = a.user
            if not u:
                continue

            # Doctors assigned in territory grouped by specialization
            d_stmt = select(Doctor).where(Doctor.territory_id == a.territory_id)
            if filters.specialization and filters.specialization != "All":
                d_stmt = d_stmt.where(Doctor.specialization.ilike(f"%{filters.specialization}%"))

            doctors = list(db.scalars(d_stmt).all())
            spec_docs: dict[str, list[Doctor]] = {}
            for d in doctors:
                spec = d.specialization or "General Physician"
                spec_docs.setdefault(spec, []).append(d)

            # Visits in date range for this MR
            v_stmt = select(DcrVisit.doctor_id, func.count(DcrVisit.id)).where(DcrVisit.user_id == u.id)
            if start_utc and end_utc:
                v_stmt = v_stmt.where(DcrVisit.dcr_date >= start_utc.date(), DcrVisit.dcr_date <= end_utc.date())
            visited_counts = dict(db.execute(v_stmt.group_by(DcrVisit.doctor_id)).all())

            for spec, doc_list in spec_docs.items():
                assigned_cnt = len(doc_list)
                visited_cnt = sum(1 for d in doc_list if d.id in visited_counts)
                tot_calls = sum(visited_counts.get(d.id, 0) for d in doc_list)
                cov_pct = round(visited_cnt / assigned_cnt, 3) if assigned_cnt else 0.0
                avg_calls = round(tot_calls / visited_cnt, 1) if visited_cnt else 0.0

                results.append({
                    "mr_name": u.full_name,
                    "specialization": spec,
                    "doctors_assigned": assigned_cnt,
                    "doctors_visited": visited_cnt,
                    "total_visits": tot_calls,
                    "coverage_pct": cov_pct,
                    "avg_visits_per_doc": avg_calls,
                })

        return results

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        tot_assigned = sum(it.get("doctors_assigned", 0) for it in items)
        tot_visited = sum(it.get("doctors_visited", 0) for it in items)
        overall_cov = round(tot_visited / tot_assigned, 3) if tot_assigned else 0.0
        return {
            "total_specialty_categories": len(items),
            "total_doctors_assigned": tot_assigned,
            "total_doctors_visited": tot_visited,
            "overall_specialty_coverage": overall_cov,
        }


class MrWiseDoctorCategoryWiseReport(BaseReport):
    """Report 16: MR Wise Doctor Category Wise Report (NOW).

    Columns: MR, Category (A, B, C), Assigned, Visited, Total visits, Coverage %, Frequency met %.
    """

    key = "mr_wise_doctor_category_wise_report"
    title = "MR Wise Doctor Category Wise Report"
    group = "Doctor Analysis"
    description = "Doctor tier (Class A/B/C) coverage compliance and visit frequency attainment per MR."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    report_number = 16
    status = "NOW"
    is_ready = True
    filter_schema = ReportFilterSchema(
        date_range=True,
        mr_picker=True,
        territory_picker=True,
        category_picker=True,
    )

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="mr_name", label="MR", type="string"),
            ReportColumn(key="category", label="Tier Category", type="string", align="center"),
            ReportColumn(key="assigned", label="Assigned", type="number", align="right"),
            ReportColumn(key="visited", label="Visited", type="number", align="right"),
            ReportColumn(key="total_visits", label="Total Calls", type="number", align="right"),
            ReportColumn(key="coverage_pct", label="Coverage %", type="percent", align="right"),
            ReportColumn(key="frequency_met_pct", label="Freq Met %", type="percent", align="right"),
        ]

    def run_query(
        self,
        db: Session,
        filters: ReportFilterParams,
        user_ids: list[int] | None,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> list[dict[str, Any]]:
        a_stmt = select(UserTerritoryAssignment).options(selectinload(UserTerritoryAssignment.user))
        if user_ids is not None:
            a_stmt = a_stmt.where(UserTerritoryAssignment.user_id.in_(user_ids))
        if filters.territory_id:
            a_stmt = a_stmt.where(UserTerritoryAssignment.territory_id == filters.territory_id)

        assigns = list(db.scalars(a_stmt).all())
        results: list[dict[str, Any]] = []

        categories = ["A", "B", "C"]
        if filters.category and filters.category != "All":
            categories = [filters.category.upper()]

        for a in assigns:
            u = a.user
            if not u:
                continue

            # Doctors assigned in territory
            docs = list(db.scalars(select(Doctor).where(Doctor.territory_id == a.territory_id)).all())

            # DCR visits in date range for this MR
            v_stmt = select(DcrVisit.doctor_id, func.count(DcrVisit.id)).where(DcrVisit.user_id == u.id)
            if start_utc and end_utc:
                v_stmt = v_stmt.where(DcrVisit.dcr_date >= start_utc.date(), DcrVisit.dcr_date <= end_utc.date())
            visited_counts = dict(db.execute(v_stmt.group_by(DcrVisit.doctor_id)).all())

            for cat in categories:
                cat_docs = [d for d in docs if (d.category or "A") == cat]
                assigned_cnt = len(cat_docs)
                visited_cnt = sum(1 for d in cat_docs if d.id in visited_counts)
                tot_calls = sum(visited_counts.get(d.id, 0) for d in cat_docs)

                req_f = 3 if cat == "A" else (2 if cat == "B" else 1)
                freq_met_cnt = sum(1 for d in cat_docs if visited_counts.get(d.id, 0) >= req_f)

                cov_pct = round(visited_cnt / assigned_cnt, 3) if assigned_cnt else 0.0
                freq_pct = round(freq_met_cnt / assigned_cnt, 3) if assigned_cnt else 0.0

                results.append({
                    "mr_name": u.full_name,
                    "category": f"Category {cat}",
                    "assigned": assigned_cnt,
                    "visited": visited_cnt,
                    "total_visits": tot_calls,
                    "coverage_pct": cov_pct,
                    "frequency_met_pct": freq_pct,
                })

        return results

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        tot_ass = sum(it.get("assigned", 0) for it in items)
        tot_vis = sum(it.get("visited", 0) for it in items)
        overall_cov = round(tot_vis / tot_ass, 3) if tot_ass else 0.0
        return {
            "total_assigned": tot_ass,
            "total_visited": tot_vis,
            "overall_category_coverage": overall_cov,
        }


class MrWiseDoctorTypeWiseReport(BaseReport):
    """Report 17: MR Wise Doctor Type Wise Report (NOW).

    Columns: Same as report 16 but grouped by doctor type.
    """

    key = "mr_wise_doctor_type_wise_report"
    title = "MR Wise Doctor Type Wise Report"
    group = "Doctor Analysis"
    description = "Doctor type classification (Consultant, Specialist, Physician, Surgeon) coverage and visit statistics."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    report_number = 17
    status = "NOW"
    is_ready = True
    filter_schema = ReportFilterSchema(
        date_range=True,
        mr_picker=True,
        territory_picker=True,
    )

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="mr_name", label="MR", type="string"),
            ReportColumn(key="doctor_type", label="Doctor Type", type="string"),
            ReportColumn(key="assigned", label="Assigned", type="number", align="right"),
            ReportColumn(key="visited", label="Visited", type="number", align="right"),
            ReportColumn(key="total_visits", label="Total Calls", type="number", align="right"),
            ReportColumn(key="coverage_pct", label="Coverage %", type="percent", align="right"),
            ReportColumn(key="frequency_met_pct", label="Freq Met %", type="percent", align="right"),
        ]

    def run_query(
        self,
        db: Session,
        filters: ReportFilterParams,
        user_ids: list[int] | None,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> list[dict[str, Any]]:
        a_stmt = select(UserTerritoryAssignment).options(selectinload(UserTerritoryAssignment.user))
        if user_ids is not None:
            a_stmt = a_stmt.where(UserTerritoryAssignment.user_id.in_(user_ids))
        if filters.territory_id:
            a_stmt = a_stmt.where(UserTerritoryAssignment.territory_id == filters.territory_id)

        assigns = list(db.scalars(a_stmt).all())
        results: list[dict[str, Any]] = []

        for a in assigns:
            u = a.user
            if not u:
                continue

            docs = list(db.scalars(select(Doctor).where(Doctor.territory_id == a.territory_id)).all())
            type_docs: dict[str, list[Doctor]] = {}
            for d in docs:
                dtype = d.qualification or d.specialization or "Consultant"
                type_docs.setdefault(dtype, []).append(d)

            v_stmt = select(DcrVisit.doctor_id, func.count(DcrVisit.id)).where(DcrVisit.user_id == u.id)
            if start_utc and end_utc:
                v_stmt = v_stmt.where(DcrVisit.dcr_date >= start_utc.date(), DcrVisit.dcr_date <= end_utc.date())
            visited_counts = dict(db.execute(v_stmt.group_by(DcrVisit.doctor_id)).all())

            for dtype, dlist in type_docs.items():
                assigned_cnt = len(dlist)
                visited_cnt = sum(1 for d in dlist if d.id in visited_counts)
                tot_calls = sum(visited_counts.get(d.id, 0) for d in dlist)
                freq_met_cnt = sum(1 for d in dlist if visited_counts.get(d.id, 0) >= 2)

                cov_pct = round(visited_cnt / assigned_cnt, 3) if assigned_cnt else 0.0
                freq_pct = round(freq_met_cnt / assigned_cnt, 3) if assigned_cnt else 0.0

                results.append({
                    "mr_name": u.full_name,
                    "doctor_type": dtype,
                    "assigned": assigned_cnt,
                    "visited": visited_cnt,
                    "total_visits": tot_calls,
                    "coverage_pct": cov_pct,
                    "frequency_met_pct": freq_pct,
                })

        return results

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        tot_ass = sum(it.get("assigned", 0) for it in items)
        tot_vis = sum(it.get("visited", 0) for it in items)
        overall_cov = round(tot_vis / tot_ass, 3) if tot_ass else 0.0
        return {
            "total_assigned": tot_ass,
            "total_visited": tot_vis,
            "overall_type_coverage": overall_cov,
        }


ReportRegistry.register(MrDoctorWiseMonthlySummaryReport)
ReportRegistry.register(MrWiseNotSeenDoctorReport)
ReportRegistry.register(MrWiseDocSpWiseStatsReport)
ReportRegistry.register(MrWiseDoctorCategoryWiseReport)
ReportRegistry.register(MrWiseDoctorTypeWiseReport)
