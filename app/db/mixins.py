"""Standard audit and concurrency model mixins."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column


def utc_now() -> datetime:
    """Return current UTC timestamp with timezone."""
    return datetime.now(UTC)


class StandardAuditMixin:
    """Standard audit mixin specified by architecture section 5.1.

    Columns:
    - id: BIGINT identity primary key
    - client_uuid: nullable unique UUID for mobile-created records
    - created_at: UTC timestamp
    - updated_at: UTC timestamp
    - created_by: User ID reference (nullable for system)
    - updated_by: User ID reference (nullable)
    - is_active: Active state flag
    - is_deleted: Soft delete flag
    - row_version: Concurrency counter
    """

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )

    client_uuid: Mapped[str | None] = mapped_column(
        String(36),
        unique=True,
        nullable=True,
        index=True,
        default=lambda: str(uuid.uuid4()),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    row_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
