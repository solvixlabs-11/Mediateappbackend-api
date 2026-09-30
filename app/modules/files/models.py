"""File metadata ORM model."""

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import StandardAuditMixin


class FileRecord(Base, StandardAuditMixin):
    """File metadata stored in database with payload in object/local storage."""

    __tablename__ = "files"

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_provider: Mapped[str] = mapped_column(String(50), default="local", nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    uploaded_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
