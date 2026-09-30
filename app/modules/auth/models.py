"""Authentication and session ORM models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import StandardAuditMixin

if TYPE_CHECKING:
    from app.modules.users.models import User


class RefreshToken(Base, StandardAuditMixin):
    """Persisted refresh tokens with rotation and token family support."""

    __tablename__ = "refresh_tokens"

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    family_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    replaced_by_token_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    user: Mapped[User] = relationship("User", back_populates="refresh_tokens")
