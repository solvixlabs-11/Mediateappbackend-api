"""Tour Program SQLAlchemy ORM models."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import StandardAuditMixin, utc_now
from app.modules.users.models import User


class TourProgram(Base):
    """Monthly / Weekly Tour Program submitted by MR for Manager approval."""

    __tablename__ = "tour_programs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    total_days: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    route_details: Mapped[str | None] = mapped_column(String(255), nullable=True)
    objectives: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="SUBMITTED", nullable=False, index=True
    )  # DRAFT, SUBMITTED, APPROVED, REJECTED
    approval_request_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("approval_requests.id", ondelete="SET NULL"), nullable=True
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user: Mapped[User] = relationship("User", foreign_keys=[user_id])  # type: ignore # noqa: F821
    approval_request: Mapped[ApprovalRequest] = relationship(  # type: ignore # noqa: F821
        "ApprovalRequest", foreign_keys=[approval_request_id]
    )


class TourPlanLock(Base, StandardAuditMixin):
    """Cutoff lock on tour plan submissions by scope (ALL, TERRITORY, EMPLOYEE)."""

    __tablename__ = "tour_plan_locks"

    scope: Mapped[str] = mapped_column(String(50), nullable=False)  # ALL, TERRITORY, EMPLOYEE
    scope_id: Mapped[int | None] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), nullable=True
    )
    month: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-12
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    financial_year: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. '2026-2027'
    cutoff_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="LOCKED", nullable=False, index=True
    )  # LOCKED, UNLOCKED
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("users.id"),
        nullable=False,
    )
    unlocked_by_id: Mapped[int | None] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("users.id"),
        nullable=True,
    )
    unlocked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by_user: Mapped[User] = relationship("User", foreign_keys=[created_by_id])
    unlocked_by_user: Mapped[User | None] = relationship("User", foreign_keys=[unlocked_by_id])
