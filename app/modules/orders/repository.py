"""Database repository for Commercial Orders."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session, joinedload, selectinload

from app.modules.customers.models import Chemist, Stockist
from app.modules.orders.models import Order, OrderItem


class OrderRepository:
    """Handles CRUD queries for orders."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_orders(
        self,
        accessible_user_ids: list[int] | None = None,
        customer_type: str | None = None,
        customer_id: int | None = None,
        status: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Order]:
        """Fetch orders with hierarchy scoping."""
        query = self.db.query(Order).options(
            joinedload(Order.user),
            selectinload(Order.items).joinedload(OrderItem.product),
        )
        if accessible_user_ids is not None:
            query = query.filter(Order.user_id.in_(accessible_user_ids))
        if customer_type:
            query = query.filter(Order.customer_type == customer_type.upper())
        if customer_id:
            query = query.filter(Order.customer_id == customer_id)
        if status:
            query = query.filter(Order.status == status.upper())
        if start_date:
            query = query.filter(Order.created_at >= start_date)
        if end_date:
            query = query.filter(Order.created_at <= end_date)

        return query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()

    def get_by_id(self, order_id: int) -> Order | None:
        """Fetch single order by ID with items and products."""
        return (
            self.db.query(Order)
            .options(
                joinedload(Order.user),
                selectinload(Order.items).joinedload(OrderItem.product),
            )
            .filter(Order.id == order_id)
            .first()
        )

    def get_customer_name(self, customer_type: str, customer_id: int) -> str | None:
        """Fetch pharmacy or agency name."""
        if customer_type.upper() == "CHEMIST":
            chm = self.db.query(Chemist).filter(Chemist.id == customer_id).first()
            return chm.shop_name if chm else None
        elif customer_type.upper() == "STOCKIST":
            stk = self.db.query(Stockist).filter(Stockist.id == customer_id).first()
            return stk.agency_name if stk else None
        return None

    def update_status(self, order_id: int, new_status: str, notes: str | None = None) -> Order | None:
        """Update status of an order."""
        order = self.get_by_id(order_id)
        if not order:
            return None
        order.status = new_status.upper()
        if notes:
            order.notes = f"{order.notes or ''}\n[Status Update]: {notes}".strip()
        self.db.commit()
        self.db.refresh(order)
        return order

    def get_orders_summary(self, accessible_user_ids: list[int] | None = None) -> dict:
        """Calculate KPI summary across orders."""
        query = self.db.query(Order)
        if accessible_user_ids is not None:
            query = query.filter(Order.user_id.in_(accessible_user_ids))
        orders = query.all()

        chemist_orders = [o for o in orders if o.customer_type == "CHEMIST"]
        stockist_orders = [o for o in orders if o.customer_type == "STOCKIST"]

        return {
            "total_orders": len(orders),
            "total_amount": round(sum(o.total_amount for o in orders), 2),
            "chemist_orders_count": len(chemist_orders),
            "chemist_orders_amount": round(sum(o.total_amount for o in chemist_orders), 2),
            "stockist_orders_count": len(stockist_orders),
            "stockist_orders_amount": round(sum(o.total_amount for o in stockist_orders), 2),
            "submitted_count": len([o for o in orders if o.status == "SUBMITTED"]),
            "confirmed_count": len([o for o in orders if o.status == "CONFIRMED"]),
            "dispatched_count": len([o for o in orders if o.status == "DISPATCHED"]),
            "delivered_count": len([o for o in orders if o.status == "DELIVERED"]),
        }
