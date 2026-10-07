"""Group C: Visits reports (Reports 7 to 12)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.attendance.models import Attendance
from app.modules.customers.models import Chemist, Doctor, Hospital, Stockist
from app.modules.dcr.models import DcrVisit, PlannedVisit
from app.modules.reports.base import BaseReport, ReportRegistry
from app.modules.reports.schemas import ReportColumn, ReportFilterParams, ReportFilterSchema
from app.modules.reports.utils import utc_to_ist_date, utc_to_ist_time
from app.modules.territories.models import UserTerritoryAssignment
from app.modules.users.models import Role, User


class MrWiseVisitsReport(BaseReport):
    """Report 7: MR Wise Visits (NOW).

    Columns: Grouped by MR then date: Time, Visit type, Customer, Specialization or type,
    Category, Verified, Distance, Outcome, Remarks, Next visit.
    PDF grouped date wise with day subtotals.
    """

    key = "mr_wise_visits"
    title = "MR Wise Visits"
    group = "Visits"
    description = "Detailed log of every customer visit with geolocation compliance, call outcomes, and next appointment dates."
    landscape = True
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    report_number = 7
    status = "NOW"
    is_ready = True
    filter_schema = ReportFilterSchema(
        date_range=True,
        mr_picker=True,
        territory_picker=True,
        customer_type_picker=True,
        status_picker=True,
        status_options=["All", "Verified", "Not Verified"],
    )

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="date", label="Date", type="date", align="center"),
            ReportColumn(key="time", label="Time", type="string", align="center"),
            ReportColumn(key="mr_name", label="MR", type="string"),
            ReportColumn(key="visit_type", label="Visit Type", type="string"),
            ReportColumn(key="customer_name", label="Customer", type="string"),
            ReportColumn(key="customer_type", label="Type", type="string"),
            ReportColumn(key="specialization", label="Specialization", type="string"),
            ReportColumn(key="category", label="Cat", type="string", align="center"),
            ReportColumn(key="verified", label="Verified", type="status", align="center"),
            ReportColumn(key="distance", label="Dist (m)", type="number", align="right"),
            ReportColumn(key="outcome", label="Outcome", type="string"),
            ReportColumn(key="remarks", label="Remarks", type="string"),
            ReportColumn(key="next_visit", label="Next Visit", type="date", align="center"),
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
            select(DcrVisit)
            .options(
                selectinload(DcrVisit.user),
                selectinload(DcrVisit.doctor).selectinload(Doctor.territory),
                selectinload(DcrVisit.chemist).selectinload(Chemist.territory),
                selectinload(DcrVisit.hospital).selectinload(Hospital.territory),
                selectinload(DcrVisit.stockist).selectinload(Stockist.territory),
                selectinload(DcrVisit.post_call_analysis),
            )
            .order_by(DcrVisit.dcr_date.desc(), DcrVisit.call_time.desc())
        )

        if user_ids is not None:
            stmt = stmt.where(DcrVisit.user_id.in_(user_ids))

        if start_utc and end_utc:
            s_d = utc_to_ist_date(start_utc)
            e_d = utc_to_ist_date(end_utc)
            stmt = stmt.where(
                ((DcrVisit.dcr_date >= s_d) & (DcrVisit.dcr_date <= e_d))
                | ((DcrVisit.call_time >= start_utc) & (DcrVisit.call_time <= end_utc))
            )

        if filters.territory_id:
            t_id = filters.territory_id
            stmt = stmt.where(
                (DcrVisit.doctor.has(Doctor.territory_id == t_id))
                | (DcrVisit.chemist.has(Chemist.territory_id == t_id))
                | (DcrVisit.hospital.has(Hospital.territory_id == t_id))
                | (DcrVisit.stockist.has(Stockist.territory_id == t_id))
            )

        if filters.customer_type and filters.customer_type != "All":
            stmt = stmt.where(DcrVisit.customer_type == filters.customer_type.upper())

        if filters.visit_type and filters.visit_type != "All":
            stmt = stmt.where(func.lower(DcrVisit.visit_type) == filters.visit_type.lower())

        if filters.verified is not None:
            stmt = stmt.where(DcrVisit.is_geofence_verified.is_(filters.verified))
        elif filters.status:
            if filters.status.lower() == "verified":
                stmt = stmt.where(DcrVisit.is_geofence_verified.is_(True))
            elif filters.status.lower() in ["not verified", "not_verified"]:
                stmt = stmt.where(DcrVisit.is_geofence_verified.is_(False))

        records = list(db.scalars(stmt).all())
        results: list[dict[str, Any]] = []

        for v in records:
            cust_name = "-"
            spec = "-"
            cat = "-"
            if v.doctor:
                cust_name = v.doctor.full_name if v.doctor.full_name.lower().startswith("dr") else f"Dr. {v.doctor.full_name}"
                spec = v.doctor.specialization or v.doctor.qualification or "-"
                cat = v.doctor.category or "A"
            elif v.chemist:
                cust_name = v.chemist.shop_name
                spec = "Retail Chemist"
                cat = "B"
            elif v.hospital:
                cust_name = v.hospital.name
                spec = v.hospital.type or "Hospital"
                cat = "A"
            elif v.stockist:
                cust_name = v.stockist.agency_name
                spec = "Wholesale Stockist"
                cat = "A"

            outcome = v.post_call_analysis.call_outcome if v.post_call_analysis else "-"
            next_v = (
                v.post_call_analysis.next_visit_date.strftime("%d-%b-%Y")
                if v.post_call_analysis and v.post_call_analysis.next_visit_date
                else "-"
            )

            dist_val = round(v.distance_to_customer_meters, 1) if v.distance_to_customer_meters is not None else 0.0

            results.append({
                "date": v.dcr_date.strftime("%d-%b-%Y"),
                "time": utc_to_ist_time(v.call_time),
                "mr_name": v.user.full_name if v.user else f"MR #{v.user_id}",
                "visit_type": v.visit_type.replace("_", " ").title(),
                "customer_name": cust_name,
                "customer_type": v.customer_type.title(),
                "specialization": spec,
                "category": cat,
                "verified": "Verified" if v.is_geofence_verified else "Not Verified",
                "distance": dist_val,
                "outcome": outcome,
                "remarks": v.remarks or "-",
                "next_visit": next_v,
            })

        return results

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        total = len(items)
        ver_cnt = sum(1 for it in items if it.get("verified") == "Verified")
        ver_pct = round(ver_cnt / total, 3) if total else 0.0
        return {
            "total_visits": total,
            "verified_visits": ver_cnt,
            "verification_rate": ver_pct,
        }


class MrWiseVisitsAnalysisReport(BaseReport):
    """Report 8: MR Wise Visits Analysis (NOW).

    Columns: MR, Total visits, Doctor, Hospital, Chemist, Stockist split,
    Unique customers, Days worked, Average per day, Verified %, Planned vs actual %.
    """

    key = "mr_wise_visits_analysis"
    title = "MR Wise Visits Analysis"
    group = "Visits"
    description = "Field force productivity overview showing call volume by customer type, unique coverage, and call average."
    landscape = True
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    report_number = 8
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
            ReportColumn(key="total_visits", label="Total Visits", type="number", align="right"),
            ReportColumn(key="doctor_calls", label="Doctor", type="number", align="right"),
            ReportColumn(key="hospital_calls", label="Hospital", type="number", align="right"),
            ReportColumn(key="chemist_calls", label="Chemist", type="number", align="right"),
            ReportColumn(key="stockist_calls", label="Stockist", type="number", align="right"),
            ReportColumn(key="unique_customers", label="Unique Cust", type="number", align="right"),
            ReportColumn(key="days_worked", label="Days Worked", type="number", align="right"),
            ReportColumn(key="avg_per_day", label="Avg / Day", type="number", align="right"),
            ReportColumn(key="verified_pct", label="Verified %", type="percent", align="right"),
            ReportColumn(key="planned_vs_actual_pct", label="Plan Adherence %", type="percent", align="right"),
        ]

    def run_query(
        self,
        db: Session,
        filters: ReportFilterParams,
        user_ids: list[int] | None,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> list[dict[str, Any]]:
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

        results: list[dict[str, Any]] = []

        for u in users:
            # DCR visits for user
            v_stmt = select(DcrVisit).where(DcrVisit.user_id == u.id)
            if start_utc and end_utc:
                v_stmt = v_stmt.where(DcrVisit.call_time >= start_utc, DcrVisit.call_time <= end_utc)
            if filters.territory_id:
                t_id = filters.territory_id
                v_stmt = v_stmt.where(
                    (DcrVisit.doctor.has(Doctor.territory_id == t_id))
                    | (DcrVisit.chemist.has(Chemist.territory_id == t_id))
                    | (DcrVisit.hospital.has(Hospital.territory_id == t_id))
                    | (DcrVisit.stockist.has(Stockist.territory_id == t_id))
                )
            visits = list(db.scalars(v_stmt).all())

            tot = len(visits)
            doc = sum(1 for v in visits if v.customer_type == "DOCTOR")
            hosp = sum(1 for v in visits if v.customer_type == "HOSPITAL")
            chem = sum(1 for v in visits if v.customer_type == "CHEMIST")
            stock = sum(1 for v in visits if v.customer_type == "STOCKIST")

            # Unique customers
            unique_custs: set[tuple[str, int]] = set()
            for v in visits:
                cid = v.doctor_id or v.chemist_id or v.hospital_id or v.stockist_id or 0
                unique_custs.add((v.customer_type, cid))

            # Days worked from attendance
            a_stmt = select(func.count(Attendance.id)).where(
                Attendance.user_id == u.id,
                Attendance.status.in_(["PRESENT", "HALF_DAY"]),
            )
            if start_utc and end_utc:
                a_stmt = a_stmt.where(Attendance.date >= start_utc.date(), Attendance.date <= end_utc.date())
            days_worked = db.scalar(a_stmt) or 0

            avg_per_day = round(tot / days_worked, 1) if days_worked > 0 else (tot if tot > 0 else 0.0)

            ver_cnt = sum(1 for v in visits if v.is_geofence_verified)
            ver_pct = round(ver_cnt / tot, 3) if tot > 0 else 0.0

            # Planned visits
            p_stmt = select(func.count(PlannedVisit.id)).where(PlannedVisit.user_id == u.id)
            if start_utc and end_utc:
                p_stmt = p_stmt.where(PlannedVisit.plan_date >= start_utc.date(), PlannedVisit.plan_date <= end_utc.date())
            planned_cnt = db.scalar(p_stmt) or 0
            plan_pct = round(tot / planned_cnt, 3) if planned_cnt > 0 else 1.0

            results.append({
                "mr_name": u.full_name,
                "total_visits": tot,
                "doctor_calls": doc,
                "hospital_calls": hosp,
                "chemist_calls": chem,
                "stockist_calls": stock,
                "unique_customers": len(unique_custs),
                "days_worked": days_worked,
                "avg_per_day": avg_per_day,
                "verified_pct": ver_pct,
                "planned_vs_actual_pct": plan_pct,
            })

        return results

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        tot_v = sum(it.get("total_visits", 0) for it in items)
        tot_mrs = len(items)
        avg = round(tot_v / tot_mrs, 1) if tot_mrs else 0.0
        return {
            "total_representatives": tot_mrs,
            "total_visits": tot_v,
            "average_visits_per_mr": avg,
        }


class MrDesignationWiseVisitsAnalysisReport(BaseReport):
    """Report 9: MR Designation Wise Visits Analysis (NOW).

    Columns: Designation, MR count, Total visits, Average visits per MR, Average per day, Verified %.
    Manager and Admin only.
    """

    key = "mr_designation_wise_visits_analysis"
    title = "MR Designation Wise Visits Analysis"
    group = "Visits"
    description = "Hierarchical visit productivity comparison across field force designation levels."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER"]
    report_number = 9
    status = "NOW"
    is_ready = True
    filter_schema = ReportFilterSchema(
        date_range=True,
    )

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="designation", label="Designation", type="string"),
            ReportColumn(key="mr_count", label="Staff Count", type="number", align="right"),
            ReportColumn(key="total_visits", label="Total Visits", type="number", align="right"),
            ReportColumn(key="avg_visits_per_mr", label="Avg Visits / Person", type="number", align="right"),
            ReportColumn(key="avg_per_day", label="Avg Visits / Day", type="number", align="right"),
            ReportColumn(key="verified_pct", label="Verified %", type="percent", align="right"),
        ]

    def run_query(
        self,
        db: Session,
        filters: ReportFilterParams,
        user_ids: list[int] | None,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> list[dict[str, Any]]:
        # Query users joined with role
        u_stmt = select(User).options(selectinload(User.role))
        if user_ids is not None:
            u_stmt = u_stmt.where(User.id.in_(user_ids))
        users = list(db.scalars(u_stmt).all())

        # Group users by role name / designation
        desig_users: dict[str, list[User]] = {}
        for u in users:
            desig = u.role.name if u.role else "Field Representative"
            desig_users.setdefault(desig, []).append(u)

        results: list[dict[str, Any]] = []
        for desig, u_list in desig_users.items():
            uids = [u.id for u in u_list]
            v_stmt = select(DcrVisit).where(DcrVisit.user_id.in_(uids))
            if start_utc and end_utc:
                v_stmt = v_stmt.where(DcrVisit.call_time >= start_utc, DcrVisit.call_time <= end_utc)
            visits = list(db.scalars(v_stmt).all())

            tot_v = len(visits)
            staff_cnt = len(u_list)
            avg_per_person = round(tot_v / staff_cnt, 1) if staff_cnt else 0.0

            # Days worked across staff
            a_stmt = select(func.count(Attendance.id)).where(
                Attendance.user_id.in_(uids),
                Attendance.status.in_(["PRESENT", "HALF_DAY"]),
            )
            if start_utc and end_utc:
                a_stmt = a_stmt.where(Attendance.date >= start_utc.date(), Attendance.date <= end_utc.date())
            days_worked = db.scalar(a_stmt) or 0
            avg_per_day = round(tot_v / days_worked, 1) if days_worked > 0 else (tot_v if tot_v > 0 else 0.0)

            ver_cnt = sum(1 for v in visits if v.is_geofence_verified)
            ver_pct = round(ver_cnt / tot_v, 3) if tot_v > 0 else 0.0

            results.append({
                "designation": desig,
                "mr_count": staff_cnt,
                "total_visits": tot_v,
                "avg_visits_per_mr": avg_per_person,
                "avg_per_day": avg_per_day,
                "verified_pct": ver_pct,
            })

        return results

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "total_designations": len(items),
            "total_field_force": sum(it.get("mr_count", 0) for it in items),
            "total_visits": sum(it.get("total_visits", 0) for it in items),
        }


class MrWiseDoctorChemistCallReport(BaseReport):
    """Report 10: MR Wise Doctor Chemist Call (NOW).

    Columns: MR, Doctor calls, Chemist calls, Stockist calls, Doctor to chemist ratio.
    """

    key = "mr_wise_doctor_chemist_call"
    title = "MR Wise Doctor Chemist Call"
    group = "Visits"
    description = "Doctor vs Chemist call distribution and conversion ratio per representative."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    report_number = 10
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
            ReportColumn(key="doctor_calls", label="Doctor Calls", type="number", align="right"),
            ReportColumn(key="chemist_calls", label="Chemist Calls", type="number", align="right"),
            ReportColumn(key="stockist_calls", label="Stockist Calls", type="number", align="right"),
            ReportColumn(key="doc_to_chemist_ratio", label="Doc : Chemist Ratio", type="string", align="center"),
        ]

    def run_query(
        self,
        db: Session,
        filters: ReportFilterParams,
        user_ids: list[int] | None,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> list[dict[str, Any]]:
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

        results: list[dict[str, Any]] = []
        for u in users:
            v_stmt = select(DcrVisit.customer_type, func.count(DcrVisit.id)).where(DcrVisit.user_id == u.id)
            if start_utc and end_utc:
                v_stmt = v_stmt.where(DcrVisit.call_time >= start_utc, DcrVisit.call_time <= end_utc)
            if filters.territory_id:
                t_id = filters.territory_id
                v_stmt = v_stmt.where(
                    (DcrVisit.doctor.has(Doctor.territory_id == t_id))
                    | (DcrVisit.chemist.has(Chemist.territory_id == t_id))
                    | (DcrVisit.hospital.has(Hospital.territory_id == t_id))
                    | (DcrVisit.stockist.has(Stockist.territory_id == t_id))
                )
            counts = dict(db.execute(v_stmt.group_by(DcrVisit.customer_type)).all())

            doc = counts.get("DOCTOR", 0)
            chem = counts.get("CHEMIST", 0)
            stock = counts.get("STOCKIST", 0)

            ratio_str = f"{round(doc / chem, 2)} : 1" if chem > 0 else f"{doc} : 0"

            results.append({
                "mr_name": u.full_name,
                "doctor_calls": doc,
                "chemist_calls": chem,
                "stockist_calls": stock,
                "doc_to_chemist_ratio": ratio_str,
            })

        return results

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        tot_doc = sum(it.get("doctor_calls", 0) for it in items)
        tot_chem = sum(it.get("chemist_calls", 0) for it in items)
        tot_stock = sum(it.get("stockist_calls", 0) for it in items)
        overall_ratio = f"{round(tot_doc / tot_chem, 2)} : 1" if tot_chem > 0 else "N/A"
        return {
            "total_doctor_calls": tot_doc,
            "total_chemist_calls": tot_chem,
            "total_stockist_calls": tot_stock,
            "overall_ratio": overall_ratio,
        }


class MrWisePromotionalCallReport(BaseReport):
    """Report 11: MR Wise Promotional Call (P8 - Coming soon)."""

    key = "mr_wise_promotional_call"
    title = "MR Wise Promotional Call"
    group = "Visits"
    description = "Promotional samples, visual aid demonstrations, and gift distribution per doctor call."
    landscape = True
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    report_number = 11
    status = "P8"
    is_ready = False
    coming_soon_reason = "Needs Phase 8 data (products, sample ledgers, promotional items)"

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="mr_name", label="MR", type="string"),
            ReportColumn(key="date", label="Date", type="date", align="center"),
            ReportColumn(key="customer", label="Customer", type="string"),
            ReportColumn(key="products_promoted", label="Products Promoted", type="string"),
            ReportColumn(key="samples", label="Samples Distributed", type="string"),
            ReportColumn(key="gifts", label="Gifts Given", type="string"),
        ]

    def run_query(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        return []

    def calculate_summary(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return {}


class MrDeviationReport(BaseReport):
    """Report 12: MR Deviation Report (NOW).

    Columns: Date, MR, Planned territory and customers, Actual territory and visits,
    Deviation type (other territory, unplanned, missed), Remarks.
    """

    key = "mr_deviation_report"
    title = "MR Deviation Report"
    group = "Visits"
    description = "Comparison between pre-approved tour plan and actual field visits, highlighting unplanned calls and route deviations."
    landscape = True
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    report_number = 12
    status = "NOW"
    is_ready = True
    filter_schema = ReportFilterSchema(
        date_range=True,
        mr_picker=True,
        territory_picker=True,
        deviation_type_picker=True,
    )

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="date", label="Date", type="date", align="center"),
            ReportColumn(key="mr_name", label="MR", type="string"),
            ReportColumn(key="planned_territory_customers", label="Planned Visits", type="string"),
            ReportColumn(key="actual_territory_visits", label="Actual Visits", type="string"),
            ReportColumn(key="deviation_type", label="Deviation Type", type="status", align="center"),
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
        # Fetch planned visits
        pv_stmt = (
            select(PlannedVisit)
            .options(
                selectinload(PlannedVisit.user),
                selectinload(PlannedVisit.doctor),
                selectinload(PlannedVisit.chemist),
            )
            .order_by(PlannedVisit.plan_date.desc())
        )
        if user_ids is not None:
            pv_stmt = pv_stmt.where(PlannedVisit.user_id.in_(user_ids))
        if filters.territory_id:
            terr_user_ids = db.execute(
                select(UserTerritoryAssignment.user_id).where(
                    UserTerritoryAssignment.territory_id == filters.territory_id
                )
            ).scalars().all()
            pv_stmt = pv_stmt.where(PlannedVisit.user_id.in_(terr_user_ids))

        if start_utc and end_utc:
            pv_stmt = pv_stmt.where(PlannedVisit.plan_date >= start_utc.date(), PlannedVisit.plan_date <= end_utc.date())

        planned_visits = list(db.scalars(pv_stmt).all())

        # Fetch actual DCR visits
        dcr_stmt = (
            select(DcrVisit)
            .options(
                selectinload(DcrVisit.user),
                selectinload(DcrVisit.doctor),
                selectinload(DcrVisit.chemist),
            )
            .order_by(DcrVisit.dcr_date.desc())
        )
        if user_ids is not None:
            dcr_stmt = dcr_stmt.where(DcrVisit.user_id.in_(user_ids))
        if filters.territory_id:
            terr_user_ids = db.execute(
                select(UserTerritoryAssignment.user_id).where(
                    UserTerritoryAssignment.territory_id == filters.territory_id
                )
            ).scalars().all()
            dcr_stmt = dcr_stmt.where(DcrVisit.user_id.in_(terr_user_ids))

        if start_utc and end_utc:
            dcr_stmt = dcr_stmt.where(DcrVisit.dcr_date >= start_utc.date(), DcrVisit.dcr_date <= end_utc.date())

        dcr_visits = list(db.scalars(dcr_stmt).all())
        completed_pv_ids = {v.planned_visit_id for v in dcr_visits if v.planned_visit_id}

        results: list[dict[str, Any]] = []

        # 1. Missed Planned Visits
        for pv in planned_visits:
            if pv.id not in completed_pv_ids and pv.status != "COMPLETED":
                cust = (
                    f"Dr. {pv.doctor.full_name}"
                    if pv.doctor
                    else (pv.chemist.shop_name if pv.chemist else f"{pv.customer_type} #{pv.id}")
                )
                results.append({
                    "date": pv.plan_date.strftime("%d-%b-%Y"),
                    "mr_name": pv.user.full_name if pv.user else f"MR #{pv.user_id}",
                    "planned_territory_customers": cust,
                    "actual_territory_visits": "None (Not Visited)",
                    "deviation_type": "Missed Call",
                    "remarks": pv.notes or "Scheduled appointment not fulfilled",
                })

        # 2. Unplanned Actual Visits
        for dv in dcr_visits:
            if not dv.planned_visit_id:
                cust = (
                    f"Dr. {dv.doctor.full_name}"
                    if dv.doctor
                    else (dv.chemist.shop_name if dv.chemist else f"{dv.customer_type} #{dv.id}")
                )
                results.append({
                    "date": dv.dcr_date.strftime("%d-%b-%Y"),
                    "mr_name": dv.user.full_name if dv.user else f"MR #{dv.user_id}",
                    "planned_territory_customers": "None (Unplanned)",
                    "actual_territory_visits": cust,
                    "deviation_type": "Unplanned Call",
                    "remarks": dv.remarks or "Customer visited outside approved tour plan",
                })

        if filters.deviation_type and filters.deviation_type != "All":
            results = [r for r in results if filters.deviation_type.lower() in r["deviation_type"].lower()]

        return results

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        tot = len(items)
        missed = sum(1 for it in items if it.get("deviation_type") == "Missed Call")
        unplanned = sum(1 for it in items if it.get("deviation_type") == "Unplanned Call")
        return {
            "total_deviations": tot,
            "missed_planned_calls": missed,
            "unplanned_calls": unplanned,
        }


ReportRegistry.register(MrWiseVisitsReport)
ReportRegistry.register(MrWiseVisitsAnalysisReport)
ReportRegistry.register(MrDesignationWiseVisitsAnalysisReport)
ReportRegistry.register(MrWiseDoctorChemistCallReport)
ReportRegistry.register(MrWisePromotionalCallReport)
ReportRegistry.register(MrDeviationReport)
