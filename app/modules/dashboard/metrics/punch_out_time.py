"""Metric Handler: Punchout Time (RECORD)."""

from __future__ import annotations

from typing import Any

from app.modules.attendance.models import Attendance
from app.modules.dashboard.metrics.base import BaseMetricHandler, MetricHandlerContext
from app.modules.dashboard.schemas import (
    MetricDetailResponse,
    MetricRecordData,
    MetricRecordField,
)


class PunchOutTimeMetric(BaseMetricHandler):
    key = "punch_out_time"
    title = "Punchout Time"
    kind = "RECORD"
    color_group = "primary"

    def _get_attendance(self, ctx: MetricHandlerContext) -> Attendance | None:
        return (
            ctx.db.query(Attendance)
            .filter(
                Attendance.user_id == ctx.employee.id,
                Attendance.date >= ctx.from_date,
                Attendance.date <= ctx.to_date,
                Attendance.check_out_time.isnot(None),
            )
            .order_by(Attendance.date.desc(), Attendance.check_out_time.desc())
            .first()
        )

    def get_summary_value(self, ctx: MetricHandlerContext) -> tuple[Any, str]:
        att = self._get_attendance(ctx)
        if att and att.check_out_time:
            time_str = att.check_out_time.strftime("%H:%M")
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

        if att and att.check_out_time:
            lat = att.check_out_latitude
            lng = att.check_out_longitude
            acc = att.check_out_accuracy
            addr = att.check_out_address or "Location verified on device"
            mock = bool(att.check_out_mock_flag)

            work_mins = att.total_work_minutes or 0
            hours = work_mins // 60
            mins = work_mins % 60
            duration_str = f"{hours}h {mins}m ({work_mins} minutes)"

            fields = [
                MetricRecordField(key="date", label="Date", value=str(att.date), formatted_value=str(att.date)),
                MetricRecordField(key="time", label="Punchout Time", value=att.check_out_time.strftime("%I:%M %p"), formatted_value=att.check_out_time.strftime("%I:%M %p")),
                MetricRecordField(key="address", label="Address / Landmark", value=addr, formatted_value=addr),
                MetricRecordField(key="latitude", label="Latitude", value=lat, formatted_value=f"{lat:.6f}" if lat is not None else "-"),
                MetricRecordField(key="longitude", label="Longitude", value=lng, formatted_value=f"{lng:.6f}" if lng is not None else "-"),
                MetricRecordField(key="accuracy", label="GPS Accuracy", value=acc, formatted_value=f"{acc:.1f} meters" if acc is not None else "-"),
                MetricRecordField(key="total_work", label="Total Field Duration", value=work_mins, formatted_value=duration_str),
                MetricRecordField(key="mock_flag", label="Mock GPS Detected", value=mock, formatted_value="YES (Warning)" if mock else "NO (Genuine GPS)"),
                MetricRecordField(key="status", label="Checkout Status", value="COMPLETED", formatted_value="Day Completed Successfully"),
            ]
        else:
            fields = [
                MetricRecordField(key="status", label="Status", value="NO_RECORD", formatted_value="No Punchout record found for this period"),
            ]

        record_data = MetricRecordData(
            title=f"Punchout Record - {ctx.employee.full_name}",
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
