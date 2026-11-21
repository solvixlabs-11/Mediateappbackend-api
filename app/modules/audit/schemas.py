"""System Audit Trail Pydantic schemas."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    """Single audit log entry."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None = None
    user_name: str | None = None
    module: str
    action: str
    entity_type: str | None = None
    entity_id: str | None = None
    channel: str
    request_id: str | None = None
    result: str
    summary: str | None = None
    details: str | None = None
    before_json: str | None = None
    after_json: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: dt.datetime


class AuditLogListResponse(BaseModel):
    """Paginated audit logs response."""

    total: int
    page: int
    page_size: int
    items: list[AuditLogResponse]


class AuditMetaOption(BaseModel):
    """Code and label item for dynamic filters."""

    code: str
    label: str


class AuditMetaResponse(BaseModel):
    """Dynamic metadata options for audit log filters."""

    modules: list[AuditMetaOption]
    actions: list[AuditMetaOption]
    channels: list[AuditMetaOption]
    results: list[AuditMetaOption]
    users: list[dict[str, str | int]]
