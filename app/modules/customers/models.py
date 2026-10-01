"""Customers (Hospitals, Doctors, Chemists, Stockists) SQLAlchemy ORM models."""

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import StandardAuditMixin

if TYPE_CHECKING:
    from app.modules.masters.models import Area
    from app.modules.territories.models import Territory


class Hospital(Base, StandardAuditMixin):
    """Hospital and medical institution customer."""

    __tablename__ = "hospitals"

    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), default="General", nullable=False)
    contact_person: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(25), nullable=True)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    area_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("areas.id", ondelete="SET NULL"), nullable=True, index=True
    )
    territory_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("territories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    bed_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    area: Mapped["Area | None"] = relationship("Area", lazy="joined")
    territory: Mapped["Territory | None"] = relationship("Territory", lazy="joined")
    hospital_doctors: Mapped[list["HospitalDoctor"]] = relationship(
        "HospitalDoctor", back_populates="hospital", cascade="all, delete-orphan"
    )


class HospitalDoctor(Base, StandardAuditMixin):
    """Many-to-many relationship mapping doctors to hospitals with primary flag."""

    __tablename__ = "hospital_doctors"

    hospital_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    doctor_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    visiting_hours: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (UniqueConstraint("hospital_id", "doctor_id", name="uq_hospital_doctor"),)

    hospital: Mapped[Hospital] = relationship("Hospital", back_populates="hospital_doctors")
    doctor: Mapped["Doctor"] = relationship("Doctor", back_populates="hospital_doctors")


class Doctor(Base, StandardAuditMixin):
    """Doctor customer entity."""

    __tablename__ = "doctors"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    qualification: Mapped[str | None] = mapped_column(String(100), nullable=True)
    specialization: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(50), default="A", nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(25), nullable=True)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    clinic_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    area_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("areas.id", ondelete="SET NULL"), nullable=True, index=True
    )
    territory_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("territories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    anniversary_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    area: Mapped["Area | None"] = relationship("Area", lazy="joined")
    territory: Mapped["Territory | None"] = relationship("Territory", lazy="joined")
    hospital_doctors: Mapped[list[HospitalDoctor]] = relationship(
        "HospitalDoctor", back_populates="doctor", cascade="all, delete-orphan"
    )


class Chemist(Base, StandardAuditMixin):
    """Chemist / Pharmacy customer entity."""

    __tablename__ = "chemists"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    shop_name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    contact_person: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(25), nullable=True)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dl_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    gstin: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    area_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("areas.id", ondelete="SET NULL"), nullable=True, index=True
    )
    territory_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("territories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    area: Mapped["Area | None"] = relationship("Area", lazy="joined")
    territory: Mapped["Territory | None"] = relationship("Territory", lazy="joined")


class Stockist(Base, StandardAuditMixin):
    """Stockist / Distributor customer entity."""

    __tablename__ = "stockists"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    agency_name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    contact_person: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(25), nullable=True)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dl_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    gstin: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    area_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("areas.id", ondelete="SET NULL"), nullable=True, index=True
    )
    territory_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("territories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    credit_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)

    area: Mapped["Area | None"] = relationship("Area", lazy="joined")
    territory: Mapped["Territory | None"] = relationship("Territory", lazy="joined")
