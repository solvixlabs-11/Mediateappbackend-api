"""Unified Audit Service for compliance, security logging, and traceability."""

from __future__ import annotations

import datetime as dt
import json
import re
from typing import Any

from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from app.modules.common.models import AuditLog
from app.modules.users.models import User

# Keys whose values should always be masked
SENSITIVE_KEYS = {
    "password",
    "hashed_password",
    "secret",
    "secret_key",
    "token",
    "access_token",
    "refresh_token",
    "otp",
    "api_key",
    "authorization",
}


def mask_sensitive_data(data: Any) -> Any:
    """Recursively mask sensitive attributes in dicts, lists, and primitives."""
    if isinstance(data, dict):
        masked: dict[str, Any] = {}
        for k, v in data.items():
            lower_k = str(k).lower()
            if any(s in lower_k for s in SENSITIVE_KEYS):
                masked[k] = "******"
            elif lower_k in {"phone", "mobile", "contact"} and isinstance(v, str) and len(v) >= 4:
                masked[k] = f"******{v[-4:]}"
            else:
                masked[k] = mask_sensitive_data(v)
        return masked
    elif isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    return data


def to_json_str(val: Any) -> str | None:
    """Format object or string to masked JSON string."""
    if val is None:
        return None
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            return json.dumps(mask_sensitive_data(parsed))
        except (json.JSONDecodeError, ValueError):
            # Check for phone numbers in plain string
            phone_pattern = re.compile(r"\b\d{10}\b")
            return phone_pattern.sub(lambda m: f"******{m.group(0)[-4:]}", val)
    return json.dumps(mask_sensitive_data(val))


class AuditService:
    """Central audit recorder and query service."""

    def __init__(self, db: Session) -> None:
        self.db = db

    @classmethod
    def record(
        cls,
        db: Session,
        *,
        module: str,
        action: str,
        user_id: int | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        channel: str = "WEB",
        request_id: str | None = None,
        result: str = "SUCCESS",
        summary: str | None = None,
        details: str | None = None,
        before: Any = None,
        after: Any = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Create and persist an immutable audit trail entry."""
        log = AuditLog(
            user_id=user_id,
            module=module,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            channel=channel,
            request_id=request_id,
            result=result,
            summary=summary,
            details=details,
            before_json=to_json_str(before),
            after_json=to_json_str(after),
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,
        )
        db.add(log)
        db.flush()
        return log

    def list_logs(
        self,
        *,
        user_id: int | None = None,
        module: str | None = None,
        action: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        result: str | None = None,
        channel: str | None = None,
        date_from: dt.datetime | None = None,
        date_to: dt.datetime | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[int, list[AuditLog]]:
        """Query audit trail with multi-field filtering and pagination."""
        query = select(AuditLog)

        if user_id is not None:
            query = query.where(AuditLog.user_id == user_id)
        if module:
            query = query.where(AuditLog.module == module)
        if action:
            query = query.where(AuditLog.action == action)
        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)
        if entity_id:
            query = query.where(AuditLog.entity_id == entity_id)
        if result:
            query = query.where(AuditLog.result == result)
        if channel:
            query = query.where(AuditLog.channel == channel)
        if date_from:
            query = query.where(AuditLog.created_at >= date_from)
        if date_to:
            query = query.where(AuditLog.created_at <= date_to)
        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.where(
                or_(
                    AuditLog.summary.ilike(search_pattern),
                    AuditLog.details.ilike(search_pattern),
                    AuditLog.entity_id.ilike(search_pattern),
                )
            )

        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        logs = (
            self.db.scalars(
                query.order_by(desc(AuditLog.created_at))
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            .all()
        )
        return total, list(logs)

    def get_log_by_id(self, log_id: int) -> AuditLog | None:
        """Fetch single audit log by primary key."""
        return self.db.scalar(select(AuditLog).where(AuditLog.id == log_id))

    def get_meta(self) -> dict[str, Any]:
        """Return distinct metadata options dynamically from data."""
        modules = [
            {"code": r, "label": r.replace("_", " ").title()}
            for r in self.db.scalars(select(AuditLog.module).distinct()).all()
            if r
        ]
        actions = [
            {"code": r, "label": r.replace("_", " ").title()}
            for r in self.db.scalars(select(AuditLog.action).distinct()).all()
            if r
        ]
        channels = [
            {"code": r, "label": r.title()}
            for r in self.db.scalars(select(AuditLog.channel).distinct()).all()
            if r
        ]
        results = [
            {"code": r, "label": r.title()}
            for r in self.db.scalars(select(AuditLog.result).distinct()).all()
            if r
        ]

        users = [
            {"id": u.id, "name": u.full_name, "email": u.email}
            for u in self.db.scalars(
                select(User).order_by(User.full_name).limit(100)
            ).all()
        ]

        return {
            "modules": modules,
            "actions": actions,
            "channels": channels,
            "results": results,
            "users": users,
        }

    def cleanup_retention(self, retention_days: int) -> int:
        """Remove audit logs older than retention period; log retention execution."""
        cutoff_date = dt.datetime.now(dt.UTC) - dt.timedelta(days=retention_days)
        deleted = (
            self.db.query(AuditLog)
            .filter(AuditLog.created_at < cutoff_date)
            .delete(synchronize_session=False)
        )
        self.db.commit()

        # Audit the cleanup itself
        self.record(
            self.db,
            module="AUDIT",
            action="DELETE",
            summary=f"Automated retention policy purged {deleted} audit log rows older than {retention_days} days.",
            channel="SYSTEM",
        )
        self.db.commit()
        return deleted
