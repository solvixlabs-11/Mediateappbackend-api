
"""Reports & Analytics REST API router conforming to Reports Catalog v3."""

from __future__ import annotations

import io
from datetime import date
from urllib.parse import quote

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.reports.schemas import (
    ReportCatalogV3Response,
    ReportDefinitionItem,
    ReportExportRequest,
    ReportOptionsResponse,
    ReportRunRequest,
    ReportRunResponse,
    ReportsDashboardResponse,
)
from app.modules.reports.service import ReportService
from app.modules.users.models import User
from app.modules.users.service import UserService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get(
    "",
    response_model=ReportCatalogV3Response,
    summary="Get reports catalog available for caller's role (Catalog v3)",
)
def get_reports_catalog(
    search: str | None = Query(None, description="Search by report name or key"),
    group: str | None = Query(None, description="Filter by report group"),
    status: str | None = Query(None, description="Filter by status (AVAILABLE, COMING_SOON)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReportCatalogV3Response:
    """Return reports catalog with search, group, status, and role-based filtering."""
    scope = UserService(db).get_user_scope_context(current_user)
    service = ReportService(db)
    return service.get_catalog_v3(
        context=scope,
        search=search,
        group=group,
        status=status,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/options/{source}",
    response_model=ReportOptionsResponse,
    summary="Get options for schema-driven dynamic filter fields",
)
def get_report_options(
    source: str,
    q: str | None = Query(None, description="Search term for options"),
    parent_id: str | None = Query(None, description="Parent ID for dependent dropdowns"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=500, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReportOptionsResponse:
    """Fetch scoped and searchable options for report filters (e.g. employees, territories)."""
    scope = UserService(db).get_user_scope_context(current_user)
    service = ReportService(db)
    return service.get_options(
        source=source,
        context=scope,
        q=q,
        parent_id=parent_id,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/dashboard",
    response_model=ReportsDashboardResponse,
    summary="Get aggregate field performance and coverage dashboard KPIs",
)
def get_reports_dashboard(
    start_date: date | None = Query(None, description="Start date for reporting window"),
    end_date: date | None = Query(None, description="End date for reporting window"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReportsDashboardResponse:
    """Compute and return operational field KPIs, leaderboard, and customer coverage."""
    scope = UserService(db).get_user_scope_context(current_user)
    service = ReportService(db)
    return service.get_dashboard_reports(
        context=scope,
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/{key}",
    response_model=ReportDefinitionItem,
    summary="Get report definition metadata, schema, and status",
)
def get_report_definition(
    key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReportDefinitionItem:
    """Retrieve report definition metadata and schema by key."""
    scope = UserService(db).get_user_scope_context(current_user)
    service = ReportService(db)
    return service.get_definition_v3(key=key, context=scope)


@router.post(
    "/{key}/run",
    response_model=ReportRunResponse,
    summary="Execute report view on screen with schema-driven filters",
)
def run_report(
    key: str,
    body: ReportRunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReportRunResponse:
    """Run dynamic report query with server-enforced scoping and return paged results."""
    scope = UserService(db).get_user_scope_context(current_user)
    service = ReportService(db)
    return service.run_report_v3(
        key=key,
        req=body,
        context=scope,
        current_user=current_user,
    )


@router.post(
    "/{key}/export",
    summary="Export report file as PDF or Excel (XLSX) using POST",
    responses={
        200: {
            "content": {
                "application/pdf": {},
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {},
            },
            "description": "Streamed report file download",
        }
    },
)
def export_report_post(
    key: str,
    body: ReportExportRequest,
    format: str = Query("xlsx", description="Export format: 'xlsx' or 'pdf'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Stream report as PDF or Excel workbook with audit log tracking."""
    scope = UserService(db).get_user_scope_context(current_user)
    service = ReportService(db)
    file_bytes, filename, media_type = service.export_report_v3(
        key=key,
        req=body,
        export_format=format,
        context=scope,
        current_user=current_user,
    )

    encoded_filename = quote(filename)
    headers = {
        "Content-Disposition": f"attachment; filename=\"{filename}\"; filename*=UTF-8''{encoded_filename}",
        "Access-Control-Expose-Headers": "Content-Disposition",
    }

    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type=media_type,
        headers=headers,
    )


@router.get(
    "/{key}/export",
    summary="Export report file as PDF or Excel (XLSX) using GET (backward compatibility)",
)
def export_report_get(
    request: Request,
    key: str,
    format: str = Query("xlsx", description="Export format: 'xlsx' or 'pdf'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Stream report as PDF or Excel workbook using GET query params."""
    filters = dict(request.query_params)
    filters.pop("format", None)
    if "month" not in filters:
        filters["month"] = date.today().month
    if "year" not in filters:
        filters["year"] = date.today().year
    body = ReportExportRequest(filters=filters)
    return export_report_post(key=key, body=body, format=format, db=db, current_user=current_user)
