"""Target business service."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.scope import ScopeContext, UserRole, get_accessible_user_ids
from app.modules.targets.models import Target
from app.modules.targets.repository import TargetRepository
from app.modules.targets.schemas import TargetCreateOrUpdate, TargetResponse, TargetsListResponse


class TargetService:
    """Business logic for targets."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = TargetRepository(db)

    def get_targets(
        self,
        context: ScopeContext,
        year: int | None = None,
        month: int | None = None,
    ) -> TargetsListResponse:
        """List targets within caller scope for the specified or current month."""
        if context.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            raise HTTPException(
                status_code=403,
                detail="Only ADMIN and MANAGER can view target settings",
            )

        now = datetime.now(ZoneInfo("Asia/Kolkata"))
        target_year = year or now.year
        target_month = month or now.month

        accessible_ids = get_accessible_user_ids(context)
        user_ids = list(accessible_ids) if accessible_ids is not None else None

        records = self.repo.list_targets(
            year=target_year,
            month=target_month,
            user_ids=user_ids,
        )

        items = [
            TargetResponse(
                id=target.id,
                user_id=target.user_id,
                user_name=user_name,
                year=target.year,
                month=target.month,
                visit_target=target.visit_target,
                doctor_call_target=target.doctor_call_target,
                chemist_call_target=target.chemist_call_target,
                primary_sales_target=float(target.primary_sales_target),
                secondary_sales_target=float(target.secondary_sales_target),
            )
            for target, user_name in records
        ]

        return TargetsListResponse(
            year=target_year,
            month=target_month,
            items=items,
        )

    def set_target(
        self,
        context: ScopeContext,
        payload: TargetCreateOrUpdate,
    ) -> TargetResponse:
        """Upsert a monthly target within caller scope."""
        if context.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            raise HTTPException(
                status_code=403,
                detail="Only ADMIN and MANAGER can set targets",
            )

        if context.role == UserRole.MANAGER:
            if payload.user_id not in context.team_member_ids:
                raise HTTPException(
                    status_code=403,
                    detail="Cannot set target for an MR outside your assigned team",
                )

        target = self.repo.upsert_target(
            user_id=payload.user_id,
            year=payload.year,
            month=payload.month,
            visit_target=payload.visit_target,
            doctor_call_target=payload.doctor_call_target,
            chemist_call_target=payload.chemist_call_target,
            primary_sales_target=payload.primary_sales_target,
            secondary_sales_target=payload.secondary_sales_target,
            creator_id=context.user_id,
        )

        return TargetResponse(
            id=target.id,
            user_id=target.user_id,
            year=target.year,
            month=target.month,
            visit_target=target.visit_target,
            doctor_call_target=target.doctor_call_target,
            chemist_call_target=target.chemist_call_target,
            primary_sales_target=float(target.primary_sales_target),
            secondary_sales_target=float(target.secondary_sales_target),
        )

    def get_mr_target_for_month(self, user_id: int, year: int, month: int) -> Target | None:
        return self.repo.get_by_user_and_period(user_id, year, month)
