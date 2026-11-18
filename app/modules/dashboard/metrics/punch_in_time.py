"""Metric Handler: Punching In Time (RECORD)."""

from __future__ import annotations

from typing import Any

from app.modules.attendance.models import Attendance
from app.modules.dashboard.metrics.base import BaseMetricHandler, MetricHandlerContext
from app.modules.dashboard.schemas import (
    MetricDetailResponse,
    MetricRecordData,
    MetricRecordField,
)


class PunchInTimeMetric(BaseMetricHandler):
    key = "punch_in_time"
    title = "Punching In Time"
    kind = "RECORD"
    color_group = "primary"

    def _get_attendance(self, ctx: MetricHandlerContext) -> Attendance | None:
        return (
            ctx.db.query(Attendance)
            .filter(
                Attendance.user_id == ctx.employee.id,
                Attendance.date >= ctx.from_date,
                Attendance.date <= ctx.to_date,
                Attendance.check_in_time.isnot(None),
            )
            .order_by(Attendance.date.desc(), Attendance.check_in_time.desc())
            .first()
        )

    def get_summary_value(self, ctx: MetricHandlerContext) -> tuple[Any, str]:
        att = self._get_attendance(ctx)
        if att and att.check_in_time:
            time_str = att.check_in_time.strftime("%H:%M")
            return time_str, time_str
        return None, "--:--"

    def get_detail(self, ctx: MetricHandlerContext) -> MetricDetailResponse:
        att = self._get_attendance(ctx)

        fields: list[MetricRecordField] = []
        lat = None
        lng = None
        acc = None
        addr = None
        mock = False

        if att and att.check_in_time:
            lat = att.check_in_latitude
            lng = att.check_in_longitude
            acc = att.check_in_accuracy
            addr = att.check_in_address or "Location verified on device"
            mock = bool(att.check_in_mock_flag)

            fields = [
                MetricRecordField(key="date", label="Date", value=str(att.date), formatted_value=str(att.date)),
                MetricRecordField(key="time", label="Punch In Time", value=att.check_in_time.strftime("%I:%M %p"), formatted_value=att.check_in_time.strftime("%I:%M %p")),
                MetricRecordField(key="address", label="Address / Landmark", value=addr, formatted_value=addr),
                MetricRecordField(key="latitude", label="Latitude", value=lat, formatted_value=f"{lat:.6f}" if lat is not None else "-"),
                MetricRecordField(key="longitude", label="Longitude", value=lng, formatted_value=f"{lng:.6f}" if lng is not None else "-"),
                MetricRecordField(key="accuracy", label="GPS Accuracy", value=acc, formatted_value=f"{acc:.1f} meters" if acc is not None else "-"),
                MetricRecordField(key="mock_flag", label="Mock GPS Detected", value=mock, formatted_value="YES (Warning)" if mock else "NO (Genuine GPS)"),
                MetricRecordField(key="status", label="Check-in Status", value="VERIFIED", formatted_value="Verified Attendance"),
            ]
        else:
            fields = [
                MetricRecordField(key="status", label="Status", value="NO_RECORD", formatted_value="No Punch-in record found for this period"),
            ]

        record_data = MetricRecordData(
            title=f"Punch In - {ctx.employee.full_name}",
            fields=fields,
            latitude=lat,
            longitude=lng,
            accuracy=acc,
            address=addr,
            map_pin=bool(lat and lng),
            mock_flag=mock,
        )

        return MetricDetailResponse(
            meta=self.build_meta(ctx),
            record=record_data,
            total=1 if att else 0,
            page=1,
            page_size=1,
        )
