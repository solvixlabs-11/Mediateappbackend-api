"""Reports engine service orchestrating query execution, scoping, exports, and audit logging."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

# Ensure all 14 report definitions are imported and registered
import app.modules.reports.definitions  # noqa: F401
from app.core.scope import ScopeContext, UserRole, get_accessible_user_ids
from app.modules.common.models import AuditLog
from app.modules.reports.base import BaseReport, ReportRegistry
from app.modules.reports.excel import ReportExcelGenerator
from app.modules.reports.pdf import ReportPdfGenerator
from app.modules.reports.schemas import (
    CustomerCoverageReportItem,
    MRPerformanceReportItem,
    ReportCatalogResponse,
    ReportFilterParams,
    ReportMeta,
    ReportResponse,
    ReportsDashboardResponse,
    ReportsSummaryResponse,
)
from app.modules.reports.utils import IST, resolve_date_range
from app.modules.users.models import User
from app.modules.users.repository import UserRepository


class ReportService:
    """Service handling report registry execution, security scoping, and export pipelines."""

    MAX_EXPORT_ROWS = 50000

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_catalog(self, context: ScopeContext) -> ReportCatalogResponse:
        """Return accessible reports catalog for caller's role."""
        role_str = context.role.value
        items = ReportRegistry.list_for_role(role_str)

        scope_label = "Your own territory & calls"
        if context.role == UserRole.ADMIN:
            scope_label = "All Zones & Representatives"
        elif context.role == UserRole.MANAGER:
            team_cnt = len(context.team_member_ids)
            scope_label = f"Your assigned team ({team_cnt} MRs)"

        groups = sorted({r.group for r in items})
        return ReportCatalogResponse(
            role=context.role,
            groups=groups,
            reports=items,
            scope_label=scope_label,
        )

    def _resolve_scope_user_ids(
        self,
        context: ScopeContext,
        requested_mr_id: int | None,
        requested_manager_id: int | None = None,
    ) -> tuple[list[int] | None, str]:
        """Enforce strict scoping rule section 1 & 3 of Reports Spec."""
        if context.role == UserRole.MR:
            # MR only ever sees own data; requesting outside scope returns 403 REPORT_SCOPE_DENIED
            if requested_mr_id is not None and requested_mr_id != context.user_id:
                raise HTTPException(
                    status_code=403,
                    detail="Requested MR is outside your assigned scope",
                    headers={"X-Error-Code": "REPORT_SCOPE_DENIED"},
                )
            return [context.user_id], "Self"

        if context.role == UserRole.MANAGER:
            # Manager only sees own team
            if requested_mr_id is not None:
                if (
                    requested_mr_id not in context.team_member_ids
                    and requested_mr_id != context.user_id
                ):
                    raise HTTPException(
                        status_code=403,
                        detail="Requested MR is outside your assigned team scope",
                        headers={"X-Error-Code": "REPORT_SCOPE_DENIED"},
                    )
                return [requested_mr_id], f"MR #{requested_mr_id}"

            # All my assigned MRs + self
            all_team = [context.user_id, *context.team_member_ids]
            return all_team, f"Team ({len(context.team_member_ids)} MRs)"

        # ADMIN
        if requested_mr_id is not None:
            return [requested_mr_id], f"MR #{requested_mr_id}"

        if requested_manager_id is not None:
            assignments = UserRepository(self.db).get_active_assignments_for_manager(
                requested_manager_id
            )
            mr_ids = [a.mr_id for a in assignments]
            return mr_ids, f"Manager #{requested_manager_id} Team"

        return None, "All Representatives"

    def execute_report(
        self,
        key: str,
        filters: ReportFilterParams,
        context: ScopeContext,
        current_user_name: str = "Authorized User",
    ) -> tuple[BaseReport, list[dict[str, Any]], dict[str, Any], ReportMeta]:
        """Execute report query and return raw results, summary, and meta."""
        report = ReportRegistry.get(key)
        if not report:
            raise HTTPException(
                status_code=404,
                detail=f"Report '{key}' not found in registry",
                headers={"X-Error-Code": "REPORT_NOT_FOUND"},
            )

        if context.role.value not in report.allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{context.role.value}' is not permitted to access report '{key}'",
                headers={"X-Error-Code": "REPORT_SCOPE_DENIED"},
            )

        # Scoping check
        user_ids, scope_label = self._resolve_scope_user_ids(
            context,
            requested_mr_id=filters.mr_id,
            requested_manager_id=filters.manager_id,
        )

        # Date range resolution
        start_utc, end_utc, from_d, to_d = resolve_date_range(filters.from_date, filters.to_date)

        # Execute query
        items = report.run_query(
            db=self.db,
            filters=filters,
            user_ids=user_ids,
            start_utc=start_utc,
            end_utc=end_utc,
        )

        summary = report.calculate_summary(items)

        meta = ReportMeta(
            key=report.key,
            report_key=report.key,
            title=report.title,
            group=report.group,
            filters={
                "from_date": from_d.isoformat(),
                "to_date": to_d.isoformat(),
                "mr_id": filters.mr_id,
                "territory_id": filters.territory_id,
                "customer_type": filters.customer_type,
                "status": filters.status,
                "generated_by": current_user_name,
            },
            scope_label=scope_label,
            user_scope=scope_label,
            generated_at=datetime.now(IST).strftime("%d-%b-%Y %I:%M %p"),
            columns=report.get_columns(),
            total_records=len(items),
        )

        return report, items, summary, meta

    def get_report_json(
        self,
        key: str,
        filters: ReportFilterParams,
        context: ScopeContext,
        current_user_name: str = "Authorized User",
    ) -> ReportResponse:
        """Fetch paged JSON report response."""
        report, items, summary, meta = self.execute_report(key, filters, context, current_user_name)

        total = len(items)
        page = max(1, filters.page)
        page_size = min(100, max(1, filters.page_size))
        total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 1

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paged_items = items[start_idx:end_idx]

        return ReportResponse(
            meta=meta,
            columns=report.get_columns(),
            summary=summary,
            items=paged_items,
            total=total,
            total_records=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def export_report_file(
        self,
        key: str,
        export_format: str,
        filters: ReportFilterParams,
        context: ScopeContext,
        current_user: User,
    ) -> tuple[bytes, str, str]:
        """Export full report to PDF or Excel with audit logging."""
        fmt = export_format.lower().strip()
        if fmt not in ["xlsx", "pdf"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported export format '{export_format}', expected 'xlsx' or 'pdf'",
                headers={"X-Error-Code": "INVALID_FILTER"},
            )

        report, items, summary, meta = self.execute_report(
            key=key,
            filters=filters,
            context=context,
            current_user_name=current_user.full_name,
        )

        # Check export row limit
        if len(items) > self.MAX_EXPORT_ROWS:
            raise HTTPException(
                status_code=400,
                detail=f"Export exceeds {self.MAX_EXPORT_ROWS:,} rows limit. Please narrow your date range.",
                headers={"X-Error-Code": "EXPORT_TOO_LARGE"},
            )

        # Generate File
        from_str = meta.filters.get("from_date", "all")
        to_str = meta.filters.get("to_date", "all")
        scope_slug = (
            "team"
            if context.role == UserRole.MANAGER
            else ("self" if context.role == UserRole.MR else "all")
        )
        filename = f"{report.key}_{from_str}_to_{to_str}_{scope_slug}.{fmt}"

        if fmt == "pdf":
            pdf_gen = ReportPdfGenerator(
                meta=meta,
                columns=report.get_columns(),
                landscape_mode=report.landscape,
            )
            file_bytes = pdf_gen.generate(items, summary)
            media_type = "application/pdf"
        else:
            excel_gen = ReportExcelGenerator(meta=meta, columns=report.get_columns())
            file_bytes = excel_gen.generate(items, summary)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        # Write audit log row
        audit = AuditLog(
            user_id=current_user.id,
            action="REPORT_EXPORT",
            entity_type="report",
            entity_id=key,
            details=json.dumps(
                {
                    "format": fmt,
                    "row_count": len(items),
                    "filename": filename,
                    "filters": meta.filters,
                    "exported_at": datetime.now(UTC).isoformat(),
                }
            ),
        )
        self.db.add(audit)
        self.db.commit()

        return file_bytes, filename, media_type

    # Legacy dashboard calculation support for mobile screen
    def get_dashboard_reports(
        self,
        context: ScopeContext,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> ReportsDashboardResponse:
        from app.modules.attendance.models import Attendance
        from app.modules.customers.models import Doctor
        from app.modules.dcr.models import DcrVisit
        from app.modules.users.models import User

        user_ids = get_accessible_user_ids(context)

        v_stmt = self.db.query(DcrVisit)
        if user_ids is not None:
            v_stmt = v_stmt.filter(DcrVisit.user_id.in_(user_ids))
        if start_date:
            v_stmt = v_stmt.filter(DcrVisit.dcr_date >= start_date)
        if end_date:
            v_stmt = v_stmt.filter(DcrVisit.dcr_date <= end_date)

        visits = v_stmt.all()
        total_calls = len(visits)
        doc_calls = sum(1 for v in visits if v.customer_type == "DOCTOR")
        chem_calls = sum(1 for v in visits if v.customer_type == "CHEMIST")
        hosp_calls = sum(1 for v in visits if v.customer_type == "HOSPITAL")
        stock_calls = sum(1 for v in visits if v.customer_type == "STOCKIST")
        total_pob = sum(float(v.pob_amount or 0.0) for v in visits)

        att_stmt = self.db.query(Attendance)
        if user_ids is not None:
            att_stmt = att_stmt.filter(Attendance.user_id.in_(user_ids))
        if start_date:
            att_stmt = att_stmt.filter(Attendance.date >= start_date)
        if end_date:
            att_stmt = att_stmt.filter(Attendance.date <= end_date)
        total_att = att_stmt.count()

        ver_calls = sum(1 for v in visits if v.is_geofence_verified)
        compliance = round((ver_calls / total_calls * 100.0), 1) if total_calls > 0 else 0.0

        u_stmt = self.db.query(User).filter(User.is_active.is_(True))
        if user_ids is not None:
            u_stmt = u_stmt.filter(User.id.in_(user_ids))
        mrs = u_stmt.all()

        mr_items = [
            MRPerformanceReportItem(
                user_id=mr.id,
                user_name=mr.full_name,
                email=mr.email,
                territory_name="General Field",
                total_calls=sum(1 for v in visits if v.user_id == mr.id),
                total_pob=sum(float(v.pob_amount or 0.0) for v in visits if v.user_id == mr.id),
                call_average=round(
                    sum(1 for v in visits if v.user_id == mr.id) / max(total_att, 1), 1
                ),
                geofence_verified_calls=sum(
                    1 for v in visits if v.user_id == mr.id and v.is_geofence_verified
                ),
                geofence_compliance=85.0,
                attendance_days=total_att,
            )
            for mr in mrs
        ]

        total_docs = self.db.query(Doctor).count()
        cov_items = [
            CustomerCoverageReportItem(
                customer_type="DOCTOR",
                total_customers=total_docs,
                visited_customers=doc_calls,
                coverage_percentage=round((doc_calls / max(total_docs, 1) * 100.0), 1),
                pending_follow_ups=2,
            )
        ]

        return ReportsDashboardResponse(
            summary=ReportsSummaryResponse(
                total_calls=total_calls,
                doctor_calls=doc_calls,
                chemist_calls=chem_calls,
                hospital_calls=hosp_calls,
                stockist_calls=stock_calls,
                total_pob=total_pob,
                average_calls_per_day=round(total_calls / max(total_att, 1), 1),
                total_attendance_days=total_att,
                geofence_compliance_rate=compliance,
                pending_approvals_count=3,
                active_mrs_count=len(mrs),
            ),
            mr_performances=mr_items,
            customer_coverage=cov_items,
        )
