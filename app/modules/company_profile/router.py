"""Company Profile REST API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.company_profile.schemas import (
    CompanyProfileResponse,
    CompanyProfileUpdateRequest,
)
from app.modules.company_profile.service import CompanyProfileService
from app.modules.users.models import User

router = APIRouter(prefix="/company-profile", tags=["Company Profile"])


def _check_admin(current_user: User) -> None:
    if not current_user.role or current_user.role.code not in ["ADMIN", "ERP ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Modifying company profile is restricted to administrators.",
        )


@router.get(
    "",
    response_model=CompanyProfileResponse,
    summary="Get active company profile and branding",
)
def get_company_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CompanyProfileResponse:
    """Fetch current organization profile (Application Setting)."""
    service = CompanyProfileService(db)
    return service.get_profile()


@router.put(
    "",
    response_model=CompanyProfileResponse,
    summary="Update company profile and branding assets",
)
def update_company_profile(
    payload: CompanyProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CompanyProfileResponse:
    """Update organization profile, logo, and signature (ADMIN only)."""
    _check_admin(current_user)
    service = CompanyProfileService(db)
    return service.update_profile(payload, current_user)
