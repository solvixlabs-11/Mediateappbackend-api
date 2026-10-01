"""Daily Call Report (DCR), Pre-call Planning, Post-call Analysis, and Follow-up ORM models."""

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PlannedVisit(Base):
    """Pre-call planned visit for a customer."""

    __tablename__ = "planned_visits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plan_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    customer_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # DOCTOR, CHEMIST, HOSPITAL, STOCKIST

    doctor_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("doctors.id", ondelete="SET NULL"), nullable=True, index=True
    )
    chemist_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("chemists.id", ondelete="SET NULL"), nullable=True, index=True
    )
    hospital_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("hospitals.id", ondelete="SET NULL"), nullable=True, index=True
    )
    stockist_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("stockists.id", ondelete="SET NULL"), nullable=True, index=True
    )

    priority: Mapped[str] = mapped_column(String(50), default="MEDIUM")
    visit_purpose: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="PLANNED", index=True
    )  # PLANNED, COMPLETED, MISSED, CANCELLED
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_uuid: Mapped[str | None] = mapped_column(
        String(64), unique=True, index=True, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])  # type: ignore # noqa: F821
    doctor: Mapped["Doctor"] = relationship("Doctor", foreign_keys=[doctor_id])  # type: ignore # noqa: F821
    chemist: Mapped["Chemist"] = relationship("Chemist", foreign_keys=[chemist_id])  # type: ignore # noqa: F821
    hospital: Mapped["Hospital"] = relationship("Hospital", foreign_keys=[hospital_id])  # type: ignore # noqa: F821
    stockist: Mapped["Stockist"] = relationship("Stockist", foreign_keys=[stockist_id])  # type: ignore # noqa: F821


class DcrVisit(Base):
    """Daily Call Report visit record with geofencing and call details."""

    __tablename__ = "dcr_visits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dcr_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    customer_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # DOCTOR, CHEMIST, HOSPITAL, STOCKIST

    doctor_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("doctors.id", ondelete="SET NULL"), nullable=True, index=True
    )
    chemist_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("chemists.id", ondelete="SET NULL"), nullable=True, index=True
    )
    hospital_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("hospitals.id", ondelete="SET NULL"), nullable=True, index=True
    )
    stockist_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("stockists.id", ondelete="SET NULL"), nullable=True, index=True
    )
    planned_visit_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("planned_visits.id", ondelete="SET NULL"), nullable=True, index=True
    )

    visit_type: Mapped[str] = mapped_column(
        String(50), default="INDEPENDENT"
    )  # INDEPENDENT, JOINT_WITH_MANAGER, HOSPITAL_OPD
    joint_manager_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    call_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    call_duration_minutes: Mapped[int] = mapped_column(Integer, default=15)

    # GPS & Server Geofence fields (BR-04, BR-05, BR-13)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    distance_to_customer_meters: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_geofence_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    geofence_radius_meters: Mapped[float] = mapped_column(Float, default=200.0)
    is_mock_location: Mapped[bool] = mapped_column(Boolean, default=False)

    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    pob_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    status: Mapped[str] = mapped_column(
        String(50), default="SUBMITTED", index=True
    )  # DRAFT, SUBMITTED, APPROVED, REJECTED
    client_uuid: Mapped[str | None] = mapped_column(
        String(64), unique=True, index=True, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])  # type: ignore # noqa: F821
    doctor: Mapped["Doctor"] = relationship("Doctor", foreign_keys=[doctor_id])  # type: ignore # noqa: F821
    chemist: Mapped["Chemist"] = relationship("Chemist", foreign_keys=[chemist_id])  # type: ignore # noqa: F821
    hospital: Mapped["Hospital"] = relationship("Hospital", foreign_keys=[hospital_id])  # type: ignore # noqa: F821
    stockist: Mapped["Stockist"] = relationship("Stockist", foreign_keys=[stockist_id])  # type: ignore # noqa: F821
    post_call_analysis: Mapped["DcrPostCallAnalysis | None"] = relationship(
        "DcrPostCallAnalysis",
        back_populates="dcr_visit",
        uselist=False,
        cascade="all, delete-orphan",
    )
    product_details: Mapped[list["DcrProductDetail"]] = relationship(
        "DcrProductDetail", back_populates="dcr_visit", cascade="all, delete-orphan"
    )


class DcrPostCallAnalysis(Base):
    """Post-call analysis recording customer response, prescription commitment, and follow-up."""

    __tablename__ = "dcr_post_call_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dcr_visit_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dcr_visits.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    call_outcome: Mapped[str] = mapped_column(
        String(50), default="HIGHLY_INTERESTED"
    )  # HIGHLY_INTERESTED, MODERATE, NOT_INTERESTED, BUSY_RESCHEDULED
    doctor_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    prescription_commitment: Mapped[str] = mapped_column(
        String(50), default="HIGH"
    )  # HIGH, MEDIUM, LOW, NIL
    next_visit_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    follow_up_required: Mapped[bool] = mapped_column(Boolean, default=False)
    follow_up_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    dcr_visit: Mapped["DcrVisit"] = relationship("DcrVisit", back_populates="post_call_analysis")


class DcrProductDetail(Base):
    """Placeholder table for promoted products and sample / gift allocation lines."""

    __tablename__ = "dcr_product_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dcr_visit_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dcr_visits.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_name: Mapped[str] = mapped_column(String(150), nullable=False)
    sample_quantity: Mapped[int] = mapped_column(Integer, default=0)
    gift_quantity: Mapped[int] = mapped_column(Integer, default=0)
    remarks: Mapped[str | None] = mapped_column(String(255), nullable=True)

    dcr_visit: Mapped["DcrVisit"] = relationship("DcrVisit", back_populates="product_details")


class FollowUp(Base):
    """Actionable customer follow-up task and reminder."""

    __tablename__ = "follow_ups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    customer_type: Mapped[str] = mapped_column(String(50), nullable=False)

    doctor_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("doctors.id", ondelete="SET NULL"), nullable=True, index=True
    )
    chemist_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("chemists.id", ondelete="SET NULL"), nullable=True, index=True
    )
    hospital_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("hospitals.id", ondelete="SET NULL"), nullable=True, index=True
    )
    stockist_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("stockists.id", ondelete="SET NULL"), nullable=True, index=True
    )
    dcr_visit_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("dcr_visits.id", ondelete="SET NULL"), nullable=True
    )

    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(50), default="MEDIUM")
    status: Mapped[str] = mapped_column(
        String(50), default="PENDING", index=True
    )  # PENDING, COMPLETED, OVERDUE, CANCELLED
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    client_uuid: Mapped[str | None] = mapped_column(
        String(64), unique=True, index=True, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])  # type: ignore # noqa: F821
    doctor: Mapped["Doctor"] = relationship("Doctor", foreign_keys=[doctor_id])  # type: ignore # noqa: F821
    chemist: Mapped["Chemist"] = relationship("Chemist", foreign_keys=[chemist_id])  # type: ignore # noqa: F821
    hospital: Mapped["Hospital"] = relationship("Hospital", foreign_keys=[hospital_id])  # type: ignore # noqa: F821
    stockist: Mapped["Stockist"] = relationship("Stockist", foreign_keys=[stockist_id])  # type: ignore # noqa: F821
