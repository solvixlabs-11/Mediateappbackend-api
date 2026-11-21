"""Mobile registrations service."""

from __future__ import annotations

import math
from typing import Any

from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session, joinedload

from app.db.mixins import utc_now
from app.modules.audit.service import AuditService
from app.modules.mobile_registrations.models import MobileRegistration
from app.modules.mobile_registrations.schemas import (
    MobileRegistrationBulkActionRequest,
    MobileRegistrationBulkActionResponse,
    MobileRegistrationListResponse,
    MobileRegistrationResponse,
    MobileRegistrationRowResult,
)
from app.modules.users.models import User


class MobileRegistrationService:
    """Business logic for device and mobile registrations."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def _to_response(self, reg: MobileRegistration) -> MobileRegistrationResponse:
        return MobileRegistrationResponse(
            id=reg.id,
            registration_code=reg.registration_code,
            employee_id=reg.employee_id,
            employee_name=reg.employee.full_name if reg.employee else None,
            employee_email=reg.employee.email if reg.employee else None,
            designation=reg.designation or (reg.employee.role.name if reg.employee and reg.employee.role else "Medical Representative"),
            territory=reg.territory or "Central Territory",
            city="Mumbai",
            state="Maharashtra",
            device_id_hash=reg.device_id_hash,
            device_model=reg.device_model,
            app_version=reg.app_version,
            status=reg.status,
            requested_at=reg.requested_at,
            decided_by_id=reg.decided_by_id,
            decided_by_name=reg.decided_by.full_name if reg.decided_by else None,
            decided_at=reg.decided_at,
            comment=reg.comment,
            created_at=reg.created_at,
            updated_at=reg.updated_at,
        )

    def list_registrations(
        self,
        *,
        status: str | None = None,
        search: str | None = None,
        state_ids: list[int] | None = None,
        city_ids: list[int] | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> MobileRegistrationListResponse:
        query = (
            self.db.query(MobileRegistration)
            .join(MobileRegistration.employee)
            .options(
                joinedload(MobileRegistration.employee).joinedload(User.role),
                joinedload(MobileRegistration.decided_by),
            )
        )

        if status and status.upper() != "ALL":
            query = query.filter(MobileRegistration.status == status.upper())

        if state_ids:
            query = query.filter(User.state_id.in_(state_ids))

        if city_ids:
            query = query.filter(User.city_id.in_(city_ids))

        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    MobileRegistration.registration_code.ilike(term),
                    MobileRegistration.device_model.ilike(term),
                    User.full_name.ilike(term),
                    User.email.ilike(term),
                )
            )

        total = query.count()
        pending_count = (
            self.db.query(func.count(MobileRegistration.id))
            .filter(MobileRegistration.status == "PENDING")
            .scalar()
            or 0
        )

        items = (
            query.order_by(desc(MobileRegistration.requested_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        total_pages = math.ceil(total / page_size) if total > 0 else 1

        return MobileRegistrationListResponse(
            items=[self._to_response(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            pending_count=pending_count,
        )

    def approve_registrations(
        self,
        payload: MobileRegistrationBulkActionRequest,
        admin_user: User,
    ) -> MobileRegistrationBulkActionResponse:
        results: list[MobileRegistrationRowResult] = []
        success_count = 0
        failure_count = 0
        now = utc_now()

        for reg_id in payload.ids:
            reg = self.db.query(MobileRegistration).filter(MobileRegistration.id == reg_id).first()
            if not reg:
                results.append(
                    MobileRegistrationRowResult(
                        id=reg_id,
                        success=False,
                        status="NOT_FOUND",
                        message=f"Registration #{reg_id} does not exist.",
                    )
                )
                failure_count += 1
                continue

            if reg.status != "PENDING":
                results.append(
                    MobileRegistrationRowResult(
                        id=reg_id,
                        success=False,
                        status=reg.status,
                        message=f"Registration #{reg_id} is already {reg.status}.",
                    )
                )
                failure_count += 1
                continue

            # Update registration record
            reg.status = "APPROVED"
            reg.decided_by_id = admin_user.id
            reg.decided_at = now
            reg.comment = payload.comment

            # Activate employee user account
            employee = self.db.query(User).filter(User.id == reg.employee_id).first()
            if employee:
                employee.is_active = True

            # Audit log
            AuditService.record(
                self.db,
                user_id=admin_user.id,
                module="mobile_registrations",
                action="APPROVE_MOBILE_REGISTRATION",
                entity_type="mobile_registration",
                entity_id=str(reg.id),
                summary=f"Approved mobile registration for employee #{reg.employee_id} ({employee.full_name if employee else 'N/A'})",
                after={"status": "APPROVED", "device_model": reg.device_model, "comment": payload.comment},
            )

            results.append(
                MobileRegistrationRowResult(
                    id=reg_id,
                    success=True,
                    status="APPROVED",
                    message="Registration approved and employee account activated.",
                )
            )
            success_count += 1

        self.db.commit()

        return MobileRegistrationBulkActionResponse(
            total_processed=len(payload.ids),
            success_count=success_count,
            failure_count=failure_count,
            results=results,
        )

    def reject_registrations(
        self,
        payload: MobileRegistrationBulkActionRequest,
        admin_user: User,
    ) -> MobileRegistrationBulkActionResponse:
        results: list[MobileRegistrationRowResult] = []
        success_count = 0
        failure_count = 0
        now = utc_now()

        for reg_id in payload.ids:
            reg = self.db.query(MobileRegistration).filter(MobileRegistration.id == reg_id).first()
            if not reg:
                results.append(
                    MobileRegistrationRowResult(
                        id=reg_id,
                        success=False,
                        status="NOT_FOUND",
                        message=f"Registration #{reg_id} does not exist.",
                    )
                )
                failure_count += 1
                continue

            if reg.status != "PENDING":
                results.append(
                    MobileRegistrationRowResult(
                        id=reg_id,
                        success=False,
                        status=reg.status,
                        message=f"Registration #{reg_id} is already {reg.status}.",
                    )
                )
                failure_count += 1
                continue

            # Update registration record
            reg.status = "REJECTED"
            reg.decided_by_id = admin_user.id
            reg.decided_at = now
            reg.comment = payload.comment or "Registration rejected by administrator"

            # Audit log
            AuditService.record(
                self.db,
                user_id=admin_user.id,
                module="mobile_registrations",
                action="REJECT_MOBILE_REGISTRATION",
                entity_type="mobile_registration",
                entity_id=str(reg.id),
                summary=f"Rejected mobile registration for employee #{reg.employee_id}",
                after={"status": "REJECTED", "comment": reg.comment},
            )

            results.append(
                MobileRegistrationRowResult(
                    id=reg_id,
                    success=True,
                    status="REJECTED",
                    message="Registration rejected.",
                )
            )
            success_count += 1

        self.db.commit()

        return MobileRegistrationBulkActionResponse(
            total_processed=len(payload.ids),
            success_count=success_count,
            failure_count=failure_count,
            results=results,
        )
