"""Metric Handler: Doctor Call Average (TABLE)."""

from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
from typing import Any
from sqlalchemy import func

from app.modules.attendance.models import Attendance
from app.modules.dashboard.metrics.base import BaseMetricHandler, MetricHandlerContext
from app.modules.dashboard.schemas import MetricColumnItem, MetricDetailResponse
from app.modules.dcr.models import DcrVisit


class DoctorCallAverageMetric(BaseMetricHandler):
    key = "doctor_call_average"
    title = "Doctor Call Average"
    kind = "TABLE"
    color_group = "success"

    def get_summary_value(self, ctx: MetricHandlerContext) -> tuple[Any, str]:
        # Count total doctor visits
        doc_visits_count = (
            ctx.db.query(func.count(DcrVisit.id))
            .filter(
                DcrVisit.user_id == ctx.employee.id,
                DcrVisit.customer_type == "DOCTOR",
                DcrVisit.dcr_date >= ctx.from_date,
                DcrVisit.dcr_date <= ctx.to_date,
            )
            .scalar()
            or 0
        )

        # Working days attended
        working_days = (
            ctx.db.query(func.count(Attendance.id))
            .filter(
                Attendance.user_id == ctx.employee.id,
                Attendance.date >= ctx.from_date,
                Attendance.date <= ctx.to_date,
            )
            .scalar()
            or 0
        )

        days = working_days if working_days > 0 else (1 if doc_visits_count > 0 else 0)
        avg = round(doc_visits_count / days, 1) if days > 0 else 0.0
        return avg, f"{avg:.1f}"

    def get_detail(self, ctx: MetricHandlerContext) -> MetricDetailResponse:
        # Generate list of days in the date range
        all_dates = []
        cur = ctx.from_date
        while cur <= ctx.to_date:
            all_dates.append(cur)
            cur += timedelta(days=1)

        # Query doctor calls grouped by date
        calls_query = (
            ctx.db.query(DcrVisit.dcr_date, func.count(DcrVisit.id))
            .filter(
                DcrVisit.user_id == ctx.employee.id,
                DcrVisit.customer_type == "DOCTOR",
                DcrVisit.dcr_date >= ctx.from_date,
                DcrVisit.dcr_date <= ctx.to_date,
            )
            .group_by(DcrVisit.dcr_date)
            .all()
        )
        calls_by_date = {d: c for d, c in calls_query}

        # Query attendances
        atts = (
            ctx.db.query(Attendance)
            .filter(
                Attendance.user_id == ctx.employee.id,
                Attendance.date >= ctx.from_date,
                Attendance.date <= ctx.to_date,
            )
            .all()
        )
        att_by_date = {a.date: a for a in atts}

        columns = [
            MetricColumnItem(key="date", label="Date", type="date"),
            MetricColumnItem(key="day_name", label="Day", type="string"),
            MetricColumnItem(key="is_working", label="Working Day", type="status"),
            MetricColumnItem(key="doctor_calls", label="Doctor Calls", type="number", align="right"),
            MetricColumnItem(key="attendance_status", label="Attendance", type="string"),
            MetricColumnItem(key="running_avg", label="Running Average", type="number", align="right"),
        ]

        total = len(all_dates)
        # Sort descending (most recent first)
        reversed_dates = list(reversed(all_dates))
        paged_dates = reversed_dates[(ctx.page - 1) * ctx.page_size : ctx.page * ctx.page_size]

        # Calculate running stats
        total_calls = 0
        working_days_count = 0
        running_stats: dict[Any, float] = {}
        for d in all_dates:
            calls = calls_by_date.get(d, 0)
            is_att = d in att_by_date
            if is_att or calls > 0:
                working_days_count += 1
                total_calls += calls
                running_stats[d] = round(total_calls / working_days_count, 1) if working_days_count > 0 else 0.0
            else:
                running_stats[d] = round(total_calls / max(1, working_days_count), 1)

        rows = []
        for d in paged_dates:
            calls = calls_by_date.get(d, 0)
            att = att_by_date.get(d)
            is_work = bool(att or calls > 0)
            rows.append({
                "id": str(d),
                "date": d.isoformat(),
                "day_name": d.strftime("%A"),
                "is_working": "WORKING" if is_work else "HOLIDAY_OFF",
                "doctor_calls": calls,
                "attendance_status": "PRESENT" if att else ("FIELD_CALLS" if calls > 0 else "ABSENT"),
                "running_avg": running_stats.get(d, 0.0),
            })

        return MetricDetailResponse(
            meta=self.build_meta(ctx, columns),
            rows=rows,
            total=total,
            page=ctx.page,
            page_size=ctx.page_size,
        )

