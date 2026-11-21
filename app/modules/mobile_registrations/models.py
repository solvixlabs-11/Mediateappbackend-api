"""Mobile registration models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import StandardAuditMixin, utc_now
from app.modules.users.models import User


class MobileRegistration(Base, StandardAuditMixin):
    """Mobile device registration request by an employee."""

    __tablename__ = "mobile_registrations"

    registration_code: Mapped[str] = mapped_column(String(100), nullable=False)
    employee_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    designation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    territory: Mapped[str | None] = mapped_column(String(100), nullable=True)
    device_id_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    device_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    app_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="PENDING", nullable=False, index=True
    )  # PENDING, APPROVED, REJECTED
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    decided_by_id: Mapped[int | None] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    employee: Mapped[User] = relationship("User", foreign_keys=[employee_id])
    decided_by: Mapped[User | None] = relationship("User", foreign_keys=[decided_by_id])
