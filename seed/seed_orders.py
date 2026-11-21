
"""Seeder for Commercial Orders and Invoicing (80+ records across Chemists & Stockists)."""

import uuid
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from app.modules.customers.models import Chemist, Stockist
from app.modules.orders.models import Order, OrderItem
from app.modules.products.models import Product
from app.modules.users.models import User, Role
from seed.base import SeedResult


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="orders")
    if not dev:
        return result

    mr_role = session.query(Role).filter(Role.code == "MR").first()
    if mr_role:
        users = session.query(User).filter(User.role_id == mr_role.id).all()
    else:
        users = session.query(User).all()
    if not users:
        return result

    chemists = session.query(Chemist).filter(Chemist.is_deleted == False).all()  # noqa: E712
    stockists = session.query(Stockist).filter(Stockist.is_deleted == False).all()  # noqa: E712
    products = session.query(Product).filter(Product.is_active == True).all()  # noqa: E712

    if not products:
        return result

    today = date.today()
    now = datetime.utcnow()

    payment_terms_options = [
        "Net 30 Days",
        "Net 15 Days",
        "Cash on Delivery",
        "Immediate Advance",
        "Weekly Credit Cycle",
    ]
    statuses = ["SUBMITTED", "CONFIRMED", "DISPATCHED", "DELIVERED"]

    # 1. Seed 40 Chemist Secondary Orders
    for idx in range(min(40, len(chemists))):
        chm = chemists[idx]
        user = users[idx % len(users)]
        day_offset = idx % 10
        order_date = today - timedelta(days=day_offset)
        order_num = f"ORD-CHM-2026-{String_pad(idx + 1)}"
        status_val = statuses[idx % len(statuses)]

        existing = session.query(Order).filter(Order.order_number == order_num).first()
        if existing:
            result.unchanged += 1
            continue

        num_items = 2 + (idx % 3)  # 2 to 4 items
        line_items = []
        total_amount = 0.0

        for item_idx in range(num_items):
            prod = products[(idx * 3 + item_idx) % len(products)]
            qty = 5 * (item_idx + 1) + (idx % 10)
            u_price = float(prod.mrp or 120.0) * 0.7  # 30% trade discount
            line_total = round(qty * u_price, 2)
            free_qty = 1 if qty >= 20 else 0
            total_amount += line_total

            line_items.append(
                OrderItem(
                    product_id=prod.id,
                    quantity=qty,
                    unit_price=round(u_price, 2),
                    total_price=line_total,
                    free_quantity=free_qty,
                )
            )

        order = Order(
            order_number=order_num,
            customer_type="CHEMIST",
            customer_id=chm.id,
            user_id=user.id,
            total_amount=round(total_amount, 2),
            status=status_val,
            expected_delivery_date=order_date + timedelta(days=3),
            payment_terms=payment_terms_options[idx % len(payment_terms_options)],
            notes=f"Secondary prescription booking taken at {chm.shop_name} by {user.full_name}.",
            created_at=datetime(order_date.year, order_date.month, order_date.day, 10 + (idx % 7), 15),
            updated_at=now,
            items=line_items,
        )
        session.add(order)
        result.created += 1

    # 2. Seed 40 Stockist Primary Orders
    for idx in range(min(40, len(stockists))):
        stk = stockists[idx]
        user = users[(idx + 5) % len(users)]
        day_offset = idx % 12
        order_date = today - timedelta(days=day_offset)
        order_num = f"ORD-STK-2026-{String_pad(idx + 1)}"
        status_val = statuses[(idx + 1) % len(statuses)]

        existing = session.query(Order).filter(Order.order_number == order_num).first()
        if existing:
            result.unchanged += 1
            continue

        num_items = 3 + (idx % 3)  # 3 to 5 bulk items
        line_items = []
        total_amount = 0.0

        for item_idx in range(num_items):
            prod = products[(idx * 4 + item_idx) % len(products)]
            qty = 50 * (item_idx + 1) + (idx * 5)
            u_price = float(prod.mrp or 120.0) * 0.6  # 40% wholesale discount
            line_total = round(qty * u_price, 2)
            free_qty = (qty // 50) * 2  # Scheme 50+2 free
            total_amount += line_total

            line_items.append(
                OrderItem(
                    product_id=prod.id,
                    quantity=qty,
                    unit_price=round(u_price, 2),
                    total_price=line_total,
                    free_quantity=free_qty,
                )
            )

        order = Order(
            order_number=order_num,
            customer_type="STOCKIST",
            customer_id=stk.id,
            user_id=user.id,
            total_amount=round(total_amount, 2),
            status=status_val,
            expected_delivery_date=order_date + timedelta(days=5),
            payment_terms=payment_terms_options[(idx + 2) % len(payment_terms_options)],
            notes=f"Primary wholesale replenishment order booked for {stk.agency_name}.",
            created_at=datetime(order_date.year, order_date.month, order_date.day, 11 + (idx % 6), 30),
            updated_at=now,
            items=line_items,
        )
        session.add(order)
        result.created += 1

    session.flush()
    return result


def String_pad(n: int) -> str:
    return str(n).zfill(4)
