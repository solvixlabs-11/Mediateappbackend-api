"""Financial Year SQLAlchemy ORM Model."""

from datetime import date
from sqlalchemy import Boolean, Date, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import StandardAuditMixin


class FinancialYear(Base, StandardAuditMixin):
    """Corporate Financial Year definition (e.g. 2024-2025, 2025-2026)."""

    __tablename__ = "financial_years"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
