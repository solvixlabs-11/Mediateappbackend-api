"""Target ORM model."""

from sqlalchemy import BigInteger, ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import StandardAuditMixin


class Target(Base, StandardAuditMixin):
    """Monthly performance targets assigned to MRs."""

    __tablename__ = "targets"

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    month: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    visit_target: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    doctor_call_target: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    chemist_call_target: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    primary_sales_target: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    secondary_sales_target: Mapped[float] = mapped_column(
        Numeric(12, 2), default=0.0, nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "year", "month", name="uq_target_user_year_month"),
    )
