"""Database repository for Products and Visual Aids."""

from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.modules.products.models import Product


class ProductRepository:
    """Handles CRUD queries for products catalog and visual aid detailing."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_products(
        self,
        category: str | None = None,
        search: str | None = None,
        is_sample_available: bool | None = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Product]:
        """Fetch products with filtering."""
        query = self.db.query(Product).options(selectinload(Product.visual_aids))
        if active_only:
            query = query.filter(Product.is_active == True)  # noqa: E712
        if category:
            query = query.filter(Product.category.ilike(category.strip()))
        if is_sample_available is not None:
            query = query.filter(Product.is_sample_available == is_sample_available)
        if search:
            pat = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Product.name.ilike(pat),
                    Product.code.ilike(pat),
                    Product.brand.ilike(pat),
                    Product.composition.ilike(pat),
                    Product.indications.ilike(pat),
                )
            )

        return (
            query.order_by(Product.category.asc(), Product.name.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_id(self, product_id: int) -> Product | None:
        """Fetch single product by ID."""
        return (
            self.db.query(Product)
            .options(selectinload(Product.visual_aids))
            .filter(Product.id == product_id)
            .first()
        )

    def get_by_code(self, code: str) -> Product | None:
        """Fetch by SKU code."""
        return self.db.query(Product).filter(Product.code == code).first()

    def list_categories(self) -> list[str]:
        """Get distinct product categories."""
        rows = (
            self.db.query(Product.category)
            .filter(Product.is_active == True)  # noqa: E712
            .distinct()
            .order_by(Product.category.asc())
            .all()
        )
        return [r[0] for r in rows if r[0]]
