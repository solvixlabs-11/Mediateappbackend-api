"""Meeting SQLAlchemy ORM model for cycle meetings & field review workflows."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import StandardAuditMixin


class Meeting(Base, StandardAuditMixin):
    """Cycle meetings, business reviews, and field training sessions."""

    __tablename__ = "meetings"

    agenda: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    meeting_type: Mapped[str] = mapped_column(
        String(50), default="CYCLE_MEETING", nullable=False, index=True
    )  # CYCLE_MEETING, BUSINESS_REVIEW, FIELD_TRAINING, ANNUAL_CONFERENCE
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_by_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    organiser_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="DRAFT", nullable=False, index=True
    )  # DRAFT, APPLIED, APPROVED, REJECTED, COMPLETED
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by_user: Mapped[User] = relationship(  # type: ignore # noqa: F821
        "User", foreign_keys=[created_by_id]
    )
    organiser_user: Mapped[User] = relationship(  # type: ignore # noqa: F821
        "User", foreign_keys=[organiser_id]
    )
