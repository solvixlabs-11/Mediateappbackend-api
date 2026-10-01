"""Attendance ORM models."""

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Attendance(Base):
    """Daily field attendance and check-in / check-out record."""

    __tablename__ = "attendances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(50), default="PRESENT", nullable=False
    )  # PRESENT, HALF_DAY, LEAVE, HOLIDAY

    # Check-in details
    check_in_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    check_in_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    check_in_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    check_in_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    check_in_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    check_in_mock_flag: Mapped[bool] = mapped_column(Boolean, default=False)

    # Check-out details
    check_out_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    check_out_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    check_out_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    check_out_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    check_out_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    check_out_mock_flag: Mapped[bool] = mapped_column(Boolean, default=False)

    total_work_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_uuid: Mapped[str | None] = mapped_column(
        String(64), unique=True, index=True, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])  # type: ignore # noqa: F821
