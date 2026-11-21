"""Tour Program business logic service."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session, joinedload

from app.db.mixins import utc_now
from app.modules.approvals.repository import ApprovalRepository
from app.modules.audit.service import AuditService
from app.modules.territories.models import Territory
from app.modules.tours.models import TourPlanLock, TourProgram
from app.modules.tours.repository import TourRepository
from app.modules.tours.schemas import (
    TourPlanLockCreateRequest,
    TourPlanLockResponse,
    TourPlanUnlockRequest,
    TourProgramCreateRequest,
    TourProgramResponse,
)
from app.modules.users.models import User


class TourService:
    """Service enforcing Tour Program lifecycle, cutoff locking, and approval dispatch."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = TourRepository(db)
        self.approval_repo = ApprovalRepository(db)

    def _to_response(self, tour: TourProgram) -> TourProgramResponse:
        return TourProgramResponse(
            id=tour.id,
            user_id=tour.user_id,
            user_name=tour.user.full_name if tour.user else None,
            title=tour.title,
            start_date=tour.start_date,
            end_date=tour.end_date,
            total_days=tour.total_days,
            route_details=tour.route_details,
            objectives=tour.objectives,
            status=tour.status,
            approval_request_id=tour.approval_request_id,
            rejection_reason=tour.rejection_reason,
            created_at=tour.created_at,
            updated_at=tour.updated_at,
        )

    def _to_lock_response(self, lock: TourPlanLock) -> TourPlanLockResponse:
        scope_name = None
        if lock.scope == "ALL":
            scope_name = "All India / Entire Organization"
        elif lock.scope == "TERRITORY" and lock.scope_id:
            terr = self.db.query(Territory).filter(Territory.id == lock.scope_id).first()
            scope_name = f"Territory: {terr.name}" if terr else f"Territory #{lock.scope_id}"
        elif lock.scope == "EMPLOYEE" and lock.scope_id:
            emp = self.db.query(User).filter(User.id == lock.scope_id).first()
            scope_name = f"Employee: {emp.full_name}" if emp else f"Employee #{lock.scope_id}"

        return TourPlanLockResponse(
            id=lock.id,
            scope=lock.scope,
            scope_id=lock.scope_id,
            scope_name=scope_name,
            month=lock.month,
            year=lock.year,
            financial_year=lock.financial_year,
            cutoff_date=lock.cutoff_date,
            status=lock.status,
            reason=lock.reason,
            created_by_id=lock.created_by_id,
            created_by_name=lock.created_by_user.full_name if lock.created_by_user else None,
            unlocked_by_id=lock.unlocked_by_id,
            unlocked_by_name=lock.unlocked_by_user.full_name if lock.unlocked_by_user else None,
            unlocked_at=lock.unlocked_at,
            created_at=lock.created_at,
            updated_at=lock.updated_at,
        )

    def check_tour_lock(
        self,
        user: User,
        month: int,
        year: int,
        admin_override_reason: str | None = None,
    ) -> None:
        """Check if an active cutoff lock applies to this tour submission."""
        locks = (
            self.db.query(TourPlanLock)
            .filter(
                TourPlanLock.month == month,
                TourPlanLock.year == year,
                TourPlanLock.status == "LOCKED",
            )
            .all()
        )

        for lock in locks:
            is_locked = False
            if lock.scope == "ALL":
                is_locked = True
            elif lock.scope == "TERRITORY" and user.territory_id and lock.scope_id == user.territory_id:
                is_locked = True
            elif lock.scope == "EMPLOYEE" and lock.scope_id == user.id:
                is_locked = True

            if is_locked:
                role_code = user.role.code if user.role else "MR"
                # Admin override check
                if role_code in ("ADMIN", "ERP ADMIN") and admin_override_reason:
                    AuditService.record(
                        self.db,
                        user_id=user.id,
                        module="tours",
                        action="TOUR_PLAN_LOCK_OVERRIDE",
                        entity_type="tour_plan_lock",
                        entity_id=str(lock.id),
                        summary=f"Admin {user.full_name} overrode lock #{lock.id} for user #{user.id}. Reason: {admin_override_reason}",
                    )
                    return

                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"TOUR_PLAN_LOCKED: Tour plan submissions for {year}-{month:02d} are locked by {lock.created_by_user.full_name if lock.created_by_user else 'Admin'}. Reason: {lock.reason or 'Monthly cutoff deadline passed'}.",
                )

    def create_tour(self, payload: TourProgramCreateRequest, user: User) -> TourProgramResponse:
        """Create and submit a Tour Program with lock & overlap validation (BR-09)."""
        if payload.end_date < payload.start_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Tour end date cannot precede start date.",
            )

        # Enforce Tour Plan Lock
        self.check_tour_lock(
            user=user,
            month=payload.start_date.month,
            year=payload.start_date.year,
            admin_override_reason=payload.admin_override_reason,
        )

        # BR-09: Overlapping tour check
        if self.repo.has_overlapping_tour(user.id, payload.start_date, payload.end_date):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A Tour Program already exists overlapping this date period.",
            )

        total_days = (payload.end_date - payload.start_date).days + 1

        tour = self.repo.create(
            user_id=user.id,
            title=payload.title,
            start_date=payload.start_date,
            end_date=payload.end_date,
            total_days=total_days,
            route_details=payload.route_details,
            objectives=payload.objectives,
        )

        # Dispatch approval request into the manager's inbox
        approval_req = self.approval_repo.create_request(
            entity_type="TOUR",
            entity_id=tour.id,
            requester_id=user.id,
            title=f"Tour Plan: {tour.title} ({tour.start_date} to {tour.end_date})",
            details=f"Route: {tour.route_details or 'N/A'}. Total Days: {total_days}.",
        )
        tour.approval_request_id = approval_req.id

        self.db.commit()
        self.db.refresh(tour)
        return self._to_response(tour)

    def list_tours(self, current_user: User) -> list[TourProgramResponse]:
        """List tours scoped to user (MR sees own, Manager/Admin sees team/all)."""
        role_code = current_user.role.code if current_user.role else "MR"
        user_id = None if role_code in ("ADMIN", "MANAGER") else current_user.id
        tours = self.repo.list_tours(user_id=user_id)
        return [self._to_response(t) for t in tours]

    def get_tour(self, tour_id: int) -> TourProgramResponse:
        """Fetch tour program by id."""
        tour = self.repo.get_by_id(tour_id)
        if not tour:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tour program {tour_id} not found.",
            )
        return self._to_response(tour)

    # --- Tour Plan Lock Management APIs ---

    def list_locks(
        self,
        *,
        month: int | None = None,
        year: int | None = None,
        scope: str | None = None,
        status: str | None = None,
    ) -> list[TourPlanLockResponse]:
        """List active and historical tour plan cutoff locks."""
        query = (
            self.db.query(TourPlanLock)
            .options(
                joinedload(TourPlanLock.created_by_user),
                joinedload(TourPlanLock.unlocked_by_user),
            )
        )

        if month:
            query = query.filter(TourPlanLock.month == month)
        if year:
            query = query.filter(TourPlanLock.year == year)
        if scope and scope.upper() != "ALL_SCOPES":
            query = query.filter(TourPlanLock.scope == scope.upper())
        if status and status.upper() != "ALL":
            query = query.filter(TourPlanLock.status == status.upper())

        locks = query.order_by(desc(TourPlanLock.created_at)).all()
        return [self._to_lock_response(l) for l in locks]

    def create_lock(
        self,
        payload: TourPlanLockCreateRequest,
        admin_user: User,
    ) -> TourPlanLockResponse:
        """Create a new cutoff lock for tour plan submissions."""
        existing = (
            self.db.query(TourPlanLock)
            .filter(
                TourPlanLock.scope == payload.scope.upper(),
                TourPlanLock.scope_id == payload.scope_id,
                TourPlanLock.month == payload.month,
                TourPlanLock.year == payload.year,
                TourPlanLock.status == "LOCKED",
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"An active lock already exists for {payload.scope} #{payload.scope_id or 'ALL'} for month {payload.year}-{payload.month:02d}.",
            )

        lock = TourPlanLock(
            scope=payload.scope.upper(),
            scope_id=payload.scope_id,
            month=payload.month,
            year=payload.year,
            financial_year=payload.financial_year,
            cutoff_date=payload.cutoff_date,
            status="LOCKED",
            reason=payload.reason or f"Cutoff lock established on {payload.cutoff_date}",
            created_by_id=admin_user.id,
        )
        self.db.add(lock)
        self.db.flush()

        AuditService.record(
            self.db,
            user_id=admin_user.id,
            module="tours",
            action="CREATE_TOUR_PLAN_LOCK",
            entity_type="tour_plan_lock",
            entity_id=str(lock.id),
            summary=f"Created {payload.scope} lock for {payload.year}-{payload.month:02d}. Reason: {lock.reason}",
            after={"scope": lock.scope, "scope_id": lock.scope_id, "month": lock.month, "year": lock.year},
        )

        self.db.commit()
        self.db.refresh(lock)
        return self._to_lock_response(lock)

    def unlock_lock(
        self,
        lock_id: int,
        payload: TourPlanUnlockRequest,
        admin_user: User,
    ) -> TourPlanLockResponse:
        """Unlock an existing tour plan lock with audited business justification."""
        lock = self.db.query(TourPlanLock).filter(TourPlanLock.id == lock_id).first()
        if not lock:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tour plan lock #{lock_id} not found.",
            )

        if lock.status == "UNLOCKED":
            return self._to_lock_response(lock)

        lock.status = "UNLOCKED"
        lock.unlocked_by_id = admin_user.id
        lock.unlocked_at = utc_now()
        lock.reason = f"{lock.reason or ''} | Unlocked by {admin_user.full_name}: {payload.reason}".strip()

        AuditService.record(
            self.db,
            user_id=admin_user.id,
            module="tours",
            action="UNLOCK_TOUR_PLAN",
            entity_type="tour_plan_lock",
            entity_id=str(lock.id),
            summary=f"Unlocked tour plan lock #{lock.id}. Reason: {payload.reason}",
            after={"status": "UNLOCKED", "unlocked_by": admin_user.id, "unlock_reason": payload.reason},
        )

        self.db.commit()
        self.db.refresh(lock)
        return self._to_lock_response(lock)

    def get_lock_history(self) -> list[TourPlanLockResponse]:
        """Fetch all lock and unlock audit historical events."""
        locks = (
            self.db.query(TourPlanLock)
            .options(
                joinedload(TourPlanLock.created_by_user),
                joinedload(TourPlanLock.unlocked_by_user),
            )
            .order_by(desc(TourPlanLock.updated_at))
            .limit(100)
            .all()
        )
        return [self._to_lock_response(l) for l in locks]
