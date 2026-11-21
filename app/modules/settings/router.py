"""System Configuration & Geofence Settings REST API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.settings.schemas import (
    GeofenceBulkUpdateRequest,
    GeofenceSettingResponse,
    SettingBulkUpdateRequest,
    SettingGroupResponse,
    SettingHistoryResponse,
    SettingResponse,
    SettingUpdateRequest,
)
from app.modules.settings.service import SettingsService
from app.modules.users.models import User

router = APIRouter(prefix="/settings", tags=["System Configuration"])


def _check_settings_write_access(current_user: User) -> None:
    """Ensure user has admin privileges to modify settings."""
    if not current_user.role or current_user.role.code not in ["ADMIN", "ERP ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Modifying system settings requires Administrator privileges.",
        )


@router.get(
    "/groups",
    response_model=list[SettingGroupResponse],
    summary="Get all configuration groups with their settings and metadata",
)
def get_setting_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Fetch complete tree of system settings grouped by functional area."""
    service = SettingsService(db)
    return service.get_all_groups()


@router.get(
    "",
    response_model=list[SettingResponse],
    summary="List settings with optional group or search filter",
)
def list_settings(
    group: str | None = Query(default=None),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List matching application settings."""
    service = SettingsService(db)
    return service.list_settings(group=group, search=search)


@router.put(
    "/bulk",
    response_model=list[SettingResponse],
    summary="Bulk update multiple settings in a transaction",
)
def bulk_update_settings(
    payload: SettingBulkUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Transactional all-or-nothing bulk update of settings."""
    _check_settings_write_access(current_user)
    service = SettingsService(db)
    return service.bulk_update(payload, current_user)


# Geofence Endpoints (placed before /{key} to avoid path shadowing)
@router.get(
    "/geofence/rules",
    response_model=list[GeofenceSettingResponse],
    summary="List all geofence radius rules",
)
@router.get(
    "/geofence",
    response_model=list[GeofenceSettingResponse],
    summary="List all geofence radius rules (alias)",
)
def list_geofence_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Fetch geofence radii for Doctor, Hospital, Chemist, Stockist."""
    service = SettingsService(db)
    return service.list_geofence_settings()


@router.put(
    "/geofence",
    response_model=list[GeofenceSettingResponse],
    summary="Update geofence radius and accuracy rules",
)
def update_geofence_settings(
    payload: GeofenceBulkUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Update geofence rules per customer type."""
    _check_settings_write_access(current_user)
    service = SettingsService(db)
    return service.update_geofence_settings(payload, current_user)


@router.put(
    "/{key}",
    response_model=SettingResponse,
    summary="Update a single setting value",
)
def update_setting(
    key: str,
    payload: SettingUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Update single setting with typed server validation and audit trail."""
    _check_settings_write_access(current_user)
    service = SettingsService(db)
    return service.update_setting(key, payload.value, current_user, payload.reason)


@router.post(
    "/{key}/confirm",
    response_model=SettingResponse,
    summary="Confirm a provisional setting value",
)
def confirm_setting(
    key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Acknowledge and mark a provisional setting as confirmed."""
    _check_settings_write_access(current_user)
    service = SettingsService(db)
    return service.confirm_setting(key, current_user)


@router.get(
    "/{key}/history",
    response_model=list[SettingHistoryResponse],
    summary="Get change history timeline for a setting",
)
def get_setting_history(
    key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Fetch change audit history for a single setting."""
    service = SettingsService(db)
    return service.get_setting_history(key)
