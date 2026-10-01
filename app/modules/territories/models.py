"""Territory and Area/User assignment SQLAlchemy ORM models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import StandardAuditMixin, utc_now

if TYPE_CHECKING:
    from app.modules.masters.models import Area, State
    from app.modules.users.models import User


class Territory(Base, StandardAuditMixin):
    """Territory representing field-force operational jurisdiction."""

    __tablename__ = "territories"

    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    headquarters: Mapped[str] = mapped_column(String(100), nullable=False)
    state_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("states.id", ondelete="SET NULL"), nullable=True, index=True
    )
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    state: Mapped["State | None"] = relationship("State", lazy="joined")
    areas: Mapped[list["Area"]] = relationship(
        "Area",
        secondary="territory_areas",
        lazy="selectin",
    )
    assignments: Mapped[list["UserTerritoryAssignment"]] = relationship(
        "UserTerritoryAssignment", back_populates="territory"
    )


class TerritoryArea(Base, StandardAuditMixin):
    """Many-to-many mapping between Territories and operational Areas."""

    __tablename__ = "territory_areas"

    territory_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("territories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    area_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("areas.id", ondelete="CASCADE"), nullable=False, index=True
    )


class UserTerritoryAssignment(Base, StandardAuditMixin):
    """User (MR or Manager) assignment to a Territory with history tracking."""

    __tablename__ = "user_territory_assignments"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    territory_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("territories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    unassigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    territory: Mapped[Territory] = relationship("Territory", back_populates="assignments")
    user: Mapped["User"] = relationship("User")
