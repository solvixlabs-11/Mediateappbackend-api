"""Master data SQLAlchemy ORM models."""

from sqlalchemy import BigInteger, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import StandardAuditMixin


class MasterItem(Base, StandardAuditMixin):
    """Generic business master item (Specializations, Categories, Priorities, etc.)."""

    __tablename__ = "master_items"

    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (UniqueConstraint("type", "code", name="uq_master_items_type_code"),)


class State(Base, StandardAuditMixin):
    """State / Province entity."""

    __tablename__ = "states"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)

    cities: Mapped[list["City"]] = relationship(
        "City", back_populates="state", cascade="all, delete-orphan"
    )


class City(Base, StandardAuditMixin):
    """City / District entity under a State."""

    __tablename__ = "cities"

    state_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("states.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    code: Mapped[str | None] = mapped_column(String(10), nullable=True)

    state: Mapped[State] = relationship("State", back_populates="cities")
    areas: Mapped[list["Area"]] = relationship(
        "Area", back_populates="city", cascade="all, delete-orphan"
    )


class Area(Base, StandardAuditMixin):
    """Locality / Area under a City."""

    __tablename__ = "areas"

    city_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)

    city: Mapped[City] = relationship("City", back_populates="areas")
