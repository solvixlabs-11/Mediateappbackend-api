"""SQLAlchemy ORM models for Sample Stock, Inwards, Allocations, Issues, and Ledger."""

from __future__ import annotations

from datetime import date
from sqlalchemy import (
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import StandardAuditMixin


class SampleStock(Base, StandardAuditMixin):
    """Head Office / Central Depot sample stock per product and batch."""

    __tablename__ = "sample_stocks"

    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    batch_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    mfg_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    quantity_received: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quantity_allocated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quantity_issued: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quantity_balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    product = relationship("Product", foreign_keys=[product_id])


class SampleInward(Base, StandardAuditMixin):
    """Inward receipt of promotional medical sample stock at Head Office."""

    __tablename__ = "sample_inwards"

    challan_number: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    inward_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    batch_number: Mapped[str] = mapped_column(String(50), nullable=False)
    mfg_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    supplier_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    received_by_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    product = relationship("Product", foreign_keys=[product_id])
    received_by = relationship("User", foreign_keys=[received_by_id])


class SampleAllocation(Base, StandardAuditMixin):
    """Monthly sample quota allocated to field representatives / managers."""

    __tablename__ = "sample_allocations"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    month: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    allocated_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    issued_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    distributed_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    balance_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    allocated_by_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    product = relationship("Product", foreign_keys=[product_id])
    allocated_by = relationship("User", foreign_keys=[allocated_by_id])


class SampleIssue(Base, StandardAuditMixin):
    """Physical dispatch and handover of samples from depot to field staff."""

    __tablename__ = "sample_issues"

    issue_number: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    issue_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    batch_number: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    dispatch_mode: Mapped[str] = mapped_column(String(50), default="COURIER", nullable=False)
    tracking_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="DISPATCHED", nullable=False)
    received_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    issued_by_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    product = relationship("Product", foreign_keys=[product_id])
    issued_by = relationship("User", foreign_keys=[issued_by_id])


class SampleLedger(Base, StandardAuditMixin):
    """Audit ledger tracking every sample stock debit and credit transaction."""

    __tablename__ = "sample_ledgers"

    transaction_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # INWARD, ALLOCATION, ISSUE, SAMPLE_DISTRIBUTED_DCR, ADJUSTMENT
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    batch_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    product = relationship("Product", foreign_keys=[product_id])
    user = relationship("User", foreign_keys=[user_id])
