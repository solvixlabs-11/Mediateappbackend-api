"""Orders REST API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.orders.schemas import OrderCreate, OrderResponse
from app.modules.orders.service import OrderService
from app.modules.users.models import User
from app.modules.users.service import UserService

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get(
    "",
    response_model=list[OrderResponse],
    summary="List booked orders with scoping and filters",
)
def list_orders(
    customer_type: str | None = Query(None, description="CHEMIST or STOCKIST"),
    customer_id: int | None = Query(None, description="Specific customer ID"),
    status: str | None = Query(None, description="SUBMITTED, CONFIRMED, DELIVERED, CANCELLED"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[OrderResponse]:
    """List orders."""
    scope = UserService(db).get_user_scope_context(current_user)
    service = OrderService(db)
    return service.list_orders(
        context=scope,
        customer_type=customer_type,
        customer_id=customer_id,
        status_filter=status,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order details with line items",
)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrderResponse:
    """Get single order."""
    scope = UserService(db).get_user_scope_context(current_user)
    service = OrderService(db)
    return service.get_order(scope, order_id)


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Book a new commercial order",
)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrderResponse:
    """Create order."""
    scope = UserService(db).get_user_scope_context(current_user)
    service = OrderService(db)
    return service.create_order(scope, payload)
