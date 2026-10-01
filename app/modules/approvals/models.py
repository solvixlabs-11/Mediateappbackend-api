"""Approval engine SQLAlchemy ORM models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ApprovalRequest(Base):
    """Generic approval tracking for Tour Programs, Expenses, and Leaves."""

    __tablename__ = "approval_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # TOUR, EXPENSE, LEAVE
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    requester_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), default="PENDING", nullable=False, index=True
    )  # PENDING, APPROVED, REJECTED, CANCELLED
    current_step: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    total_steps: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    requester: Mapped[User] = relationship("User", foreign_keys=[requester_id])  # type: ignore # noqa: F821
    history: Mapped[list[ApprovalHistory]] = relationship(
        "ApprovalHistory", back_populates="request", cascade="all, delete-orphan"
    )


class ApprovalHistory(Base):
    """Audit log of each approval or rejection action."""

    __tablename__ = "approval_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    request_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("approval_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    approver_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    decision: Mapped[str] = mapped_column(String(50), nullable=False)  # APPROVED, REJECTED
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    request: Mapped[ApprovalRequest] = relationship("ApprovalRequest", back_populates="history")
    approver: Mapped[User] = relationship("User", foreign_keys=[approver_id])  # type: ignore # noqa: F821
