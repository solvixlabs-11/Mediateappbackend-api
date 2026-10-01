"""Tour Program SQLAlchemy ORM models."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


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
