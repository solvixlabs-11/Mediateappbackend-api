"""Targets REST API router."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.targets.schemas import TargetCreateOrUpdate, TargetResponse, TargetsListResponse
from app.modules.targets.service import TargetService
from app.modules.users.models import User
from app.modules.users.service import UserService

router = APIRouter(prefix="/targets", tags=["Targets"])


@router.get(
    "",
    response_model=TargetsListResponse,
    summary="Get monthly targets (ADMIN and MANAGER)",
)
def get_targets(
    year: int | None = Query(None, description="Year (defaults to current year)"),
    month: int | None = Query(None, description="Month (defaults to current month)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TargetsListResponse:
    """Fetch monthly targets scoped to caller's team."""
    scope = UserService(db).get_user_scope_context(current_user)
    service = TargetService(db)
    return service.get_targets(context=scope, year=year, month=month)


@router.put(
    "",
    response_model=TargetResponse,
    summary="Set or update an MR's monthly target (ADMIN and MANAGER)",
)
def set_target(
    payload: TargetCreateOrUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TargetResponse:
    """Upsert monthly target for an MR."""
    scope = UserService(db).get_user_scope_context(current_user)
    service = TargetService(db)
    return service.set_target(context=scope, payload=payload)
