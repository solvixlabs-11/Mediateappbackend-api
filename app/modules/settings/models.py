"""System Configuration & Geofence Settings SQLAlchemy ORM models."""

from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import StandardAuditMixin


class AppSetting(Base, StandardAuditMixin):
    """System-wide typed business configuration setting."""

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    group: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    value_type: Mapped[str] = mapped_column(String(30), nullable=False)  # BOOLEAN, INTEGER, DECIMAL, TEXT, TIME, SELECT, FORMULA
    unit: Mapped[str | None] = mapped_column(String(30), nullable=True)  # m, min, hours, days, rows, time, none
    min_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    allowed_options: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON or comma-separated options for SELECT
    help_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_provisional: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class GeofenceSetting(Base, StandardAuditMixin):
    """Geofence radius and accuracy rules per customer entity type."""

    __tablename__ = "geofence_settings"

    entity_type: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)  # DOCTOR, HOSPITAL, CHEMIST, STOCKIST
    radius_m: Mapped[float] = mapped_column(Float, nullable=False)
    min_accuracy_m: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)
    is_provisional: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class SettingHistory(Base, StandardAuditMixin):
    """Audit log of individual setting value changes."""

    __tablename__ = "setting_history"

    key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str] = mapped_column(Text, nullable=False)
    changed_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    change_summary: Mapped[str | None] = mapped_column(String(255), nullable=True)
