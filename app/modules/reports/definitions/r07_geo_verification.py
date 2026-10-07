"""R07 - Geo-Verification Report."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.dcr.models import DcrVisit
from app.modules.reports.base import BaseReport, ReportRegistry
from app.modules.reports.schemas import ReportColumn, ReportFilterParams, ReportFilterSchema
from app.modules.reports.utils import utc_to_ist_date, utc_to_ist_time


class GeoVerificationReport(BaseReport):
    """R07 Geo-Verification.

    Distance, radius, accuracy, verified or not, mock-location flag.
    """

    key = "geo_verification"
    title = "Geo-Verification Report"
    group = "Activity"
    description = "GPS distance, customer radius, handset accuracy, geofence verification, and mock location audit."
    landscape = True
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    filter_schema = ReportFilterSchema(
        date_range=True,
        mr_picker=True,
        status_picker=True,
        status_options=["All", "Verified", "Not Verified", "Mock Detected"],
    )

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="date", label="Date", type="date", align="center"),
            ReportColumn(key="time", label="Time", type="string", align="center"),
            ReportColumn(key="mr_name", label="MR", type="string"),
            ReportColumn(key="customer", label="Customer", type="string"),
            ReportColumn(key="distance_m", label="Distance (m)", type="number", align="right"),
            ReportColumn(key="radius_m", label="Radius (m)", type="number", align="right"),
            ReportColumn(key="accuracy_m", label="Accuracy (m)", type="number", align="right"),
            ReportColumn(key="verified", label="Verified", type="status", align="center"),
            ReportColumn(key="mock_location", label="Mock Location", type="status", align="center"),
            ReportColumn(key="reason", label="Reason", type="string"),
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
                selectinload(DcrVisit.doctor),
                selectinload(DcrVisit.chemist),
                selectinload(DcrVisit.hospital),
                selectinload(DcrVisit.stockist),
            )
            .order_by(DcrVisit.call_time.desc())
        )

        if user_ids is not None:
            stmt = stmt.where(DcrVisit.user_id.in_(user_ids))
        if start_utc and end_utc:
            stmt = stmt.where(DcrVisit.call_time >= start_utc, DcrVisit.call_time <= end_utc)

        if filters.status:
            stat_l = filters.status.lower()
            if stat_l == "verified":
                stmt = stmt.where(DcrVisit.is_geofence_verified.is_(True))
            elif stat_l in ["not verified", "not_verified"]:
                stmt = stmt.where(DcrVisit.is_geofence_verified.is_(False))
            elif stat_l in ["mock", "mock detected"]:
                stmt = stmt.where(DcrVisit.is_mock_location.is_(True))

        records = db.scalars(stmt).all()
        results: list[dict[str, Any]] = []

        for v in records:
            cust_name = "-"
            if v.doctor:
                cust_name = f"Dr. {v.doctor.name}"
            elif v.chemist:
                cust_name = v.chemist.name
            elif v.hospital:
                cust_name = v.hospital.name
            elif v.stockist:
                cust_name = v.stockist.name

            dist = (
                round(v.distance_to_customer_meters, 1)
                if v.distance_to_customer_meters is not None
                else None
            )
            rad = (
                round(v.geofence_radius_meters, 1)
                if v.geofence_radius_meters is not None
                else 200.0
            )
            acc = round(v.location_accuracy, 1) if v.location_accuracy is not None else None

            # Reason
            reason = "Inside customer geofence perimeter"
            if v.is_mock_location:
                reason = "Mock location provider detected on handset"
            elif not v.is_geofence_verified:
                if dist is not None and rad is not None and dist > rad:
                    reason = f"Distance ({dist}m) exceeded geofence radius ({rad}m)"
                elif acc is not None and acc > 100.0:
                    reason = f"Poor GPS accuracy ({acc}m > 100m threshold)"
                else:
                    reason = "Outside customer geofence radius"

            results.append(
                {
                    "date": utc_to_ist_date(v.call_time),
                    "time": utc_to_ist_time(v.call_time),
                    "mr_name": v.user.full_name if v.user else f"MR #{v.user_id}",
                    "customer": cust_name,
                    "distance_m": dist,
                    "radius_m": rad,
                    "accuracy_m": acc,
                    "verified": "Verified" if v.is_geofence_verified else "Not Verified",
                    "mock_location": "Yes" if v.is_mock_location else "No",
                    "reason": reason,
                    "_raw_verified": v.is_geofence_verified,
                    "_raw_mock": v.is_mock_location,
                }
            )

        return results

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        total = len(items)
        if total == 0:
            return {
                "total_calls": 0,
                "verified_calls": 0,
                "verified_pct": 0.0,
                "not_verified_count": 0,
                "mock_count": 0,
            }

        verified = sum(1 for it in items if it.get("_raw_verified"))
        not_verified = total - verified
        mock = sum(1 for it in items if it.get("_raw_mock"))
        pct = round(verified / total * 100.0, 1)

        return {
            "total_calls": total,
            "verified_calls": verified,
            "verified_pct": pct,
            "not_verified_count": not_verified,
            "mock_count": mock,
        }


ReportRegistry.register(GeoVerificationReport)
