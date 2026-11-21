"""System Configuration & Geofence Settings business logic service."""

from __future__ import annotations

import json
import re

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.audit.service import AuditService
from app.modules.settings.models import AppSetting, GeofenceSetting, SettingHistory
from app.modules.settings.schemas import (
    GeofenceBulkUpdateRequest,
    GeofenceSettingResponse,
    SettingBulkUpdateRequest,
    SettingGroupResponse,
    SettingHistoryResponse,
    SettingResponse,
)
from app.modules.users.models import User

# In-memory settings cache: {key: value}
_SETTINGS_CACHE: dict[str, str] = {}
_GEOFENCE_CACHE: dict[str, float] = {}

GROUP_METADATA = {
    "GEOFENCE": {"title": "Geofence Rules", "description": "Customer verification radii and GPS accuracy thresholds"},
    "GPS": {"title": "GPS & Location", "description": "Telemetry accuracy, spoofing, and mock GPS actions"},
    "ATTENDANCE": {"title": "Daily Attendance", "description": "Punch-in cutoffs, late tolerances, and working hours"},
    "DCR": {"title": "Daily Call Reports (DCR)", "description": "Reporting cutoffs, edit windows, and lock rules"},
    "EXPENSE": {"title": "Expense Policies", "description": "Limit enforcement policies and receipt requirements"},
    "NOTIFICATIONS": {"title": "System Alerts", "description": "Automated reminder schedules and push trigger times"},
    "SECURITY": {"title": "Access & Security", "description": "Login lockouts, failed attempt thresholds, and session timeouts"},
    "AUDIT": {"title": "Audit & Compliance", "description": "Audit retention policies and compliance archiving"},
    "EXPORT": {"title": "Data Export Rules", "description": "Row limits and date-range constraints for data exports"},
}


class SettingsService:
    """Service providing typed validation, caching, and audit for system settings."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def invalidate_cache(self) -> None:
        """Clear local in-memory configuration cache."""
        global _SETTINGS_CACHE, _GEOFENCE_CACHE
        _SETTINGS_CACHE.clear()
        _GEOFENCE_CACHE.clear()

    def get_setting_value(self, key: str, default: str | None = None) -> str:
        """Get raw setting string value with caching."""
        global _SETTINGS_CACHE
        if key in _SETTINGS_CACHE:
            return _SETTINGS_CACHE[key]

        setting = self.db.scalar(select(AppSetting).where(AppSetting.key == key))
        if setting:
            _SETTINGS_CACHE[key] = setting.value
            return setting.value
        return default or ""

    def get_geofence_radius(self, entity_type: str, default: float = 150.0) -> float:
        """Retrieve dynamic geofence radius for a customer category."""
        global _GEOFENCE_CACHE
        normalized_type = entity_type.upper().strip()
        if normalized_type in _GEOFENCE_CACHE:
            return _GEOFENCE_CACHE[normalized_type]

        setting = self.db.scalar(
            select(GeofenceSetting).where(GeofenceSetting.entity_type == normalized_type)
        )
        if setting:
            _GEOFENCE_CACHE[normalized_type] = setting.radius_m
            return setting.radius_m
        return default

    def _to_response(self, setting: AppSetting) -> SettingResponse:
        options = None
        if setting.allowed_options:
            try:
                options = json.loads(setting.allowed_options)
            except Exception:
                options = [o.strip() for o in setting.allowed_options.split(",") if o.strip()]

        return SettingResponse(
            id=setting.id,
            key=setting.key,
            group=setting.group,
            value=setting.value,
            value_type=setting.value_type,
            unit=setting.unit,
            min_value=setting.min_value,
            max_value=setting.max_value,
            allowed_options=options,
            help_text=setting.help_text,
            is_provisional=setting.is_provisional,
            updated_at=setting.updated_at,
        )

    def get_all_groups(self) -> list[SettingGroupResponse]:
        """Fetch all settings grouped by functional area."""
        settings = self.db.scalars(select(AppSetting).order_by(AppSetting.group, AppSetting.key)).all()
        grouped: dict[str, list[SettingResponse]] = {}
        for s in settings:
            grouped.setdefault(s.group, []).append(self._to_response(s))

        responses: list[SettingGroupResponse] = []
        for group_code, items in grouped.items():
            meta = GROUP_METADATA.get(group_code, {"title": group_code.title(), "description": None})
            responses.append(
                SettingGroupResponse(
                    group=group_code,
                    title=meta["title"],
                    description=meta["description"],
                    settings=items,
                )
            )
        return responses

    def list_settings(self, group: str | None = None, search: str | None = None) -> list[SettingResponse]:
        """Filter settings by group or search query."""
        query = select(AppSetting)
        if group:
            query = query.where(AppSetting.group == group.upper())
        if search:
            query = query.where(AppSetting.key.ilike(f"%{search.strip()}%"))

        settings = self.db.scalars(query.order_by(AppSetting.key)).all()
        return [self._to_response(s) for s in settings]

    def validate_setting_value(self, setting: AppSetting, value: str) -> None:
        """Server-side typed validation against value_type and min/max constraints."""
        vtype = setting.value_type.upper()
        clean_val = value.strip()

        if vtype == "BOOLEAN":
            if clean_val.lower() not in {"true", "false", "1", "0"}:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid value for '{setting.key}': Must be 'true' or 'false'.",
                )
        elif vtype == "INTEGER":
            try:
                num = int(clean_val)
                if setting.min_value is not None and num < setting.min_value:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Value for '{setting.key}' must be at least {int(setting.min_value)}.",
                    )
                if setting.max_value is not None and num > setting.max_value:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Value for '{setting.key}' cannot exceed {int(setting.max_value)}.",
                    )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid integer value for '{setting.key}'.",
                ) from None
        elif vtype == "DECIMAL":
            try:
                fnum = float(clean_val)
                if setting.min_value is not None and fnum < setting.min_value:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Value for '{setting.key}' must be at least {setting.min_value}.",
                    )
                if setting.max_value is not None and fnum > setting.max_value:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Value for '{setting.key}' cannot exceed {setting.max_value}.",
                    )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid decimal value for '{setting.key}'.",
                ) from None
        elif vtype == "TIME":
            if not re.match(r"^([01]\d|2[0-3]):[0-5]\d$", clean_val):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid time format for '{setting.key}'. Expected HH:MM (24-hour).",
                )
        elif vtype == "SELECT" and setting.allowed_options:
            try:
                allowed = json.loads(setting.allowed_options)
            except Exception:
                allowed = [o.strip() for o in setting.allowed_options.split(",") if o.strip()]
            if clean_val.upper() not in [str(o).upper() for o in allowed]:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Value '{value}' not allowed for '{setting.key}'. Options: {allowed}.",
                )

    def update_setting(self, key: str, value: str, user: User, reason: str | None = None) -> SettingResponse:
        """Update single setting with typed validation and audit trail."""
        setting = self.db.scalar(select(AppSetting).where(AppSetting.key == key))
        if not setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting '{key}' not found.",
            )

        self.validate_setting_value(setting, value)

        old_val = setting.value
        setting.value = value.strip()
        setting.is_provisional = False

        # Add history entry
        history = SettingHistory(
            key=key,
            old_value=old_val,
            new_value=setting.value,
            changed_by=user.id,
            change_summary=reason or f"Updated from {old_val} to {setting.value}",
        )
        self.db.add(history)

        # Record audit log
        AuditService.record(
            self.db,
            user_id=user.id,
            module="SETTINGS",
            action="UPDATE",
            entity_type="AppSetting",
            entity_id=key,
            summary=f"Setting '{key}' updated from '{old_val}' to '{setting.value}'",
            before={"key": key, "value": old_val},
            after={"key": key, "value": setting.value},
            channel="WEB",
        )

        self.db.commit()
        self.db.refresh(setting)
        self.invalidate_cache()
        return self._to_response(setting)

    def bulk_update(self, payload: SettingBulkUpdateRequest, user: User) -> list[SettingResponse]:
        """All-or-nothing transactional bulk update with per-key validation."""
        keys = [item.key for item in payload.settings]
        existing = {
            s.key: s
            for s in self.db.scalars(select(AppSetting).where(AppSetting.key.in_(keys))).all()
        }

        # 1. Validate all keys and types first
        for item in payload.settings:
            setting = existing.get(item.key)
            if not setting:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Setting key '{item.key}' not found.",
                )
            self.validate_setting_value(setting, item.value)

        # 2. Apply all mutations
        updated: list[AppSetting] = []
        for item in payload.settings:
            setting = existing[item.key]
            old_val = setting.value
            setting.value = item.value.strip()
            setting.is_provisional = False

            history = SettingHistory(
                key=setting.key,
                old_value=old_val,
                new_value=setting.value,
                changed_by=user.id,
                change_summary=payload.reason or "Bulk settings update",
            )
            self.db.add(history)
            updated.append(setting)

        AuditService.record(
            self.db,
            user_id=user.id,
            module="SETTINGS",
            action="UPDATE",
            entity_type="AppSetting",
            entity_id="BULK",
            summary=f"Bulk updated {len(updated)} settings: {', '.join(keys)}",
            channel="WEB",
        )

        self.db.commit()
        for s in updated:
            self.db.refresh(s)
        self.invalidate_cache()
        return [self._to_response(s) for s in updated]

    def confirm_setting(self, key: str, user: User) -> SettingResponse:
        """Mark provisional setting as formally confirmed."""
        setting = self.db.scalar(select(AppSetting).where(AppSetting.key == key))
        if not setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting '{key}' not found.",
            )

        setting.is_provisional = False
        AuditService.record(
            self.db,
            user_id=user.id,
            module="SETTINGS",
            action="CONFIRM",
            entity_type="AppSetting",
            entity_id=key,
            summary=f"Provisional setting '{key}' confirmed by {user.full_name}",
            channel="WEB",
        )
        self.db.commit()
        self.db.refresh(setting)
        self.invalidate_cache()
        return self._to_response(setting)

    def get_setting_history(self, key: str) -> list[SettingHistoryResponse]:
        """Fetch audit timeline for a specific setting."""
        records = (
            self.db.scalars(
                select(SettingHistory)
                .where(SettingHistory.key == key)
                .order_by(SettingHistory.created_at.desc())
            )
            .all()
        )
        return [
            SettingHistoryResponse(
                id=r.id,
                key=r.key,
                old_value=r.old_value,
                new_value=r.new_value,
                changed_by=r.changed_by,
                change_summary=r.change_summary,
                created_at=r.created_at,
            )
            for r in records
        ]

    # Geofence Settings
    def list_geofence_settings(self) -> list[GeofenceSettingResponse]:
        """List geofence rules across customer types."""
        settings = self.db.scalars(select(GeofenceSetting).order_by(GeofenceSetting.entity_type)).all()
        return [
            GeofenceSettingResponse(
                id=s.id,
                entity_type=s.entity_type,
                radius_m=s.radius_m,
                min_accuracy_m=s.min_accuracy_m,
                is_provisional=s.is_provisional,
                is_active=s.is_active,
                updated_at=s.updated_at,
            )
            for s in settings
        ]

    def update_geofence_settings(self, payload: GeofenceBulkUpdateRequest, user: User) -> list[GeofenceSettingResponse]:
        """Update geofence radius and accuracy rules."""
        results: list[GeofenceSetting] = []
        for item in payload.items:
            norm_type = item.entity_type.upper().strip()
            setting = self.db.scalar(
                select(GeofenceSetting).where(GeofenceSetting.entity_type == norm_type)
            )
            if not setting:
                setting = GeofenceSetting(
                    entity_type=norm_type,
                    radius_m=item.radius_m,
                    min_accuracy_m=item.min_accuracy_m,
                    is_provisional=item.is_provisional or False,
                )
                self.db.add(setting)
            else:
                old_radius = setting.radius_m
                setting.radius_m = item.radius_m
                setting.min_accuracy_m = item.min_accuracy_m
                if item.is_provisional is not None:
                    setting.is_provisional = item.is_provisional

                AuditService.record(
                    self.db,
                    user_id=user.id,
                    module="SETTINGS",
                    action="UPDATE",
                    entity_type="GeofenceSetting",
                    entity_id=norm_type,
                    summary=f"Geofence for {norm_type} updated from {old_radius}m to {item.radius_m}m",
                    before={"entity_type": norm_type, "radius_m": old_radius},
                    after={"entity_type": norm_type, "radius_m": item.radius_m},
                    channel="WEB",
                )
            results.append(setting)

        self.db.commit()
        for s in results:
            self.db.refresh(s)
        self.invalidate_cache()
        return [
            GeofenceSettingResponse(
                id=s.id,
                entity_type=s.entity_type,
                radius_m=s.radius_m,
                min_accuracy_m=s.min_accuracy_m,
                is_provisional=s.is_provisional,
                is_active=s.is_active,
                updated_at=s.updated_at,
            )
            for s in results
        ]
