"""Product service layer."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.products.models import Product, ProductVisualAid
from app.modules.products.repository import ProductRepository
from app.modules.products.schemas import (
    ProductCreate,
    ProductResponse,
    ProductVisualAidResponse,
    VisualAidCreate,
)


class ProductService:
    """Business operations for product catalog and e-detailing."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProductRepository(db)

    def _to_response(self, product: Product) -> ProductResponse:
        v_aids = [
            ProductVisualAidResponse(
                id=va.id,
                product_id=va.product_id,
                title=va.title,
                image_url=va.image_url,
                slide_order=va.slide_order,
                key_talk_points=va.key_talk_points,
                created_at=va.created_at,
            )
            for va in (product.visual_aids or [])
        ]

        return ProductResponse(
            id=product.id,
            code=product.code,
            name=product.name,
            brand=product.brand,
            category=product.category,
            composition=product.composition,
            strength=product.strength,
            packaging=product.packaging,
            mrp=product.mrp,
            ptr=product.ptr,
            pts=product.pts,
            gst_rate=product.gst_rate,
            indications=product.indications,
            dosage_guidelines=product.dosage_guidelines,
            is_sample_available=product.is_sample_available,
            is_active=product.is_active,
            visual_aids=v_aids,
            created_at=product.created_at,
            updated_at=product.updated_at,
        )

    def list_products(
        self,
        category: str | None = None,
        search: str | None = None,
        is_sample_available: bool | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ProductResponse]:
        """List products."""
        items = self.repo.list_products(
            category=category,
            search=search,
            is_sample_available=is_sample_available,
            skip=skip,
            limit=limit,
        )
        return [self._to_response(p) for p in items]

    def get_product(self, product_id: int) -> ProductResponse:
        """Get product detail."""
        product = self.repo.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found.",
            )
        return self._to_response(product)

    def list_categories(self) -> list[str]:
        """List all available categories."""
        return self.repo.list_categories()

    def create_product(self, payload: ProductCreate) -> ProductResponse:
        """Create a new product."""
        existing = self.repo.get_by_code(payload.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with code '{payload.code}' already exists.",
            )

        product = Product(
            code=payload.code.strip().upper(),
            name=payload.name.strip(),
            brand=payload.brand.strip(),
            category=payload.category.strip(),
            composition=payload.composition.strip() if payload.composition else None,
            strength=payload.strength.strip() if payload.strength else None,
            packaging=payload.packaging.strip(),
            mrp=payload.mrp,
            ptr=payload.ptr,
            pts=payload.pts,
            gst_rate=payload.gst_rate,
            indications=payload.indications.strip() if payload.indications else None,
            dosage_guidelines=payload.dosage_guidelines.strip()
            if payload.dosage_guidelines
            else None,
            is_sample_available=payload.is_sample_available,
            is_active=True,
        )
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return self._to_response(product)

    def add_visual_aid(self, product_id: int, payload: VisualAidCreate) -> ProductVisualAidResponse:
        """Add visual aid slide to product."""
        product = self.repo.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found.",
            )

        aid = ProductVisualAid(
            product_id=product.id,
            title=payload.title.strip(),
            image_url=payload.image_url,
            slide_order=payload.slide_order,
            key_talk_points=payload.key_talk_points.strip() if payload.key_talk_points else None,
        )
        self.db.add(aid)
        self.db.commit()
        self.db.refresh(aid)
        return ProductVisualAidResponse(
            id=aid.id,
            product_id=aid.product_id,
            title=aid.title,
            image_url=aid.image_url,
            slide_order=aid.slide_order,
            key_talk_points=aid.key_talk_points,
            created_at=aid.created_at,
        )
