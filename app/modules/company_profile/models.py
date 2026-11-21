"""Company Profile SQLAlchemy ORM model for Application Setting."""

from __future__ import annotations

from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import StandardAuditMixin


class CompanyProfile(Base, StandardAuditMixin):
    """Company profile and organizational identity entity."""

    __tablename__ = "company_profile"

    company_name: Mapped[str] = mapped_column(String(150), nullable=False)
    company_code: Mapped[str] = mapped_column(String(50), nullable=False)
    area: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pincode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    phone_no: Mapped[str | None] = mapped_column(String(50), nullable=True)
    mobile_no: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    website: Mapped[str | None] = mapped_column(String(100), nullable=True)
    logo_file_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    signature_file_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
