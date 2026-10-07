"""Reports & Analytics REST API router."""

from __future__ import annotations

import io
from datetime import date
from urllib.parse import quote

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.reports.schemas import (
    ReportCatalogResponse,
    ReportFilterParams,
    ReportResponse,
    ReportsDashboardResponse,
)
from app.modules.reports.service import ReportService
from app.modules.users.models import User
from app.modules.users.service import UserService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get(
    "",
    response_model=ReportCatalogResponse,
    summary="Get reports catalog available for caller's role",
)
def get_reports_catalog(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReportCatalogResponse:
    """Return reports catalog with titles, groups, filter schemas, and scope info."""
    scope = UserService(db).get_user_scope_context(current_user)
    service = ReportService(db)
    return service.get_catalog(context=scope)


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
    response_model=ReportResponse,
    summary="Get paged JSON report with summary and metadata",
)
def get_report(
    key: str,
    from_date: str | None = Query(None, description="Start date in YYYY-MM-DD (Asia/Kolkata)"),
    to_date: str | None = Query(None, description="End date in YYYY-MM-DD (Asia/Kolkata)"),
    start_date: str | None = Query(None, description="Alias for from_date"),
    end_date: str | None = Query(None, description="Alias for to_date"),
    mr_id: int | None = Query(None, description="Filter by Medical Representative user ID"),
    manager_id: int | None = Query(None, description="Filter by Reporting Manager user ID"),
    territory_id: int | None = Query(None, description="Filter by territory ID"),
    customer_type: str | None = Query(
        None, description="Filter by customer type (DOCTOR, CHEMIST, etc.)"
    ),
    status: str | None = Query(None, description="Filter by status (e.g. Verified, Approved)"),
    specialization: str | None = Query(None, description="Filter by specialization"),
    category: str | None = Query(None, description="Filter by category"),
    active: bool | None = Query(None, description="Filter by active status"),
    work_type: str | None = Query(None, description="Filter by work type"),
    visit_type: str | None = Query(None, description="Filter by visit type"),
    verified: bool | None = Query(None, description="Filter by geofence verified"),
    deviation_type: str | None = Query(None, description="Filter by deviation type"),
    days_not_seen: int | None = Query(None, description="Filter by days not seen threshold"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReportResponse:
    """Execute dynamic report query with server-enforced scoping and return paged results."""
    scope = UserService(db).get_user_scope_context(current_user)
    filters = ReportFilterParams(
        from_date=from_date or start_date,
        to_date=to_date or end_date,
        mr_id=mr_id,
        manager_id=manager_id,
        territory_id=territory_id,
        customer_type=customer_type,
        status=status,
        specialization=specialization,
        category=category,
        active=active,
        work_type=work_type,
        visit_type=visit_type,
        verified=verified,
        deviation_type=deviation_type,
        days_not_seen=days_not_seen,
        page=page,
        page_size=page_size,
    )
    service = ReportService(db)
    return service.get_report_json(
        key=key,
        filters=filters,
        context=scope,
        current_user_name=current_user.full_name,
    )


@router.get(
    "/{key}/export",
    summary="Export report file as PDF or Excel (XLSX)",
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
def export_report(
    key: str,
    format: str = Query("xlsx", description="Export format: 'xlsx' or 'pdf'"),
    from_date: str | None = Query(None, description="Start date in YYYY-MM-DD (Asia/Kolkata)"),
    to_date: str | None = Query(None, description="End date in YYYY-MM-DD (Asia/Kolkata)"),
    start_date: str | None = Query(None, description="Alias for from_date"),
    end_date: str | None = Query(None, description="Alias for to_date"),
    mr_id: int | None = Query(None, description="Filter by Medical Representative user ID"),
    manager_id: int | None = Query(None, description="Filter by Reporting Manager user ID"),
    territory_id: int | None = Query(None, description="Filter by territory ID"),
    customer_type: str | None = Query(None, description="Filter by customer type"),
    status: str | None = Query(None, description="Filter by status"),
    specialization: str | None = Query(None, description="Filter by specialization"),
    category: str | None = Query(None, description="Filter by category"),
    active: bool | None = Query(None, description="Filter by active status"),
    work_type: str | None = Query(None, description="Filter by work type"),
    visit_type: str | None = Query(None, description="Filter by visit type"),
    verified: bool | None = Query(None, description="Filter by geofence verified"),
    deviation_type: str | None = Query(None, description="Filter by deviation type"),
    days_not_seen: int | None = Query(None, description="Filter by days not seen threshold"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Stream report as PDF or Excel workbook with audit log tracking."""
    scope = UserService(db).get_user_scope_context(current_user)
    filters = ReportFilterParams(
        from_date=from_date or start_date,
        to_date=to_date or end_date,
        mr_id=mr_id,
        manager_id=manager_id,
        territory_id=territory_id,
        customer_type=customer_type,
        status=status,
        specialization=specialization,
        category=category,
        active=active,
        work_type=work_type,
        visit_type=visit_type,
        verified=verified,
        deviation_type=deviation_type,
        days_not_seen=days_not_seen,
    )
    service = ReportService(db)
    file_bytes, filename, media_type = service.export_report_file(
        key=key,
        export_format=format,
        filters=filters,
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
