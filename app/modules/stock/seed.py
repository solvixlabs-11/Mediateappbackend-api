"""Seed realistic sample stock, inwards, allocations, and issues for development and demo."""

from __future__ import annotations

from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.modules.products.models import Product
from app.modules.stock.models import (
    SampleAllocation,
    SampleInward,
    SampleIssue,
    SampleLedger,
    SampleStock,
)
from app.modules.users.models import User


def seed_sample_stock(db: Session) -> dict[str, int]:
    """Seed sample inventory, inwards, allocations, and issues."""
    products = db.query(Product).filter(Product.is_active == True).limit(8).all()
    if not products:
        print("No products available to seed sample stock.")
        return {"inwards": 0, "stocks": 0, "allocations": 0, "issues": 0}

    users = db.query(User).all()
    if not users:
        print("No users available to seed sample stock.")
        return {"inwards": 0, "stocks": 0, "allocations": 0, "issues": 0}

    admin = users[0]
    mr_users = [u for u in users if u.role and u.role.code.upper() == "MR"] or users[:4]

    counts = {"inwards": 0, "stocks": 0, "allocations": 0, "issues": 0}
    today = date.today()

    # 1. Seed Sample Inwards and Stocks
    batches = [
        ("B26-001", today - timedelta(days=60), today + timedelta(days=500), 500, 15.50, "Sun Pharma Labs"),
        ("B26-002", today - timedelta(days=30), today + timedelta(days=360), 350, 22.00, "Cipla Formulation Unit"),
        ("B26-003", today - timedelta(days=15), today + timedelta(days=720), 800, 18.00, "Torrent Life Sciences"),
        ("B26-004", today - timedelta(days=5), today + timedelta(days=60), 200, 12.00, "Lupin Manufacturing"), # Near expiry (<=90d)
    ]

    for p_idx, product in enumerate(products):
        for b_idx, (b_code, mfg, exp, qty, cost, supplier) in enumerate(batches):
            challan_no = f"CHAL-2026-{p_idx+1:02d}-{b_idx+1:02d}"
            batch_num = f"{product.code[:4]}-{b_code}"

            # Check if inward exists
            existing_inward = (
                db.query(SampleInward)
                .filter(SampleInward.challan_number == challan_no)
                .first()
            )
            if not existing_inward:
                inward = SampleInward(
                    challan_number=challan_no,
                    inward_date=mfg + timedelta(days=10),
                    product_id=product.id,
                    batch_number=batch_num,
                    mfg_date=mfg,
                    expiry_date=exp,
                    quantity=qty,
                    unit_cost=cost,
                    supplier_name=supplier,
                    remarks="Quality QC inspection passed. Accepted into central warehouse depot.",
                    received_by_id=admin.id,
                    created_by=admin.id,
                )
                db.add(inward)
                counts["inwards"] += 1

            # Check/Update SampleStock
            stock = (
                db.query(SampleStock)
                .filter(
                    SampleStock.product_id == product.id,
                    SampleStock.batch_number == batch_num,
                )
                .first()
            )
            if not stock:
                stock = SampleStock(
                    product_id=product.id,
                    batch_number=batch_num,
                    mfg_date=mfg,
                    expiry_date=exp,
                    quantity_received=qty,
                    quantity_allocated=0,
                    quantity_issued=0,
                    quantity_balance=qty,
                    created_by=admin.id,
                )
                db.add(stock)
                counts["stocks"] += 1

    db.flush()

    # 2. Seed Monthly Sample Allocations for current month
    current_month = today.month
    current_year = today.year

    for mr in mr_users:
        for product in products[:5]:
            existing_alloc = (
                db.query(SampleAllocation)
                .filter(
                    SampleAllocation.user_id == mr.id,
                    SampleAllocation.product_id == product.id,
                    SampleAllocation.month == current_month,
                    SampleAllocation.year == current_year,
                )
                .first()
            )
            if not existing_alloc:
                target_quota = 50
                alloc = SampleAllocation(
                    user_id=mr.id,
                    product_id=product.id,
                    month=current_month,
                    year=current_year,
                    allocated_quantity=target_quota,
                    issued_quantity=0,
                    distributed_quantity=0,
                    balance_quantity=target_quota,
                    allocated_by_id=admin.id,
                    created_by=admin.id,
                )
                db.add(alloc)
                counts["allocations"] += 1

    db.flush()

    # 3. Seed Sample Issues to MRs
    for idx, mr in enumerate(mr_users):
        p = products[idx % len(products)]
        stock = (
            db.query(SampleStock)
            .filter(SampleStock.product_id == p.id, SampleStock.quantity_balance >= 20)
            .first()
        )
        if not stock:
            continue

        issue_num = f"ISS-{today.strftime('%Y%m%d')}-{idx+1:04d}"
        existing_issue = db.query(SampleIssue).filter(SampleIssue.issue_number == issue_num).first()
        if not existing_issue:
            issue_qty = 20
            issue = SampleIssue(
                issue_number=issue_num,
                issue_date=today - timedelta(days=idx * 2),
                user_id=mr.id,
                product_id=p.id,
                batch_number=stock.batch_number,
                quantity=issue_qty,
                dispatch_mode="COURIER",
                tracking_reference=f"BLUEDART-88992{idx}0",
                status="ACKNOWLEDGED" if idx % 2 == 0 else "DISPATCHED",
                received_date=today - timedelta(days=1) if idx % 2 == 0 else None,
                remarks="Monthly promotional doctor sampling kit.",
                issued_by_id=admin.id,
                created_by=admin.id,
            )
            db.add(issue)

            # Deduct stock
            stock.quantity_balance -= issue_qty
            stock.quantity_issued += issue_qty

            # Update allocation
            alloc = (
                db.query(SampleAllocation)
                .filter(
                    SampleAllocation.user_id == mr.id,
                    SampleAllocation.product_id == p.id,
                    SampleAllocation.month == current_month,
                    SampleAllocation.year == current_year,
                )
                .first()
            )
            if alloc:
                alloc.issued_quantity += issue_qty

            # Add Ledger
            ledger = SampleLedger(
                transaction_type="ISSUE",
                product_id=p.id,
                batch_number=stock.batch_number,
                user_id=mr.id,
                quantity=-issue_qty,
                balance_after=stock.quantity_balance,
                notes=f"Issued to {mr.full_name}",
                created_by=admin.id,
            )
            db.add(ledger)
            counts["issues"] += 1

    db.commit()
    print(f"Sample Stock Seeding completed: {counts}")
    return counts
