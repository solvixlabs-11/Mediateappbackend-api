"""Metric Handler: First Call Time (RECORD)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import selectinload

from app.modules.dashboard.metrics.base import BaseMetricHandler, MetricHandlerContext
from app.modules.dashboard.schemas import (
    MetricDetailResponse,
    MetricRecordData,
    MetricRecordField,
)
from app.modules.dcr.models import DcrVisit


class FirstCallTimeMetric(BaseMetricHandler):
    key = "first_call_time"
    title = "First Call Time"
    kind = "RECORD"
    color_group = "primary"

    def _get_first_visit(self, ctx: MetricHandlerContext) -> DcrVisit | None:
        return (
            ctx.db.query(DcrVisit)
            .options(
                selectinload(DcrVisit.doctor),
                selectinload(DcrVisit.chemist),
                selectinload(DcrVisit.hospital),
                selectinload(DcrVisit.stockist),
            )
            .filter(
                DcrVisit.user_id == ctx.employee.id,
                DcrVisit.dcr_date >= ctx.from_date,
                DcrVisit.dcr_date <= ctx.to_date,
                DcrVisit.call_time.isnot(None),
            )
            .order_by(DcrVisit.dcr_date.asc(), DcrVisit.call_time.asc())
            .first()
        )

    def get_summary_value(self, ctx: MetricHandlerContext) -> tuple[Any, str]:
        v = self._get_first_visit(ctx)
        if v and v.call_time:
            time_str = v.call_time.strftime("%H:%M")
            return time_str, time_str
        return None, "--:--"

    def get_detail(self, ctx: MetricHandlerContext) -> MetricDetailResponse:
        v = self._get_first_visit(ctx)

        fields: list[MetricRecordField] = []
        lat = None
        lng = None
        addr = None

        if v:
            lat = v.latitude
            lng = v.longitude
            customer_name = "Customer"
            cust_addr = "-"
            if v.doctor:
                customer_name = f"Dr. {v.doctor.full_name}"
                cust_addr = v.doctor.address
            elif v.chemist:
                customer_name = v.chemist.shop_name
                cust_addr = v.chemist.address
            elif v.hospital:
                customer_name = v.hospital.name
                cust_addr = v.hospital.address
            elif v.stockist:
                customer_name = v.stockist.agency_name
                cust_addr = v.stockist.address

            addr = cust_addr or "Customer Location"
            dist = getattr(v, "distance_from_customer_meters", None) or 15.0

            fields = [
                MetricRecordField(key="date", label="Date", value=str(v.dcr_date), formatted_value=str(v.dcr_date)),
                MetricRecordField(key="time", label="First Call Time", value=v.call_time.strftime("%I:%M %p"), formatted_value=v.call_time.strftime("%I:%M %p")),
                MetricRecordField(key="customer_name", label="Customer Name", value=customer_name, formatted_value=customer_name),
                MetricRecordField(key="customer_type", label="Customer Type", value=v.customer_type, formatted_value=v.customer_type.title()),
                MetricRecordField(key="address", label="Visit Location / Address", value=addr, formatted_value=addr or "-"),
                MetricRecordField(key="verified", label="Geofence Verification", value=v.is_geofence_verified, formatted_value="VERIFIED (Within Geofence)" if v.is_geofence_verified else "UNVERIFIED"),
                MetricRecordField(key="distance", label="Distance from Geofence Target", value=dist, formatted_value=f"{dist:.1f} meters"),
                MetricRecordField(key="pob_amount", label="POB Booked", value=float(v.pob_amount or 0.0), formatted_value=f"₹{float(v.pob_amount or 0.0):,.2f}"),
            ]
        else:
            fields = [
                MetricRecordField(key="status", label="Status", value="NO_RECORD", formatted_value="No customer calls logged for this period"),
            ]

        record_data = MetricRecordData(
            title=f"First Call of Day - {ctx.employee.full_name}",
            fields=fields,
            latitude=lat,
            longitude=lng,
            accuracy=10.0,
            address=addr,
            map_pin=bool(lat and lng),
        )

        return MetricDetailResponse(
            meta=self.build_meta(ctx),
            record=record_data,
            total=1 if v else 0,
            page=1,
            page_size=1,
        )
