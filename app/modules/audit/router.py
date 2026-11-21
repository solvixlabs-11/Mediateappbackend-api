"""System Audit Trail REST API endpoints."""

from __future__ import annotations

import datetime as dt
import io
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.audit.schemas import (
    AuditLogListResponse,
    AuditLogResponse,
    AuditMetaResponse,
)
from app.modules.audit.service import AuditService
from app.modules.users.models import User

router = APIRouter(prefix="/audit", tags=["Audit Trail"])


def _check_admin_access(current_user: User) -> None:
    """Ensure user is an administrator."""
    if not current_user.role or current_user.role.code not in ["ADMIN", "ERP ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Audit trail is restricted to administrators.",
        )


@router.get(
    "/meta",
    response_model=AuditMetaResponse,
    summary="Get dynamic metadata options for audit log filters",
)
def get_audit_meta(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Fetch distinct modules, actions, channels, and results from audit logs."""
    _check_admin_access(current_user)
    service = AuditService(db)
    return service.get_meta()


@router.get(
    "/logs",
    response_model=AuditLogListResponse,
    summary="List audit logs with filtering and pagination",
)
def list_audit_logs(
    user_id: int | None = Query(default=None),
    module: str | None = Query(default=None),
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    result: str | None = Query(default=None),
    channel: str | None = Query(default=None),
    date_from: dt.datetime | None = Query(default=None),
    date_to: dt.datetime | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Fetch paginated system audit trail events."""
    _check_admin_access(current_user)
    service = AuditService(db)
    total, logs = service.list_logs(
        user_id=user_id,
        module=module,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        result=result,
        channel=channel,
        date_from=date_from,
        date_to=date_to,
        search=search,
        page=page,
        page_size=page_size,
    )

    items = []
    for log in logs:
        user_name = log.created_by_user.full_name if getattr(log, "created_by_user", None) else None
        items.append(
            AuditLogResponse(
                id=log.id,
                user_id=log.user_id,
                user_name=user_name,
                module=log.module,
                action=log.action,
                entity_type=log.entity_type,
                entity_id=log.entity_id,
                channel=log.channel,
                request_id=log.request_id,
                result=log.result,
                summary=log.summary,
                details=log.details,
                before_json=log.before_json,
                after_json=log.after_json,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                created_at=log.created_at,
            )
        )

    return AuditLogListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )


@router.get(
    "/logs/{log_id}",
    response_model=AuditLogResponse,
    summary="Get single audit log entry details",
)
def get_audit_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Fetch complete detail of an audit event including before/after diffs."""
    _check_admin_access(current_user)
    service = AuditService(db)
    log = service.get_log_by_id(log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit log entry with ID {log_id} not found.",
        )

    user_name = log.created_by_user.full_name if getattr(log, "created_by_user", None) else None
    return AuditLogResponse(
        id=log.id,
        user_id=log.user_id,
        user_name=user_name,
        module=log.module,
        action=log.action,
        entity_type=log.entity_type,
        entity_id=log.entity_id,
        channel=log.channel,
        request_id=log.request_id,
        result=log.result,
        summary=log.summary,
        details=log.details,
        before_json=log.before_json,
        after_json=log.after_json,
        ip_address=log.ip_address,
        user_agent=log.user_agent,
        created_at=log.created_at,
    )


@router.post(
    "/logs/export",
    summary="Export audit logs to CSV/Excel",
)
def export_audit_logs(
    format: str = Query(default="csv", pattern="^(csv|xlsx)$"),
    user_id: int | None = Query(default=None),
    module: str | None = Query(default=None),
    action: str | None = Query(default=None),
    date_from: dt.datetime | None = Query(default=None),
    date_to: dt.datetime | None = Query(default=None),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Stream export of filtered audit logs (action itself is audited)."""
    _check_admin_access(current_user)
    service = AuditService(db)
    _, logs = service.list_logs(
        user_id=user_id,
        module=module,
        action=action,
        date_from=date_from,
        date_to=date_to,
        search=search,
        page=1,
        page_size=5000,
    )

    # Audit the export action
    AuditService.record(
        db,
        user_id=current_user.id,
        module="AUDIT",
        action="EXPORT",
        summary=f"Admin {current_user.full_name} exported {len(logs)} audit log records in {format.upper()} format.",
        channel="WEB",
    )
    db.commit()

    output = io.StringIO()
    output.write("ID,Timestamp,Module,Action,Entity Type,Entity ID,Result,Channel,Summary\n")
    for log in logs:
        clean_summary = (log.summary or "").replace(",", ";").replace("\n", " ")
        output.write(
            f"{log.id},{log.created_at},{log.module},{log.action},{log.entity_type or ''},"
            f"{log.entity_id or ''},{log.result},{log.channel},{clean_summary}\n"
        )

    mem_stream = io.BytesIO(output.getvalue().encode("utf-8"))
    return StreamingResponse(
        mem_stream,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=audit_logs_{dt.date.today()}.csv"},
    )
