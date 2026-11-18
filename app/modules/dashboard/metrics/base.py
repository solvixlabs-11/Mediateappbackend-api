"""Base metric handler interface and context for Visits Summary drill-down."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.modules.dashboard.schemas import (
    MetricCardRowItem,
    MetricColumnItem,
    MetricDetailResponse,
    MetricMeta,
    MetricRecordData,
    MetricRecordField,
    MetricTimelineEvent,
)
from app.modules.users.models import User

settings = get_settings()


class MetricHandlerContext(BaseModel):
    """Context passed to metric handlers."""

    model_config = {"arbitrary_types_allowed": True}

    db: Session
    employee: User
    from_date: date
    to_date: date
    division_ids: list[int] | None = None
    state_id: int | None = None
    territory_id: int | None = None
    page: int = 1
    page_size: int = 20


class BaseMetricHandler(ABC):
    """Abstract base class for all 16 Visits Summary metric handlers."""

    key: str
    title: str
    kind: str = "TABLE"  # TABLE, RECORD, TIMELINE
    color_group: str = "primary"  # primary (blue), success (green), danger (red)
    status: str = "AVAILABLE"  # AVAILABLE, COMING_SOON
    unavailable_reason: str | None = None
    can_export: bool = True

    @abstractmethod
    def get_summary_value(self, ctx: MetricHandlerContext) -> tuple[Any, str]:
        """Compute the count/metric value and formatted string for the employee card.

        Returns (raw_value, formatted_string).
        """
        ...

    @abstractmethod
    def get_detail(self, ctx: MetricHandlerContext) -> MetricDetailResponse:
        """Fetch detailed drill-down data (TABLE rows, RECORD detail, or TIMELINE events)."""
        ...

    def export_xlsx(self, ctx: MetricHandlerContext) -> bytes | None:
        """Export detail rows to XLSX spreadsheet bytes (for TABLE metrics)."""
        import io
        import openpyxl
        from openpyxl.styles import Alignment, Font, PatternFill

        detail = self.get_detail(ctx)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = self.title[:31]

        # Title banner
        ws.merge_cells("A1:H1")
        title_cell = ws["A1"]
        title_cell.value = f"{self.title} - {ctx.employee.full_name} ({ctx.from_date} to {ctx.to_date})"
        title_cell.font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
        title_cell.fill = PatternFill(start_color="1B5E20", end_color="1B5E20", fill_type="solid")
        title_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 30

        # Header Row
        columns = detail.meta.columns
        header_fill = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="1B5E20")

        for col_idx, col in enumerate(columns, 1):
            cell = ws.cell(row=2, column=col_idx, value=col.label)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal=col.align or "left")
        ws.row_dimensions[2].height = 24

        # Data Rows
        for row_idx, r_dict in enumerate(detail.rows, 3):
            for col_idx, col in enumerate(columns, 1):
                val = r_dict.get(col.key)
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.font = Font(name="Calibri", size=10)
                cell.alignment = Alignment(horizontal=col.align or "left")
            ws.row_dimensions[row_idx].height = 20

        # Auto-fit column widths
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

        output = io.BytesIO()
        wb.save(output)
        return output.getvalue()

    def build_meta(self, ctx: MetricHandlerContext, columns: list[MetricColumnItem] | None = None) -> MetricMeta:
        """Construct standard MetricMeta response structure."""
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        primary_territory = None
        assignments = getattr(ctx.employee, "territory_assignments", []) or []
        for a in assignments:
            if getattr(a, "unassigned_at", None) is None and getattr(a, "territory", None):
                primary_territory = a.territory.name
                break

        return MetricMeta(
            title=self.title,
            kind=self.kind,
            status=self.status,
            unavailable_reason=self.unavailable_reason,
            columns=columns or [],
            filters={
                "from": str(ctx.from_date),
                "to": str(ctx.to_date),
                "state_id": ctx.state_id,
                "territory_id": ctx.territory_id,
            },
            can_export=self.can_export and self.status == "AVAILABLE",
            employee={
                "id": str(ctx.employee.id),
                "code": getattr(ctx.employee, "employee_code", f"EMP-{ctx.employee.id:04d}"),
                "name": ctx.employee.full_name,
                "territory": primary_territory or "Headquarter",
                "photo_url": getattr(ctx.employee, "avatar_url", None),
            },
            generated_at=now_str,
            data_as_of=now_str,
        )

    def to_card_row(self, ctx: MetricHandlerContext) -> MetricCardRowItem:
        """Generate dynamic MetricCardRowItem for the employee card."""
        raw_val, formatted_val = self.get_summary_value(ctx)
        return MetricCardRowItem(
            key=self.key,
            label=self.title.upper(),
            value=raw_val,
            formatted_value=formatted_val,
            kind=self.kind,
            color_group=self.color_group,
            status=self.status,
            unavailable_reason=self.unavailable_reason,
        )

