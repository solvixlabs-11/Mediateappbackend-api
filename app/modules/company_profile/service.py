"""Company Profile business logic service."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.audit.service import AuditService
from app.modules.company_profile.models import CompanyProfile
from app.modules.company_profile.schemas import (
    CompanyProfileResponse,
    CompanyProfileUpdateRequest,
)
from app.modules.users.models import User


class CompanyProfileService:
    """Service handling company profile configuration."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def _to_response(self, profile: CompanyProfile) -> CompanyProfileResponse:
        logo_url = f"/api/v1/files/{profile.logo_file_id}/download" if profile.logo_file_id else None
        sig_url = f"/api/v1/files/{profile.signature_file_id}/download" if profile.signature_file_id else None

        return CompanyProfileResponse(
            id=profile.id,
            company_name=profile.company_name,
            company_code=profile.company_code,
            area=profile.area,
            address=profile.address,
            city=profile.city,
            state=profile.state,
            pincode=profile.pincode,
            phone_no=profile.phone_no,
            mobile_no=profile.mobile_no,
            email=profile.email,
            website=profile.website,
            logo_file_id=profile.logo_file_id,
            signature_file_id=profile.signature_file_id,
            logo_url=logo_url,
            signature_url=sig_url,
            is_active=profile.is_active,
            updated_at=profile.updated_at,
        )

    def get_profile(self) -> CompanyProfileResponse:
        """Fetch active company profile, auto-creating default if none exists."""
        profile = self.db.query(CompanyProfile).first()
        if not profile:
            profile = CompanyProfile(
                company_name="Mediate Healthcare Pvt. Ltd.",
                company_code="MED-HQ",
                area="Shivaji Nagar",
                address="Plot No. 42, Mediate Towers, Commercial Zone",
                city="Pune",
                state="Maharashtra",
                pincode="411005",
                phone_no="020-25531000",
                mobile_no="9876543210",
                email="contact@mediatepharma.com",
                website="https://www.mediatepharma.com",
            )
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)

        return self._to_response(profile)

    def update_profile(
        self, payload: CompanyProfileUpdateRequest, user: User
    ) -> CompanyProfileResponse:
        """Update company profile with audit trail."""
        profile = self.db.query(CompanyProfile).first()
        if not profile:
            profile = CompanyProfile(
                company_name=payload.company_name,
                company_code=payload.company_code,
            )
            self.db.add(profile)

        profile.company_name = payload.company_name
        profile.company_code = payload.company_code
        profile.area = payload.area
        profile.address = payload.address
        profile.city = payload.city
        profile.state = payload.state
        profile.pincode = payload.pincode
        profile.phone_no = payload.phone_no
        profile.mobile_no = payload.mobile_no
        profile.email = payload.email
        profile.website = payload.website
        if payload.logo_file_id is not None:
            profile.logo_file_id = payload.logo_file_id
        if payload.signature_file_id is not None:
            profile.signature_file_id = payload.signature_file_id
        profile.updated_by = user.id

        AuditService.record(
            self.db,
            user_id=user.id,
            module="SETTINGS",
            action="UPDATE",
            entity_type="CompanyProfile",
            entity_id=str(profile.id or 1),
            summary=f"Updated company profile ({payload.company_name}) by {user.full_name}",
            channel="WEB",
        )

        self.db.commit()
        self.db.refresh(profile)
        return self._to_response(profile)
