"""Dashboard REST API endpoints for Admin Live Field Activity and role dashboards."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.dashboard.schemas import (
    AdminLiveActivityResponse,
    ManagerDashboardResponse,
    MrDashboardResponse,
)
from app.modules.dashboard.service import DashboardService
from app.modules.users.models import User

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


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
