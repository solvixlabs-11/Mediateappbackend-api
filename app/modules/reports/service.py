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
from app.modules.customers.models import Chemist, Doctor, Stockist
from app.modules.masters.models import Area, City, MasterItem, State
from app.modules.products.models import Product
from app.modules.reports.base import BaseReport, ReportRegistry
from app.modules.reports.engine.registry import ReportEngineRegistry
from app.modules.reports.engine.scope import validate_report_scope
from app.modules.reports.engine.validator import validate_filter_schema
from app.modules.reports.excel import ReportExcelGenerator
from app.modules.reports.models import ReportDefinition
from app.modules.reports.pdf import ReportPdfGenerator
from app.modules.reports.schemas import (
    CustomerCoverageReportItem,
    MRPerformanceReportItem,
    ReportCatalogResponse,
    ReportCatalogV3Response,
    ReportDefinitionItem,
    ReportExportRequest,
    ReportFilterParams,
    ReportMeta,
    ReportOptionItem,
    ReportOptionsResponse,
    ReportResponse,
    ReportRunRequest,
    ReportRunResponse,
    ReportsDashboardResponse,
    ReportsSummaryResponse,
)
from app.modules.reports.utils import IST, resolve_date_range
from app.modules.territories.models import Territory
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

        if not report.is_ready:
            raise HTTPException(
                status_code=400,
                detail=f"Report '{key}' is scheduled for a future release: {report.coming_soon_reason or 'Coming soon'}",
                headers={"X-Error-Code": "REPORT_COMING_SOON"},
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
            landscape=report.landscape,
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

        u_stmt = self.db.query(User).filter(User.is_active == True)  # noqa: E712
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

    # -------------------------------------------------------------------------
    # Catalog v3 Methods
    # -------------------------------------------------------------------------

    def get_catalog_v3(
        self,
        context: ScopeContext,
        search: str | None = None,
        group: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ReportCatalogV3Response:
        """Fetch dynamic catalog list of reports for caller's role."""
        role_str = context.role.value
        all_defs = (
            self.db.query(ReportDefinition)
            .filter(ReportDefinition.is_active == True)
            .order_by(ReportDefinition.sort_order.asc(), ReportDefinition.name.asc())
            .all()
        )

        # Filter by role
        accessible: list[ReportDefinition] = []
        for d in all_defs:
            if context.role == UserRole.ADMIN or role_str in (d.allowed_roles or []):
                accessible.append(d)

        # Get all distinct groups for caller
        groups = sorted({d.group for d in accessible})

        # Apply group filter
        if group and group != "ALL":
            accessible = [d for d in accessible if d.group.lower() == group.lower()]

        # Apply status filter
        if status and status != "ALL":
            accessible = [d for d in accessible if d.status.lower() == status.lower()]

        # Apply search filter
        if search and search.strip():
            s = search.strip().lower()
            accessible = [
                d for d in accessible
                if s in d.name.lower() or s in d.group.lower() or s in d.key.lower()
            ]

        total = len(accessible)
        p = max(1, page)
        ps = max(1, min(100, page_size))
        start_idx = (p - 1) * ps
        end_idx = start_idx + ps
        paged_defs = accessible[start_idx:end_idx]

        items = [
            ReportDefinitionItem(
                key=d.key,
                name=d.name,
                group=d.group,
                description=d.description,
                sort_order=d.sort_order,
                status=d.status,
                unavailable_reason=d.unavailable_reason,
                formats=d.formats or [],
                filter_schema=d.filter_schema or {},
                allowed_roles=d.allowed_roles or [],
                data_as_of_source=d.data_as_of_source,
                is_active=d.is_active,
            )
            for d in paged_defs
        ]

        return ReportCatalogV3Response(
            items=items,
            total=total,
            page=p,
            page_size=ps,
            groups=groups,
        )

    def get_definition_v3(self, key: str, context: ScopeContext) -> ReportDefinitionItem:
        """Fetch report definition metadata by key."""
        d = (
            self.db.query(ReportDefinition)
            .filter(ReportDefinition.key == key, ReportDefinition.is_active == True)
            .first()
        )
        if not d:
            raise HTTPException(
                status_code=404,
                detail=f"Report '{key}' not found",
                headers={"X-Error-Code": "REPORT_NOT_FOUND"},
            )

        role_str = context.role.value
        if context.role != UserRole.ADMIN and role_str not in (d.allowed_roles or []):
            raise HTTPException(
                status_code=403,
                detail=f"Access denied to report '{key}'",
                headers={"X-Error-Code": "REPORT_SCOPE_DENIED"},
            )

        return ReportDefinitionItem(
            key=d.key,
            name=d.name,
            group=d.group,
            description=d.description,
            sort_order=d.sort_order,
            status=d.status,
            unavailable_reason=d.unavailable_reason,
            formats=d.formats or [],
            filter_schema=d.filter_schema or {},
            allowed_roles=d.allowed_roles or [],
            data_as_of_source=d.data_as_of_source,
            is_active=d.is_active,
        )

    def get_options(
        self,
        source: str,
        context: ScopeContext,
        q: str | None = None,
        parent_id: Any | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> ReportOptionsResponse:
        """Provide dynamic options for schema-driven filters."""
        s = source.lower().strip()
        options: list[ReportOptionItem] = []

        if s == "employees":
            if context.role == UserRole.MR:
                u = self.db.query(User).filter(User.id == context.user_id).first()
                if u:
                    options.append(ReportOptionItem(value=u.id, label=f"{u.full_name} ({u.employee_code})"))
            elif context.role == UserRole.MANAGER:
                u_ids = [context.user_id, *context.team_member_ids]
                users = self.db.query(User).filter(User.id.in_(u_ids), User.is_active == True).all()
                for u in users:
                    options.append(ReportOptionItem(value=u.id, label=f"{u.full_name} ({u.employee_code})"))
            else:
                users_q = self.db.query(User).filter(User.is_active == True)
                if q:
                    users_q = users_q.filter(User.full_name.ilike(f"%{q}%") | User.employee_code.ilike(f"%{q}%"))
                for u in users_q.limit(page_size).all():
                    options.append(ReportOptionItem(value=u.id, label=f"{u.full_name} ({u.employee_code})"))

        elif s == "divisions":
            divs = self.db.query(MasterItem).filter(MasterItem.type == "DIVISION", MasterItem.is_active == True).all()
            for d in divs:
                options.append(ReportOptionItem(value=d.code, label=d.name))

        elif s == "designations":
            desigs = self.db.query(MasterItem).filter(MasterItem.type == "DESIGNATION", MasterItem.is_active == True).all()
            for d in desigs:
                options.append(ReportOptionItem(value=d.code, label=d.name))

        elif s == "states":
            states = self.db.query(State).filter(State.is_active == True).order_by(State.name.asc()).all()
            for st in states:
                options.append(ReportOptionItem(value=st.id, label=st.name))

        elif s == "cities":
            cq = self.db.query(City).filter(City.is_active == True)
            if parent_id:
                cq = cq.filter(City.state_id == parent_id)
            if q:
                cq = cq.filter(City.name.ilike(f"%{q}%"))
            for c in cq.order_by(City.name.asc()).limit(page_size).all():
                options.append(ReportOptionItem(value=c.id, label=c.name, parent_id=c.state_id))

        elif s == "areas":
            aq = self.db.query(Area).filter(Area.is_active == True)
            if parent_id:
                aq = aq.filter(Area.city_id == parent_id)
            if q:
                aq = aq.filter(Area.name.ilike(f"%{q}%"))
            for a in aq.order_by(Area.name.asc()).limit(page_size).all():
                options.append(ReportOptionItem(value=a.id, label=a.name, parent_id=a.city_id))

        elif s == "territories":
            t_q = self.db.query(Territory).filter(Territory.is_active == True)
            if q:
                t_q = t_q.filter(Territory.name.ilike(f"%{q}%") | Territory.code.ilike(f"%{q}%"))
            for t in t_q.order_by(Territory.name.asc()).limit(page_size).all():
                options.append(ReportOptionItem(value=t.id, label=f"{t.name} ({t.code})"))

        elif s == "specialities":
            specs = self.db.query(MasterItem).filter(MasterItem.type == "SPECIALITY", MasterItem.is_active == True).all()
            for sp in specs:
                options.append(ReportOptionItem(value=sp.name, label=sp.name))

        elif s == "product_types":
            cats = self.db.query(MasterItem).filter(MasterItem.type == "CATEGORY", MasterItem.is_active == True).all()
            for c in cats:
                options.append(ReportOptionItem(value=c.code, label=c.name))

        elif s == "products":
            pq = self.db.query(Product).filter(Product.is_active == True)
            if q:
                pq = pq.filter(Product.name.ilike(f"%{q}%") | Product.code.ilike(f"%{q}%"))
            for p in pq.order_by(Product.name.asc()).limit(page_size).all():
                options.append(ReportOptionItem(value=p.id, label=f"{p.name} ({p.code})"))

        elif s == "stockists":
            sq = self.db.query(Stockist).filter(Stockist.is_active == True)
            if q:
                sq = sq.filter(Stockist.agency_name.ilike(f"%{q}%") | Stockist.code.ilike(f"%{q}%"))
            for st in sq.order_by(Stockist.agency_name.asc()).limit(page_size).all():
                options.append(ReportOptionItem(value=st.id, label=f"{st.agency_name} ({st.code})"))

        elif s == "chemists":
            cq = self.db.query(Chemist).filter(Chemist.is_active == True)
            if q:
                cq = cq.filter(Chemist.shop_name.ilike(f"%{q}%") | Chemist.code.ilike(f"%{q}%"))
            for ch in cq.order_by(Chemist.shop_name.asc()).limit(page_size).all():
                options.append(ReportOptionItem(value=ch.id, label=f"{ch.shop_name} ({ch.code})"))

        elif s == "financial_years":
            fys = self.db.query(MasterItem).filter(MasterItem.type == "FINANCIAL_YEAR", MasterItem.is_active == True).all()
            for f in fys:
                options.append(ReportOptionItem(value=f.code, label=f.name))

        return ReportOptionsResponse(source=source, options=options, total=len(options))

    def run_report_v3(
        self,
        key: str,
        req: ReportRunRequest,
        context: ScopeContext,
        current_user: User,
    ) -> ReportRunResponse:
        """Run report query using schema-driven filters and return paginated table rows with summary."""
        definition = self.get_definition_v3(key, context)

        if definition.status == "COMING_SOON":
            raise HTTPException(
                status_code=400,
                detail=definition.unavailable_reason or f"Report '{definition.name}' is scheduled for a future release",
                headers={"X-Error-Code": "REPORT_NOT_AVAILABLE"},
            )

        # 1. Validate filters against schema
        sanitized_filters = validate_filter_schema(definition.filter_schema, req.filters)

        # 2. Validate scope
        user_ids, scope_label = validate_report_scope(context, sanitized_filters)

        # 3. Retrieve implementation class from registry
        report_inst = ReportEngineRegistry.get(key)
        if not report_inst:
            raise HTTPException(
                status_code=400,
                detail=f"Report implementation for '{key}' is pending code deployment",
                headers={"X-Error-Code": "REPORT_NOT_AVAILABLE"},
            )

        # Resolve date ranges if present
        date_range = sanitized_filters.get("date_range")
        start_utc, end_utc = None, None
        if isinstance(date_range, dict):
            fd = date_range.get("from")
            td = date_range.get("to")
            start_utc, end_utc, _, _ = resolve_date_range(fd, td)
        elif sanitized_filters.get("from_date") and sanitized_filters.get("to_date"):
            start_utc, end_utc, _, _ = resolve_date_range(sanitized_filters.get("from_date"), sanitized_filters.get("to_date"))

        # 4. Execute query
        items = report_inst.run_query(
            db=self.db,
            filters=sanitized_filters,
            user_ids=user_ids,
            start_utc=start_utc,
            end_utc=end_utc,
        )

        summary = report_inst.calculate_summary(items)
        columns = report_inst.get_columns()

        total = len(items)
        p = max(1, req.page)
        ps = max(1, min(100, req.page_size))
        start_idx = (p - 1) * ps
        end_idx = start_idx + ps
        paged_rows = items[start_idx:end_idx]

        meta = {
            "key": definition.key,
            "name": definition.name,
            "group": definition.group,
            "scope_label": scope_label,
            "generated_at": datetime.now(IST).strftime("%d-%b-%Y %I:%M %p"),
            "data_as_of": definition.data_as_of_source,
            "total_records": total,
            "page": p,
            "page_size": ps,
            "filters": sanitized_filters,
        }

        return ReportRunResponse(
            meta=meta,
            summary=summary,
            columns=columns,
            rows=paged_rows,
            total=total,
            page=p,
            page_size=ps,
        )

    def export_report_v3(
        self,
        key: str,
        req: ReportExportRequest,
        export_format: str,
        context: ScopeContext,
        current_user: User,
    ) -> tuple[bytes, str, str]:
        """Export report as XLSX or PDF with full row limits and audit logging."""
        fmt = export_format.lower().strip()
        if fmt not in ["xlsx", "pdf"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format '{export_format}', expected 'xlsx' or 'pdf'",
                headers={"X-Error-Code": "INVALID_FILTER"},
            )

        run_req = ReportRunRequest(filters=req.filters, page=1, page_size=self.MAX_EXPORT_ROWS)
        run_res = self.run_report_v3(key, run_req, context, current_user)

        # Retrieve full rows
        report_inst = ReportEngineRegistry.get(key)
        if not report_inst:
            raise HTTPException(status_code=400, detail="Report not available")

        # Full dataset
        user_ids, scope_label = validate_report_scope(context, run_res.meta.get("filters", {}))
        items = report_inst.run_query(
            db=self.db,
            filters=run_res.meta.get("filters", {}),
            user_ids=user_ids,
            start_utc=None,
            end_utc=None,
        )

        if len(items) > self.MAX_EXPORT_ROWS:
            raise HTTPException(
                status_code=400,
                detail=f"Export exceeds {self.MAX_EXPORT_ROWS:,} rows. Please filter your request.",
                headers={"X-Error-Code": "EXPORT_TOO_LARGE"},
            )

        # Build ReportMeta object
        meta_obj = ReportMeta(
            key=key,
            report_key=key,
            title=run_res.meta.get("name", key),
            group=run_res.meta.get("group", "Reports"),
            filters=run_res.meta.get("filters", {}),
            scope_label=scope_label,
            user_scope=scope_label,
            generated_at=run_res.meta.get("generated_at", ""),
            columns=run_res.columns,
            total_records=len(items),
            landscape=report_inst.landscape,
        )

        filename = f"{key}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{fmt}"

        if fmt == "pdf":
            pdf_gen = ReportPdfGenerator(
                meta=meta_obj,
                columns=run_res.columns,
                landscape_mode=report_inst.landscape,
            )
            file_bytes = pdf_gen.generate(items, run_res.summary)
            media_type = "application/pdf"
        else:
            excel_gen = ReportExcelGenerator(meta=meta_obj, columns=run_res.columns)
            file_bytes = excel_gen.generate(items, run_res.summary)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        # Log audit entry
        audit = AuditLog(
            user_id=current_user.id,
            action="REPORT_EXPORT",
            entity_type="report",
            entity_id=key,
            details=json.dumps({
                "format": fmt,
                "row_count": len(items),
                "filename": filename,
                "filters": run_res.meta.get("filters", {}),
                "exported_at": datetime.now(UTC).isoformat(),
            }),
        )
        self.db.add(audit)
        self.db.commit()

        return file_bytes, filename, media_type

