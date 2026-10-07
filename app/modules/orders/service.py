"""Order service layer implementing creation, calculation, and status transitions."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.scope import ScopeContext, get_accessible_user_ids
from app.modules.orders.models import Order, OrderItem
from app.modules.orders.repository import OrderRepository
from app.modules.orders.schemas import (
    OrderCreate,
    OrderItemResponse,
    OrderResponse,
)
from app.modules.products.models import Product


class OrderService:
    """Business operations for orders."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = OrderRepository(db)

    def _to_response(self, order: Order) -> OrderResponse:
        c_name = self.repo.get_customer_name(order.customer_type, order.customer_id)
        user_name = order.user.full_name or order.user.email if order.user else None

        items_resp: list[OrderItemResponse] = []
        for item in order.items or []:
            p_name = item.product.name if item.product else None
            p_code = item.product.code if item.product else None
            items_resp.append(
                OrderItemResponse(
                    id=item.id,
                    order_id=item.order_id,
                    product_id=item.product_id,
                    product_name=p_name,
                    product_code=p_code,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    total_price=item.total_price,
                    free_quantity=item.free_quantity,
                )
            )

        return OrderResponse(
            id=order.id,
            order_number=order.order_number,
            customer_type=order.customer_type,
            customer_id=order.customer_id,
            customer_name=c_name,
            user_id=order.user_id,
            user_name=user_name,
            total_amount=order.total_amount,
            status=order.status,
            expected_delivery_date=order.expected_delivery_date,
            payment_terms=order.payment_terms,
            notes=order.notes,
            items=items_resp,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )

    def list_orders(
        self,
        context: ScopeContext,
        customer_type: str | None = None,
        customer_id: int | None = None,
        status_filter: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[OrderResponse]:
        """List orders scoped to user."""
        accessible_ids = get_accessible_user_ids(context)
        orders = self.repo.list_orders(
            accessible_user_ids=list(accessible_ids) if accessible_ids is not None else None,
            customer_type=customer_type,
            customer_id=customer_id,
            status=status_filter,
            skip=skip,
            limit=limit,
        )
        return [self._to_response(o) for o in orders]

    def get_order(self, context: ScopeContext, order_id: int) -> OrderResponse:
        """Fetch single order by ID with scope validation."""
        order = self.repo.get_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found.",
            )

        accessible_ids = get_accessible_user_ids(context)
        if accessible_ids is not None and order.user_id not in accessible_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this order.",
            )

        return self._to_response(order)

    def create_order(self, context: ScopeContext, payload: OrderCreate) -> OrderResponse:
        """Create new order with line items."""
        now = datetime.utcnow()
        # Generate formatted order number
        order_num = f"ORD-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        total_amount = 0.0
        line_items: list[OrderItem] = []

        for item_in in payload.items:
            product = self.db.query(Product).filter(Product.id == item_in.product_id).first()
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product with ID {item_in.product_id} does not exist.",
                )
            line_total = round(item_in.quantity * item_in.unit_price, 2)
            total_amount += line_total

            line_items.append(
                OrderItem(
                    product_id=item_in.product_id,
                    quantity=item_in.quantity,
                    unit_price=item_in.unit_price,
                    total_price=line_total,
                    free_quantity=item_in.free_quantity,
                )
            )

        order = Order(
            order_number=order_num,
            customer_type=payload.customer_type.upper(),
            customer_id=payload.customer_id,
            user_id=context.user_id,
            total_amount=round(total_amount, 2),
            status="SUBMITTED",
            expected_delivery_date=payload.expected_delivery_date,
            payment_terms=payload.payment_terms,
            notes=payload.notes,
            created_at=now,
            updated_at=now,
            items=line_items,
        )

        self.db.add(order)
        self.db.commit()
        reloaded = self.repo.get_by_id(order.id)
        return self._to_response(reloaded or order)
