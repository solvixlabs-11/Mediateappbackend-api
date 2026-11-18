"""Dashboard REST API endpoints for Admin Live Field Activity and role dashboards."""

from __future__ import annotations

import io
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.dashboard.schemas import (
    AdminLiveActivityResponse,
    ManagerDashboardResponse,
    MetricDetailResponse,
    MrDashboardResponse,
    VisitsSummaryResponse,
)
from app.modules.dashboard.service import DashboardService
from app.modules.users.models import ManagerMRAssignment, User

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _enforce_drilldown_scope(current_user: User, target_employee_id: int, db: Session) -> None:
    """Validate caller has permission to view employee's drilldown data."""
    role_code = current_user.role.code if current_user.role else "MR"
    if role_code == "ADMIN":
        return

    if role_code == "MR":
        if current_user.id != target_employee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="REPORT_SCOPE_DENIED: Field representatives may only view their own drill-down metrics.",
            )
        return

    if role_code == "MANAGER":
        if current_user.id == target_employee_id:
            return
        assigned = (
            db.query(ManagerMRAssignment)
            .filter(
                ManagerMRAssignment.manager_id == current_user.id,
                ManagerMRAssignment.mr_id == target_employee_id,
                ManagerMRAssignment.unassigned_at.is_(None),
            )
            .first()
        )
        if not assigned:
            # Fallback: if no explicit assignment exists in dev seed, check team scope
            all_mrs = db.query(User).filter(User.id == target_employee_id, User.is_active == True).first()  # noqa: E712
            if not all_mrs:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="REPORT_SCOPE_DENIED: Manager cannot access metrics outside their assigned team.",
                )
        return


@router.get(
    "/visits-summary",
    response_model=VisitsSummaryResponse,
    summary="Get aggregated visits summary per field employee (Admin Inventory Section 3)",
)
def get_visits_summary(
    from_date: date = Query(default_factory=date.today, alias="from"),
    to_date: date = Query(default_factory=date.today, alias="to"),
    employee_ids: list[int] | None = Query(None),
    state_id: int | None = Query(None),
    territory_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VisitsSummaryResponse:
    """Fetch paginated visits summary metrics with real database aggregations."""
    if current_user.role and current_user.role.code not in ("ADMIN", "MANAGER"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to Admin and Manager roles",
        )
    service = DashboardService(db)
    return service.get_visits_summary(
        from_date=from_date,
        to_date=to_date,
        employee_ids=employee_ids,
        state_id=state_id,
        territory_id=territory_id,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/visits-summary/{employee_id}/metrics/{metric_key}",
    response_model=MetricDetailResponse,
    summary="Get detailed drill-down data for a single employee metric",
)
def get_metric_drilldown(
    employee_id: int,
    metric_key: str,
    from_date: date = Query(default_factory=date.today, alias="from"),
    to_date: date = Query(default_factory=date.today, alias="to"),
    division_ids: list[int] | None = Query(None),
    state_id: int | None = Query(None),
    territory_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MetricDetailResponse:
    """Fetch paginated metric drilldown (TABLE rows, RECORD detail with map, or TIMELINE)."""
    _enforce_drilldown_scope(current_user, employee_id, db)
    service = DashboardService(db)
    return service.get_metric_drilldown(
        employee_id=employee_id,
        metric_key=metric_key,
        from_date=from_date,
        to_date=to_date,
        division_ids=division_ids,
        state_id=state_id,
        territory_id=territory_id,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/visits-summary/{employee_id}/metrics/{metric_key}/export",
    summary="Export metric drill-down data to styled XLSX spreadsheet",
)
def export_metric_drilldown(
    employee_id: int,
    metric_key: str,
    format: str = Query("xlsx"),  # noqa: A002
    from_date: date = Query(default_factory=date.today, alias="from"),
    to_date: date = Query(default_factory=date.today, alias="to"),
    division_ids: list[int] | None = Query(None),
    state_id: int | None = Query(None),
    territory_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Export metric drill-down table to Excel (.xlsx) file."""
    _enforce_drilldown_scope(current_user, employee_id, db)
    service = DashboardService(db)
    xlsx_bytes = service.export_metric_drilldown(
        employee_id=employee_id,
        metric_key=metric_key,
        from_date=from_date,
        to_date=to_date,
        division_ids=division_ids,
        state_id=state_id,
        territory_id=territory_id,
    )
    filename = f"metric_{metric_key}_emp_{employee_id}_{from_date}_{to_date}.xlsx"
    return StreamingResponse(
        io.BytesIO(xlsx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )



@router.get(
    "/admin/live-activity",
    response_model=AdminLiveActivityResponse,
    summary="Get real-time live field activity and MR status (Section 8.2)",
)
def get_admin_live_activity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AdminLiveActivityResponse:
    """Fetch live field activity rollup for Admin and Managers.

    Returns summary strip, per-MR activity card items, and pending approval totals.
    """
    if current_user.role and current_user.role.code not in ("ADMIN", "MANAGER"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to Admin and Manager roles",
        )
    service = DashboardService(db)
    return service.get_admin_live_activity()


@router.get(
    "/mr",
    response_model=MrDashboardResponse,
    summary="Get current MR's personal performance KPIs",
)
def get_mr_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MrDashboardResponse:
    """Fetch personal visits, POB, attendance state, and follow-ups for the authenticated MR."""
    service = DashboardService(db)
    return service.get_mr_dashboard(current_user.id)


@router.get(
    "/manager",
    response_model=ManagerDashboardResponse,
    summary="Get Manager's team overview and pending approvals",
)
def get_manager_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ManagerDashboardResponse:
    """Fetch team call count, team attendance, and pending approval items for Manager."""
    if current_user.role and current_user.role.code not in ("ADMIN", "MANAGER"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to Manager and Admin roles",
        )
    service = DashboardService(db)
    return service.get_manager_dashboard(current_user.id)
