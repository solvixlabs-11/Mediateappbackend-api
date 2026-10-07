"""R01 - DCR Detailed Report (Date-wise)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.customers.models import Chemist, Doctor, Hospital, Stockist
from app.modules.dcr.models import DcrVisit
from app.modules.reports.base import BaseReport, ReportRegistry
from app.modules.reports.schemas import ReportColumn, ReportFilterParams, ReportFilterSchema
from app.modules.reports.utils import utc_to_ist_date, utc_to_ist_time


class DcrDetailedReport(BaseReport):
    """R01 DCR Detailed (date wise).

    Shows every visit report with products, samples, gifts, outcome, verification,
    and supports date-wise grouping with day subtotals in PDF/Excel.
    """

    key = "dcr_detailed"
    title = "DCR Detailed Report"
    group = "Activity"
    description = "Every visit report, grouped by date, with products, samples, gifts, outcome, and verification."
    landscape = True
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
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
            ReportColumn(key="mr_name", label="MR", type="string"),
            ReportColumn(key="emp_code", label="Emp Code", type="string", align="center"),
            ReportColumn(key="time", label="Time", type="string", align="center"),
            ReportColumn(key="visit_type", label="Visit Type", type="string"),
            ReportColumn(key="customer_name", label="Customer", type="string"),
            ReportColumn(key="customer_type", label="Customer Type", type="string"),
            ReportColumn(key="specialization", label="Specialization/Type", type="string"),
            ReportColumn(key="category", label="Category", type="string", align="center"),
            ReportColumn(key="territory", label="Territory", type="string"),
            ReportColumn(key="verified", label="Verified", type="status", align="center"),
            ReportColumn(key="distance_m", label="Distance (m)", type="number", align="right"),
            ReportColumn(key="accuracy_m", label="Accuracy (m)", type="number", align="right"),
            ReportColumn(key="products_promoted", label="Products Promoted", type="string"),
            ReportColumn(key="samples", label="Samples", type="string"),
            ReportColumn(key="gifts", label="Gifts", type="string"),
            ReportColumn(key="outcome", label="Outcome", type="string"),
            ReportColumn(key="remarks", label="Remarks", type="string"),
            ReportColumn(key="next_visit_date", label="Next Visit Date", type="date", align="center"),
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
                selectinload(DcrVisit.product_details),
                selectinload(DcrVisit.post_call_analysis),
            )
            .order_by(DcrVisit.dcr_date.desc(), DcrVisit.call_time.desc())
        )

        if user_ids is not None:
            stmt = stmt.where(DcrVisit.user_id.in_(user_ids))

        if start_utc and end_utc:
            stmt = stmt.where(DcrVisit.call_time >= start_utc, DcrVisit.call_time <= end_utc)

        if filters.customer_type:
            stmt = stmt.where(DcrVisit.customer_type == filters.customer_type.upper())

        if filters.status:
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
            terr = "-"

            if v.doctor:
                cust_name = f"Dr. {v.doctor.full_name}"
                spec = v.doctor.specialization or v.doctor.qualification or "-"
                cat = v.doctor.category or "A"
                terr = v.doctor.territory.name if v.doctor.territory else "-"
            elif v.chemist:
                cust_name = v.chemist.shop_name
                spec = "Retail Chemist"
                cat = "B"
                terr = v.chemist.territory.name if v.chemist.territory else "-"
            elif v.hospital:
                cust_name = v.hospital.name
                spec = v.hospital.type or "Hospital"
                cat = "A"
                terr = v.hospital.territory.name if v.hospital.territory else "-"
            elif v.stockist:
                cust_name = v.stockist.agency_name
                spec = "Wholesale Stockist"
                cat = "A"
                terr = v.stockist.territory.name if v.stockist.territory else "-"

            if filters.territory_id and v.doctor and v.doctor.territory_id != filters.territory_id:
                continue

            products = ", ".join(p.product_name for p in v.product_details) if v.product_details else "-"
            sample_list = [f"{p.product_name} ({p.sample_quantity})" for p in v.product_details if p.sample_quantity > 0]
            samples = ", ".join(sample_list) if sample_list else "-"

            gift_list = [f"{p.product_name} ({p.gift_quantity})" for p in v.product_details if p.gift_quantity > 0]
            gifts = ", ".join(gift_list) if gift_list else "-"

            outcome = v.post_call_analysis.call_outcome if v.post_call_analysis else "-"
            next_visit = (
                v.post_call_analysis.next_visit_date.isoformat()
                if v.post_call_analysis and v.post_call_analysis.next_visit_date
                else "-"
            )

            ist_date = utc_to_ist_date(v.call_time) if v.call_time else v.dcr_date.isoformat()
            ist_time = utc_to_ist_time(v.call_time) if v.call_time else "-"

            total_samples_cnt = sum(p.sample_quantity for p in v.product_details) if v.product_details else 0
            total_gifts_cnt = sum(p.gift_quantity for p in v.product_details) if v.product_details else 0

            results.append({
                "date": ist_date,
                "mr_name": v.user.full_name if v.user else f"MR #{v.user_id}",
                "emp_code": f"EMP-{v.user_id:04d}",
                "time": ist_time,
                "visit_type": v.visit_type or "INDEPENDENT",
                "customer_name": cust_name,
                "customer_type": v.customer_type.title() if v.customer_type else "-",
                "specialization": spec,
                "category": cat,
                "territory": terr,
                "verified": "Verified" if v.is_geofence_verified else "Not Verified",
                "distance_m": round(v.distance_to_customer_meters, 1) if v.distance_to_customer_meters is not None else None,
                "accuracy_m": round(v.location_accuracy, 1) if v.location_accuracy is not None else None,
                "products_promoted": products,
                "samples": samples,
                "gifts": gifts,
                "outcome": outcome,
                "remarks": v.remarks or "-",
                "next_visit_date": next_visit,
                "_raw_customer_type": v.customer_type,
                "_raw_verified": v.is_geofence_verified,
                "_raw_samples_count": total_samples_cnt,
                "_raw_gifts_count": total_gifts_cnt,
            })

        return results

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        total_calls = len(items)
        if total_calls == 0:
            return {
                "total_calls": 0,
                "doctors": 0,
                "chemists": 0,
                "stockists": 0,
                "hospitals": 0,
                "verified_pct": 0.0,
                "unique_customers": 0,
                "total_samples": 0,
                "total_gifts": 0,
            }

        verified_calls = sum(1 for it in items if it.get("_raw_verified"))
        verified_pct = round((verified_calls / total_calls) * 100.0, 1)
        doctors = sum(1 for it in items if str(it.get("_raw_customer_type", "")).upper() == "DOCTOR")
        chemists = sum(1 for it in items if str(it.get("_raw_customer_type", "")).upper() == "CHEMIST")
        stockists = sum(1 for it in items if str(it.get("_raw_customer_type", "")).upper() == "STOCKIST")
        hospitals = sum(1 for it in items if str(it.get("_raw_customer_type", "")).upper() == "HOSPITAL")
        unique_customers = len({it.get("customer_name") for it in items if it.get("customer_name") != "-"})
        total_samples = sum(int(it.get("_raw_samples_count", 0)) for it in items)
        total_gifts = sum(int(it.get("_raw_gifts_count", 0)) for it in items)

        return {
            "total_calls": total_calls,
            "doctors": doctors,
            "chemists": chemists,
            "stockists": stockists,
            "hospitals": hospitals,
            "verified_pct": verified_pct,
            "unique_customers": unique_customers,
            "total_samples": total_samples,
            "total_gifts": total_gifts,
        }


ReportRegistry.register(DcrDetailedReport)
