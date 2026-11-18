"""Metric Handler: Work Duration (TIMELINE)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import selectinload

from app.modules.attendance.models import Attendance
from app.modules.dashboard.metrics.base import BaseMetricHandler, MetricHandlerContext
from app.modules.dashboard.schemas import MetricDetailResponse, MetricTimelineEvent
from app.modules.dcr.models import DcrVisit


class WorkDurationMetric(BaseMetricHandler):
    key = "work_duration"
    title = "Work Duration"
    kind = "TIMELINE"
    color_group = "primary"

    def get_summary_value(self, ctx: MetricHandlerContext) -> tuple[Any, str]:
        atts = (
            ctx.db.query(Attendance)
            .filter(
                Attendance.user_id == ctx.employee.id,
                Attendance.date >= ctx.from_date,
                Attendance.date <= ctx.to_date,
            )
            .all()
        )
        total_mins = sum(a.total_work_minutes or 0 for a in atts) if atts else 0
        h = total_mins // 60
        m = total_mins % 60
        formatted = f"{h:02d}:{m:02d}" if total_mins > 0 else "--:--"
        return total_mins, formatted

    def get_detail(self, ctx: MetricHandlerContext) -> MetricDetailResponse:
        # 1. Fetch attendance for date range
        atts = (
            ctx.db.query(Attendance)
            .filter(
                Attendance.user_id == ctx.employee.id,
                Attendance.date >= ctx.from_date,
                Attendance.date <= ctx.to_date,
            )
            .order_by(Attendance.date.asc())
            .all()
        )

        # 2. Fetch all visits
        visits = (
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
            .order_by(DcrVisit.call_time.asc())
            .all()
        )

        events: list[MetricTimelineEvent] = []

        # Interleave check-in, calls with gaps, and check-out
        for att in atts:
            if att.check_in_time:
                events.append(
                    MetricTimelineEvent(
                        time=att.check_in_time.strftime("%I:%M %p"),
                        title=f"Punch In for Duty ({att.date})",
                        subtitle=att.check_in_address or "GPS Location Recorded",
                        type="CHECK_IN",
                        status="STARTED",
                        latitude=att.check_in_latitude,
                        longitude=att.check_in_longitude,
                        address=att.check_in_address,
                        verified=not att.check_in_mock_flag,
                    )
                )

        prev_time = None
        for v in visits:
            cust_name = "Customer"
            cust_addr = None
            if v.doctor:
                cust_name = f"Dr. {v.doctor.full_name} ({v.doctor.category or 'Doctor'})"
                cust_addr = v.doctor.address
            elif v.chemist:
                cust_name = f"{v.chemist.shop_name} (Chemist)"
                cust_addr = v.chemist.address
            elif v.hospital:
                cust_name = f"{v.hospital.name} (Hospital)"
                cust_addr = v.hospital.address
            elif v.stockist:
                cust_name = f"{v.stockist.agency_name} (Stockist)"
                cust_addr = v.stockist.address

            # Check gap between previous activity and this visit
            if prev_time and v.call_time:
                gap_mins = int((v.call_time - prev_time).total_seconds() / 60)
                if gap_mins >= 15:
                    events.append(
                        MetricTimelineEvent(
                            time=prev_time.strftime("%I:%M %p"),
                            title=f"Transit / Travel Gap: {gap_mins} minutes",
                            subtitle="Movement towards next field station",
                            type="GAP",
                            duration_minutes=gap_mins,
                        )
                    )

            events.append(
                MetricTimelineEvent(
                    time=v.call_time.strftime("%I:%M %p") if v.call_time else "-",
                    title=f"Customer Visit: {cust_name}",
                    subtitle=cust_addr or "Customer call logged in DCR",
                    type="CALL",
                    status="COMPLETED",
                    latitude=v.latitude,
                    longitude=v.longitude,
                    address=cust_addr,
                    verified=v.is_geofence_verified,
                )
            )
            prev_time = v.call_time

        for att in atts:
            if att.check_out_time:
                mins = att.total_work_minutes or 0
                events.append(
                    MetricTimelineEvent(
                        time=att.check_out_time.strftime("%I:%M %p"),
                        title=f"Punchout / Duty End ({att.date})",
                        subtitle=f"Total field duration: {mins // 60}h {mins % 60}m",
                        type="CHECK_OUT",
                        status="COMPLETED",
                        latitude=att.check_out_latitude,
                        longitude=att.check_out_longitude,
                        address=att.check_out_address,
                        verified=not att.check_out_mock_flag,
                    )
                )

        return MetricDetailResponse(
            meta=self.build_meta(ctx),
            events=events,
            total=len(events),
            page=1,
            page_size=max(1, len(events)),
        )
