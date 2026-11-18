"""SQLAlchemy ORM models for Report Definitions and Execution Logs."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ReportDefinition(Base):
    """Database entity defining report metadata, filter schemas, allowed roles, and availability status."""

    __tablename__ = "report_definitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    group: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="AVAILABLE", nullable=False, index=True)
    unavailable_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    formats: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    filter_schema: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    allowed_roles: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    data_as_of_source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
