"""SQLAlchemy ORM models for Pharmaceutical Products and E-Detailing Visual Aids."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Product(Base):
    """Pharmaceutical product / SKU entity."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    brand: Mapped[str] = mapped_column(
        String(100), default="Mediate Pharma", nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    composition: Mapped[str | None] = mapped_column(Text, nullable=True)
    strength: Mapped[str | None] = mapped_column(String(100), nullable=True)
    packaging: Mapped[str] = mapped_column(String(100), default="10x10 Tablets", nullable=False)
    mrp: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    ptr: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    pts: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    gst_rate: Mapped[float] = mapped_column(Float, default=12.0, nullable=False)
    indications: Mapped[str | None] = mapped_column(Text, nullable=True)
    dosage_guidelines: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_sample_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    visual_aids: Mapped[list[ProductVisualAid]] = relationship(
        "ProductVisualAid",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductVisualAid.slide_order.asc()",
    )


class ProductVisualAid(Base):
    """Digital E-Detailing presentation slide and talk track."""

    __tablename__ = "product_visual_aids"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    slide_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    key_talk_points: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    product: Mapped[Product] = relationship("Product", back_populates="visual_aids")
