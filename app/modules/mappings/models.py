"""Employee Territory & Customer Mapping Wizard SQLAlchemy ORM models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import StandardAuditMixin


class MappingBatch(Base, StandardAuditMixin):
    """Bulk territory or customer mapping batch transaction."""

    __tablename__ = "mapping_batches"

    mode: Mapped[str] = mapped_column(String(30), nullable=False)  # TERRITORY or CUSTOMER
    status: Mapped[str] = mapped_column(
        String(30), default="DRAFT", nullable=False, index=True
    )  # DRAFT, APPLIED, REVERTED
    filters_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_employee_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    conflict_policy: Mapped[str] = mapped_column(
        String(20), default="SKIP", nullable=False
    )  # SKIP, REPLACE, ADD
    counts_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reverted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    items: Mapped[list[MappingBatchItem]] = relationship(
        "MappingBatchItem", back_populates="batch", cascade="all, delete-orphan"
    )


class MappingBatchItem(Base, StandardAuditMixin):
    """Individual assignment item belonging to a mapping batch."""

    __tablename__ = "mapping_batch_items"

    batch_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("mapping_batches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(30), nullable=False)  # ASSIGN or UNASSIGN
    employee_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    territory_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    customer_type: Mapped[str | None] = mapped_column(String(30), nullable=True)  # DOCTOR, CHEMIST, STOCKIST, HOSPITAL
    customer_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    before_state: Mapped[str | None] = mapped_column(Text, nullable=True)
    after_state: Mapped[str | None] = mapped_column(Text, nullable=True)

    batch: Mapped[MappingBatch] = relationship("MappingBatch", back_populates="items")
