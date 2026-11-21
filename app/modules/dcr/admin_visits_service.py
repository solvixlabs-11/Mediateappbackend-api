"""Service for Admin Visits management: Delete My Visits, side-effect rollbacks, and restores."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload

from app.db.mixins import utc_now
from app.modules.audit.service import AuditService
from app.modules.dcr.admin_visits_schemas import (
    DeleteVisitsExecuteRequest,
    DeleteVisitsExecuteResponse,
    DeleteVisitsPreviewRequest,
    DeleteVisitsPreviewResponse,
    RestoreVisitsRequest,
    RestoreVisitsResponse,
    VisitSampleItem,
)
from app.modules.dcr.models import DcrVisit, FollowUp, PlannedVisit
from app.modules.users.models import User

# In-memory TTL cache for preview tokens: {token: {"filters": dict, "expires_at": datetime, "count": int}}
PREVIEW_TOKENS_CACHE: dict[str, dict[str, Any]] = {}
MAX_DELETION_LIMIT = 5000


class AdminVisitsService:
    """Orchestrates bulk soft-deletion and safe restoration of field visits."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def _build_preview_query(self, filters: DeleteVisitsPreviewRequest):
        query = (
            self.db.query(DcrVisit)
            .filter(DcrVisit.deleted_at.is_(None))
            .join(DcrVisit.user)
            .options(
                joinedload(DcrVisit.user),
                joinedload(DcrVisit.doctor),
                joinedload(DcrVisit.chemist),
                joinedload(DcrVisit.stockist),
            )
        )

        if filters.employee_ids:
            query = query.filter(DcrVisit.user_id.in_(filters.employee_ids))

        if filters.start_date:
            query = query.filter(DcrVisit.dcr_date >= filters.start_date)

        if filters.end_date:
            query = query.filter(DcrVisit.dcr_date <= filters.end_date)

        if filters.customer_type and filters.customer_type.upper() != "ALL":
            query = query.filter(DcrVisit.customer_type == filters.customer_type.upper())

        if filters.visit_type:
            query = query.filter(DcrVisit.visit_type == filters.visit_type)

        return query

    def get_delete_preview(
        self,
        filters: DeleteVisitsPreviewRequest,
        admin_user: User,
    ) -> DeleteVisitsPreviewResponse:
        """Calculate matching visits, generate secure preview token, and return sample."""
        query = self._build_preview_query(filters)
        total_count = query.count()

        sample_rows = query.order_by(desc(DcrVisit.dcr_date), desc(DcrVisit.id)).limit(10).all()

        sample_items: list[VisitSampleItem] = []
        for v in sample_rows:
            cust_name = None
            if v.doctor:
                cust_name = f"Dr. {v.doctor.name}"
            elif v.chemist:
                cust_name = v.chemist.name
            elif v.stockist:
                cust_name = v.stockist.name

            sample_items.append(
                VisitSampleItem(
                    id=v.id,
                    dcr_date=v.dcr_date,
                    customer_type=v.customer_type,
                    customer_name=cust_name,
                    employee_id=v.user_id,
                    employee_name=v.user.full_name if v.user else None,
                    city=str(getattr(v.doctor, "city_id", "")) if v.doctor else None,
                    pob_amount=float(v.pob_amount or 0.0),
                )
            )

        token = f"PV-{uuid.uuid4().hex[:12].upper()}"
        expires_at = datetime.now(UTC) + timedelta(minutes=15)

        PREVIEW_TOKENS_CACHE[token] = {
            "filters": filters.model_dump(),
            "count": total_count,
            "expires_at": expires_at,
            "admin_id": admin_user.id,
        }

        return DeleteVisitsPreviewResponse(
            total_matching_visits=total_count,
            preview_token=token,
            expires_at=expires_at,
            max_limit_allowed=MAX_DELETION_LIMIT,
            sample_visits=sample_items,
        )

    def execute_delete(
        self,
        payload: DeleteVisitsExecuteRequest,
        admin_user: User,
    ) -> DeleteVisitsExecuteResponse:
        """Execute soft delete in ONE atomic transaction with side-effect reversals (BR-11)."""
        cached = PREVIEW_TOKENS_CACHE.get(payload.preview_token)
        now = datetime.now(UTC)

        if not cached or cached.get("expires_at") < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deletion preview token has expired or is invalid. Please request a new preview.",
            )

        filters = DeleteVisitsPreviewRequest(**cached["filters"])
        query = self._build_preview_query(filters)
        visits = query.limit(MAX_DELETION_LIMIT).all()

        if not visits:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active visits matched the deletion criteria.",
            )

        planned_reverted = 0
        follow_ups_cancelled = 0
        deletion_token = payload.preview_token

        for v in visits:
            v.deleted_at = now
            v.deleted_by_id = admin_user.id
            v.deletion_reason = payload.reason
            v.deletion_token = deletion_token

            # Side effect 1: Revert associated PlannedVisit back to PLANNED
            if v.planned_visit_id:
                planned = (
                    self.db.query(PlannedVisit)
                    .filter(PlannedVisit.id == v.planned_visit_id)
                    .first()
                )
                if planned and planned.status == "COMPLETED":
                    planned.status = "PLANNED"
                    planned_reverted += 1

            # Side effect 2: Cancel Follow-ups generated by this visit
            follow_ups = (
                self.db.query(FollowUp)
                .filter(FollowUp.dcr_visit_id == v.id, FollowUp.status != "CANCELLED")
                .all()
            )
            for f in follow_ups:
                f.status = "CANCELLED"
                follow_ups_cancelled += 1

        # Audit logging (mandatory for admin destructive operations)
        AuditService.record(
            self.db,
            user_id=admin_user.id,
            module="dcr",
            action="DELETE_MY_VISITS",
            entity_type="dcr_visit",
            entity_id=None,
            summary=f"Admin soft-deleted {len(visits)} field visits batch #{deletion_token}. Reason: {payload.reason}",
            after={
                "deleted_count": len(visits),
                "planned_reverted": planned_reverted,
                "follow_ups_cancelled": follow_ups_cancelled,
                "reason": payload.reason,
                "deletion_token": deletion_token,
            },
        )

        self.db.commit()

        # Remove used token
        PREVIEW_TOKENS_CACHE.pop(payload.preview_token, None)

        return DeleteVisitsExecuteResponse(
            deleted_count=len(visits),
            planned_visits_reverted=planned_reverted,
            follow_ups_cancelled=follow_ups_cancelled,
            deletion_token=deletion_token,
            message=f"Successfully soft-deleted {len(visits)} visits. All linked planned visits and follow-ups safely rolled back.",
        )

    def restore_visits(
        self,
        payload: RestoreVisitsRequest,
        admin_user: User,
    ) -> RestoreVisitsResponse:
        """Restore soft-deleted visits within the allowed retention window."""
        query = self.db.query(DcrVisit).filter(DcrVisit.deleted_at.isnot(None))

        if payload.deletion_token:
            query = query.filter(DcrVisit.deletion_token == payload.deletion_token)
        elif payload.visit_ids:
            query = query.filter(DcrVisit.id.in_(payload.visit_ids))
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Either deletion_token or visit_ids must be provided to restore visits.",
            )

        visits = query.all()
        if not visits:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No soft-deleted visits found matching the criteria.",
            )

        # Check retention window (e.g., 30 days)
        now = datetime.now(UTC)
        restore_window_days = 30
        planned_restored = 0
        follow_ups_restored = 0

        for v in visits:
            if v.deleted_at:
                # Naive or tz-aware safety
                del_time = v.deleted_at.replace(tzinfo=UTC) if v.deleted_at.tzinfo is None else v.deleted_at
                if (now - del_time).days > restore_window_days:
                    continue

            v.deleted_at = None
            v.deleted_by_id = None
            v.deletion_reason = None
            v.deletion_token = None

            # Restore PlannedVisit status
            if v.planned_visit_id:
                planned = (
                    self.db.query(PlannedVisit)
                    .filter(PlannedVisit.id == v.planned_visit_id)
                    .first()
                )
                if planned and planned.status == "PLANNED":
                    planned.status = "COMPLETED"
                    planned_restored += 1

            # Restore Follow-ups status
            follow_ups = (
                self.db.query(FollowUp)
                .filter(FollowUp.dcr_visit_id == v.id, FollowUp.status == "CANCELLED")
                .all()
            )
            for f in follow_ups:
                f.status = "PENDING"
                follow_ups_restored += 1

        AuditService.record(
            self.db,
            user_id=admin_user.id,
            module="dcr",
            action="RESTORE_MY_VISITS",
            entity_type="dcr_visit",
            entity_id=None,
            summary=f"Admin restored {len(visits)} field visits. Reason: {payload.reason or 'User requested restore'}",
            after={
                "restored_count": len(visits),
                "planned_restored": planned_restored,
                "follow_ups_restored": follow_ups_restored,
            },
        )

        self.db.commit()

        return RestoreVisitsResponse(
            restored_count=len(visits),
            planned_visits_restored=planned_restored,
            follow_ups_restored=follow_ups_restored,
            message=f"Successfully restored {len(visits)} visits.",
        )
