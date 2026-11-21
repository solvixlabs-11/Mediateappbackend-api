"""Expense Claims SQLAlchemy ORM models."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import StandardAuditMixin


class Expense(Base):
    """Daily field expense claim (DA/TA, Lodging, etc.) submitted for manager approval."""

    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    expense_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    expense_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # DAILY_ALLOWANCE, TRAVEL_FARE, LODGING, MISCELLANEOUS
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    receipt_file_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="SUBMITTED", nullable=False, index=True
    )  # SUBMITTED, APPROVED, REJECTED, PAID
    approval_request_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("approval_requests.id", ondelete="SET NULL"), nullable=True
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_uuid: Mapped[str | None] = mapped_column(
        String(64), unique=True, index=True, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user: Mapped[User] = relationship("User", foreign_keys=[user_id])  # type: ignore # noqa: F821
    approval_request: Mapped[ApprovalRequest] = relationship(  # type: ignore # noqa: F821
        "ApprovalRequest", foreign_keys=[approval_request_id]
    )
    payout: Mapped[ExpensePayout | None] = relationship("ExpensePayout", back_populates="expense", uselist=False)


class ExpensePayout(Base, StandardAuditMixin):
    """Reimbursement payout record for an approved expense claim."""

    __tablename__ = "expense_payouts"

    expense_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("expenses.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_mode: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_no: Mapped[str] = mapped_column(String(100), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    processed_by_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)
    remarks: Mapped[str | None] = mapped_column(String(255), nullable=True)

    expense: Mapped[Expense] = relationship("Expense", back_populates="payout")
    processed_by: Mapped[User] = relationship("User", foreign_keys=[processed_by_id])  # type: ignore # noqa: F821


class ExpenseLimit(Base, StandardAuditMixin):
    """Designation-wise daily and monthly claim limits per expense type."""

    __tablename__ = "expense_limits"

    designation_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    designation_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    expense_type_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    expense_type_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    daily_limit: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    monthly_limit: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    is_provisional: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "designation_code", "expense_type_code", "effective_from", name="uq_exp_limit"
        ),
    )
