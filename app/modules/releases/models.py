"""App Release & What's New SQLAlchemy ORM Model."""

from datetime import date
from sqlalchemy import Boolean, Date, String, UnicodeText
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import StandardAuditMixin


class AppRelease(Base, StandardAuditMixin):
    """Product release note & feature changelog."""

    __tablename__ = "app_releases"

    version: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    release_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    release_type: Mapped[str] = mapped_column(String(30), default="WEB_UPDATE", nullable=False)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    highlights_json: Mapped[str | None] = mapped_column(UnicodeText, nullable=True)
    target_audience: Mapped[str] = mapped_column(String(30), default="ALL", nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    apk_download_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
