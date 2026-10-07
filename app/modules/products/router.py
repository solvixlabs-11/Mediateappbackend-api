"""Product catalog and E-Detailing REST API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.products.schemas import (
    ProductCreate,
    ProductResponse,
    ProductVisualAidResponse,
    VisualAidCreate,
)
from app.modules.products.service import ProductService
from app.modules.users.models import User

router = APIRouter(prefix="/products", tags=["Products"])


@router.get(
    "/categories",
    response_model=list[str],
    summary="List available product therapy categories",
)
def get_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[str]:
    """Get distinct categories."""
    service = ProductService(db)
    return service.list_categories()


@router.get(
    "",
    response_model=list[ProductResponse],
    summary="List products with category and keyword search",
)
def list_products(
    category: str | None = Query(None, description="Therapy category filter"),
    search: str | None = Query(None, description="Search by name, composition, brand, or SKU"),
    is_sample_available: bool | None = Query(
        None, description="Filter products with samples available"
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ProductResponse]:
    """List products."""
    service = ProductService(db)
    return service.list_products(
        category=category,
        search=search,
        is_sample_available=is_sample_available,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get detailed product specs and visual aids",
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProductResponse:
    """Get single product with detailing visual aid slides."""
    service = ProductService(db)
    return service.get_product(product_id)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new pharmaceutical product",
)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProductResponse:
    """Create product."""
    service = ProductService(db)
    return service.create_product(payload)


@router.post(
    "/{product_id}/visual-aids",
    response_model=ProductVisualAidResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an E-Detailing visual aid slide to a product",
)
def add_visual_aid(
    product_id: int,
    payload: VisualAidCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProductVisualAidResponse:
    """Add visual aid slide."""
    service = ProductService(db)
    return service.add_visual_aid(product_id, payload)
