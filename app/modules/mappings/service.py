"""Employee Territory & Customer Mapping Wizard business logic service."""

from __future__ import annotations

import datetime as dt
import json
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.modules.audit.service import AuditService
from app.modules.customers.models import Chemist, Doctor, Hospital, Stockist
from app.modules.mappings.models import MappingBatch, MappingBatchItem
from app.modules.mappings.schemas import (
    MappingBatchDetailResponse,
    MappingBatchItemResponse,
    MappingBatchResponse,
    MappingCapabilitiesResponse,
    MappingConflictItem,
    MappingPreviewRequest,
    MappingPreviewResponse,
)
from app.modules.territories.models import Territory, UserTerritoryAssignment
from app.modules.users.models import User

MAX_BATCH_ITEMS = 20000


class MappingService:
    """Service handling dry-run previews, bulk assignments, and transactional reverts."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_capabilities(self) -> MappingCapabilitiesResponse:
        """Return wizard capabilities, supported modes, and beat readiness."""
        return MappingCapabilitiesResponse()

    def preview(self, payload: MappingPreviewRequest, current_user: User) -> MappingPreviewResponse:
        """Perform a dry-run preview of candidate assignments and identify conflicts."""
        # 1. Target employee check
        target_user = self.db.scalar(select(User).where(User.id == payload.target_employee_id))
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target employee with ID {payload.target_employee_id} not found.",
            )

        conflicts: list[MappingConflictItem] = []
        sample_preview: list[dict[str, Any]] = []
        new_count = 0
        total_count = 0

        if payload.mode == "TERRITORY":
            query = select(Territory).where(Territory.is_active == True)  # noqa: E712
            if payload.territory_ids:
                query = query.where(Territory.id.in_(payload.territory_ids))
            elif payload.filter_state_id:
                query = query.where(Territory.state_id == payload.filter_state_id)

            candidates = self.db.scalars(query.limit(MAX_BATCH_ITEMS + 1)).all()
            if len(candidates) > MAX_BATCH_ITEMS:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Batch size exceeds maximum limit of {MAX_BATCH_ITEMS} items.",
                )

            total_count = len(candidates)

            # Check existing active assignments
            t_ids = [t.id for t in candidates]
            active_assignments = self.db.scalars(
                select(UserTerritoryAssignment).where(
                    UserTerritoryAssignment.territory_id.in_(t_ids),
                    UserTerritoryAssignment.unassigned_at.is_(None),
                )
            ).all()

            assigned_map: dict[int, UserTerritoryAssignment] = {
                a.territory_id: a for a in active_assignments
            }

            for t in candidates:
                curr_assign = assigned_map.get(t.id)
                if curr_assign and curr_assign.user_id != payload.target_employee_id:
                    curr_user_name = curr_assign.user.full_name if curr_assign.user else f"User #{curr_assign.user_id}"
                    conflicts.append(
                        MappingConflictItem(
                            entity_type="TERRITORY",
                            entity_id=t.id,
                            entity_name=t.name,
                            current_employee_id=curr_assign.user_id,
                            current_employee_name=curr_user_name,
                            resolution=payload.conflict_policy,
                        )
                    )
                else:
                    new_count += 1

                if len(sample_preview) < 10:
                    sample_preview.append({
                        "id": t.id,
                        "code": t.code,
                        "name": t.name,
                        "hq": t.headquarters,
                        "has_conflict": bool(curr_assign and curr_assign.user_id != payload.target_employee_id),
                    })

        elif payload.mode == "CUSTOMER":
            c_type = (payload.customer_type or "DOCTOR").upper()
            model_cls: Any = Doctor
            name_attr = "full_name"
            if c_type == "CHEMIST":
                model_cls = Chemist
                name_attr = "shop_name"
            elif c_type == "STOCKIST":
                model_cls = Stockist
                name_attr = "agency_name"
            elif c_type == "HOSPITAL":
                model_cls = Hospital
                name_attr = "name"

            c_query = select(model_cls).where(model_cls.is_active.is_(True))
            if payload.customer_ids:
                c_query = c_query.where(model_cls.id.in_(payload.customer_ids))
            elif payload.territory_ids:
                c_query = c_query.where(model_cls.territory_id.in_(payload.territory_ids))

            customers = self.db.scalars(c_query.limit(MAX_BATCH_ITEMS + 1)).all()
            if len(customers) > MAX_BATCH_ITEMS:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Batch size exceeds maximum limit of {MAX_BATCH_ITEMS} items.",
                )

            total_count = len(customers)
            new_count = total_count  # customer assignments without conflict initially

            for c in customers[:10]:
                sample_preview.append({
                    "id": c.id,
                    "code": c.code,
                    "name": getattr(c, name_attr, ""),
                    "customer_type": c_type,
                    "territory_id": c.territory_id,
                })

        counts = {
            "total_candidates": total_count,
            "new_assignments": new_count,
            "conflicts": len(conflicts),
        }

        # Create DRAFT batch
        batch = MappingBatch(
            mode=payload.mode,
            status="DRAFT",
            filters_json=json.dumps(payload.model_dump()),
            target_employee_id=payload.target_employee_id,
            conflict_policy=payload.conflict_policy,
            counts_json=json.dumps(counts),
        )
        self.db.add(batch)
        self.db.commit()
        self.db.refresh(batch)

        return MappingPreviewResponse(
            batch_id=batch.id,
            mode=batch.mode,
            target_employee_id=batch.target_employee_id,
            target_employee_name=target_user.full_name,
            total_candidate_items=total_count,
            new_assignments_count=new_count,
            conflicts_count=len(conflicts),
            conflicts_sample=conflicts[:50],
            sample_preview=sample_preview,
        )

    def apply(self, batch_id: int, current_user: User) -> MappingBatchResponse:
        """Apply a DRAFT mapping batch in a single atomic database transaction."""
        batch = self.db.scalar(select(MappingBatch).where(MappingBatch.id == batch_id))
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mapping batch with ID {batch_id} not found.",
            )
        if batch.status != "DRAFT":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot apply batch with status '{batch.status}'. Only DRAFT batches can be applied.",
            )

        payload_dict = json.loads(batch.filters_json or "{}")
        target_emp_id = batch.target_employee_id
        policy = batch.conflict_policy
        now = dt.datetime.now(dt.UTC)

        applied_items_count = 0

        if batch.mode == "TERRITORY":
            query = select(Territory).where(Territory.is_active.is_(True))
            if payload_dict.get("territory_ids"):
                query = query.where(Territory.id.in_(payload_dict["territory_ids"]))
            elif payload_dict.get("filter_state_id"):
                query = query.where(Territory.state_id == payload_dict["filter_state_id"])

            territories = self.db.scalars(query).all()
            for t in territories:
                # Find active assignments
                active_assign = self.db.scalar(
                    select(UserTerritoryAssignment).where(
                        UserTerritoryAssignment.territory_id == t.id,
                        UserTerritoryAssignment.unassigned_at.is_(None),
                    )
                )

                if active_assign:
                    if active_assign.user_id == target_emp_id:
                        continue  # Already assigned to target
                    if policy == "SKIP":
                        continue
                    elif policy == "REPLACE":
                        # Soft unassign existing user (BR-11: never hard delete)
                        active_assign.unassigned_at = now
                        item_un = MappingBatchItem(
                            batch_id=batch.id,
                            action="UNASSIGN",
                            employee_id=active_assign.user_id,
                            territory_id=t.id,
                            before_state=json.dumps({"assigned_at": str(active_assign.assigned_at)}),
                            after_state=json.dumps({"unassigned_at": str(now)}),
                        )
                        self.db.add(item_un)

                # Assign to target user
                new_assign = UserTerritoryAssignment(
                    user_id=target_emp_id,
                    territory_id=t.id,
                    assigned_at=now,
                )
                self.db.add(new_assign)

                item_as = MappingBatchItem(
                    batch_id=batch.id,
                    action="ASSIGN",
                    employee_id=target_emp_id,
                    territory_id=t.id,
                    before_state=None,
                    after_state=json.dumps({"assigned_at": str(now)}),
                )
                self.db.add(item_as)
                applied_items_count += 1

        batch.status = "APPLIED"
        batch.applied_at = now

        AuditService.record(
            self.db,
            user_id=current_user.id,
            module="MAPPINGS",
            action="MAPPING_APPLY",
            entity_type="MappingBatch",
            entity_id=str(batch.id),
            summary=f"Applied {batch.mode} batch #{batch.id} ({applied_items_count} items assigned) to user #{target_emp_id}",
            channel="WEB",
        )

        self.db.commit()
        self.db.refresh(batch)
        return self._to_batch_response(batch)

    def revert(self, batch_id: int, current_user: User) -> MappingBatchResponse:
        """Revert an applied batch restoring the previous assignment state."""
        batch = self.db.scalar(select(MappingBatch).where(MappingBatch.id == batch_id))
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mapping batch with ID {batch_id} not found.",
            )
        if batch.status != "APPLIED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot revert batch with status '{batch.status}'. Only APPLIED batches can be reverted.",
            )

        now = dt.datetime.now(dt.UTC)
        items = self.db.scalars(
            select(MappingBatchItem).where(MappingBatchItem.batch_id == batch.id)
        ).all()

        for item in items:
            if item.action == "ASSIGN" and item.territory_id:
                # Soft unassign the assignment that was created by this batch
                assign = self.db.scalar(
                    select(UserTerritoryAssignment).where(
                        UserTerritoryAssignment.user_id == item.employee_id,
                        UserTerritoryAssignment.territory_id == item.territory_id,
                        UserTerritoryAssignment.unassigned_at.is_(None),
                    )
                )
                if assign:
                    assign.unassigned_at = now
            elif item.action == "UNASSIGN" and item.territory_id:
                # Restore previous assignment
                restore_assign = UserTerritoryAssignment(
                    user_id=item.employee_id,
                    territory_id=item.territory_id,
                    assigned_at=now,
                )
                self.db.add(restore_assign)

        batch.status = "REVERTED"
        batch.reverted_at = now

        AuditService.record(
            self.db,
            user_id=current_user.id,
            module="MAPPINGS",
            action="MAPPING_REVERT",
            entity_type="MappingBatch",
            entity_id=str(batch.id),
            summary=f"Reverted mapping batch #{batch.id} ({len(items)} items restored)",
            channel="WEB",
        )

        self.db.commit()
        self.db.refresh(batch)
        return self._to_batch_response(batch)

    def list_batches(
        self,
        mode: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[MappingBatchResponse]:
        """List mapping batches history."""
        query = select(MappingBatch)
        if mode:
            query = query.where(MappingBatch.mode == mode.upper())
        if status:
            query = query.where(MappingBatch.status == status.upper())

        batches = (
            self.db.scalars(
                query.order_by(desc(MappingBatch.created_at))
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            .all()
        )
        return [self._to_batch_response(b) for b in batches]

    def get_batch_detail(self, batch_id: int, page: int = 1, page_size: int = 50) -> MappingBatchDetailResponse:
        """Fetch batch summary and paginated assignment items."""
        batch = self.db.scalar(select(MappingBatch).where(MappingBatch.id == batch_id))
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mapping batch with ID {batch_id} not found.",
            )

        items_query = select(MappingBatchItem).where(MappingBatchItem.batch_id == batch_id)
        total_items = self.db.scalar(select(func.count()).select_from(items_query.subquery())) or 0
        items = (
            self.db.scalars(
                items_query.order_by(MappingBatchItem.id)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            .all()
        )

        item_responses = [
            MappingBatchItemResponse(
                id=i.id,
                batch_id=i.batch_id,
                action=i.action,
                employee_id=i.employee_id,
                territory_id=i.territory_id,
                customer_type=i.customer_type,
                customer_id=i.customer_id,
                before_state=i.before_state,
                after_state=i.after_state,
                created_at=i.created_at,
            )
            for i in items
        ]

        return MappingBatchDetailResponse(
            batch=self._to_batch_response(batch),
            items=item_responses,
            total_items=total_items,
            page=page,
            page_size=page_size,
        )

    def _to_batch_response(self, batch: MappingBatch) -> MappingBatchResponse:
        counts = None
        if batch.counts_json:
            try:
                counts = json.loads(batch.counts_json)
            except Exception:
                counts = None

        emp_name = None
        if batch.target_employee_id:
            u = self.db.scalar(select(User).where(User.id == batch.target_employee_id))
            emp_name = u.full_name if u else None

        return MappingBatchResponse(
            id=batch.id,
            mode=batch.mode,
            status=batch.status,
            target_employee_id=batch.target_employee_id,
            target_employee_name=emp_name,
            conflict_policy=batch.conflict_policy,
            counts=counts,
            applied_at=batch.applied_at,
            reverted_at=batch.reverted_at,
            created_at=batch.created_at,
        )
