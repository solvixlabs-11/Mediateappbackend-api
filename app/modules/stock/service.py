"""Business logic service for Sample Inventory, Allocations, Issues, and Stock Ledger."""

from __future__ import annotations

import math
from datetime import date, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.modules.audit.service import AuditService
from app.modules.dcr.models import DcrProductDetail
from app.modules.products.models import Product
from app.modules.stock.models import (
    SampleAllocation,
    SampleInward,
    SampleIssue,
    SampleLedger,
    SampleStock,
)
from app.modules.stock.schemas import (
    SampleAllocationBulkCreate,
    SampleAllocationCreate,
    SampleAllocationListResponse,
    SampleAllocationResponse,
    SampleBatchResponse,
    SampleInwardCreate,
    SampleInwardListResponse,
    SampleInwardResponse,
    SampleIssueAcknowledgeRequest,
    SampleIssueCreate,
    SampleIssueListResponse,
    SampleIssueResponse,
    SampleStockBalanceResponse,
)
from app.modules.users.models import User

logger = get_logger(__name__)


class SampleStockService:
    """Service handling all sample inventory operations."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ==================== INWARD MANAGEMENT ====================

    def record_inward(
        self, payload: SampleInwardCreate, current_user: User
    ) -> SampleInwardResponse:
        """Inward new sample stock at Head Office and update central batch inventory."""
        # 1. Validate Product
        product = self.db.query(Product).filter(Product.id == payload.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {payload.product_id} not found",
            )

        # 2. Validate Expiry
        if payload.expiry_date <= date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sample expiry date must be in the future",
            )

        # 3. Check Duplicate Challan
        existing_challan = (
            self.db.query(SampleInward)
            .filter(SampleInward.challan_number == payload.challan_number)
            .first()
        )
        if existing_challan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Inward challan '{payload.challan_number}' has already been processed",
            )

        # 4. Create Inward Record
        inward = SampleInward(
            challan_number=payload.challan_number,
            inward_date=payload.inward_date,
            product_id=payload.product_id,
            batch_number=payload.batch_number.strip().upper(),
            mfg_date=payload.mfg_date,
            expiry_date=payload.expiry_date,
            quantity=payload.quantity,
            unit_cost=payload.unit_cost,
            supplier_name=payload.supplier_name,
            remarks=payload.remarks,
            received_by_id=current_user.id,
            created_by=current_user.id,
        )
        self.db.add(inward)

        # 5. Update or Create Batch Inventory in SampleStock
        stock = (
            self.db.query(SampleStock)
            .filter(
                SampleStock.product_id == payload.product_id,
                SampleStock.batch_number == payload.batch_number.strip().upper(),
            )
            .first()
        )
        if not stock:
            stock = SampleStock(
                product_id=payload.product_id,
                batch_number=payload.batch_number.strip().upper(),
                mfg_date=payload.mfg_date,
                expiry_date=payload.expiry_date,
                quantity_received=payload.quantity,
                quantity_allocated=0,
                quantity_issued=0,
                quantity_balance=payload.quantity,
                created_by=current_user.id,
            )
            self.db.add(stock)
        else:
            stock.quantity_received += payload.quantity
            stock.quantity_balance += payload.quantity
            stock.updated_at = datetime.utcnow()
            stock.updated_by = current_user.id

        self.db.flush()

        # 6. Record Audit Ledger
        ledger_entry = SampleLedger(
            transaction_type="INWARD",
            product_id=payload.product_id,
            batch_number=stock.batch_number,
            user_id=current_user.id,
            quantity=payload.quantity,
            balance_after=stock.quantity_balance,
            reference_id=inward.id,
            reference_type="SAMPLE_INWARD",
            notes=f"Challan #{inward.challan_number} received from {inward.supplier_name or 'Supplier'}",
            created_by=current_user.id,
        )
        self.db.add(ledger_entry)

        # 7. Audit Log
        AuditService.record(
            self.db,
            module="STOCK",
            action="SAMPLE_INWARD",
            user_id=current_user.id,
            summary=f"Inwarded {payload.quantity} units of {product.name} (Batch: {stock.batch_number})",
            details=f"Challan: {inward.challan_number}",
        )

        self.db.commit()
        self.db.refresh(inward)

        return SampleInwardResponse(
            id=inward.id,
            challan_number=inward.challan_number,
            inward_date=inward.inward_date,
            product_id=inward.product_id,
            product_name=product.name,
            product_code=product.code,
            batch_number=inward.batch_number,
            mfg_date=inward.mfg_date,
            expiry_date=inward.expiry_date,
            quantity=inward.quantity,
            unit_cost=inward.unit_cost,
            supplier_name=inward.supplier_name,
            remarks=inward.remarks,
            received_by_id=inward.received_by_id,
            received_by_name=current_user.full_name,
            created_at=inward.created_at,
        )

    def list_inwards(
        self,
        product_id: int | None = None,
        batch_number: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> SampleInwardListResponse:
        """List inward sample receipts with filters and pagination."""
        query = self.db.query(SampleInward).join(Product, SampleInward.product_id == Product.id)

        if product_id:
            query = query.filter(SampleInward.product_id == product_id)
        if batch_number:
            query = query.filter(SampleInward.batch_number.ilike(f"%{batch_number}%"))
        if search:
            query = query.filter(
                (SampleInward.challan_number.ilike(f"%{search}%"))
                | (Product.name.ilike(f"%{search}%"))
                | (SampleInward.batch_number.ilike(f"%{search}%"))
                | (SampleInward.supplier_name.ilike(f"%{search}%"))
            )

        total = query.count()
        total_pages = max(1, math.ceil(total / page_size))
        records = (
            query.order_by(SampleInward.inward_date.desc(), SampleInward.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        items = []
        for r in records:
            items.append(
                SampleInwardResponse(
                    id=r.id,
                    challan_number=r.challan_number,
                    inward_date=r.inward_date,
                    product_id=r.product_id,
                    product_name=r.product.name if r.product else None,
                    product_code=r.product.code if r.product else None,
                    batch_number=r.batch_number,
                    mfg_date=r.mfg_date,
                    expiry_date=r.expiry_date,
                    quantity=r.quantity,
                    unit_cost=r.unit_cost,
                    supplier_name=r.supplier_name,
                    remarks=r.remarks,
                    received_by_id=r.received_by_id,
                    received_by_name=r.received_by.full_name if r.received_by else None,
                    created_at=r.created_at,
                )
            )

        return SampleInwardListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    # ==================== ALLOCATION MANAGEMENT ====================

    def create_or_update_allocation(
        self, payload: SampleAllocationCreate, current_user: User
    ) -> SampleAllocationResponse:
        """Assign or update monthly sample quota for a field representative."""
        # 1. Validate User
        emp = self.db.query(User).filter(User.id == payload.user_id).first()
        if not emp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Field staff with ID {payload.user_id} not found",
            )

        # 2. Validate Product
        prod = self.db.query(Product).filter(Product.id == payload.product_id).first()
        if not prod:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {payload.product_id} not found",
            )

        # 3. Query existing or create
        alloc = (
            self.db.query(SampleAllocation)
            .filter(
                SampleAllocation.user_id == payload.user_id,
                SampleAllocation.product_id == payload.product_id,
                SampleAllocation.month == payload.month,
                SampleAllocation.year == payload.year,
            )
            .first()
        )

        if not alloc:
            alloc = SampleAllocation(
                user_id=payload.user_id,
                product_id=payload.product_id,
                month=payload.month,
                year=payload.year,
                allocated_quantity=payload.allocated_quantity,
                issued_quantity=0,
                distributed_quantity=0,
                balance_quantity=payload.allocated_quantity,
                allocated_by_id=current_user.id,
                created_by=current_user.id,
            )
            self.db.add(alloc)
        else:
            alloc.allocated_quantity = payload.allocated_quantity
            alloc.balance_quantity = max(0, alloc.allocated_quantity - alloc.distributed_quantity)
            alloc.allocated_by_id = current_user.id
            alloc.updated_at = datetime.utcnow()
            alloc.updated_by = current_user.id

        self.db.commit()
        self.db.refresh(alloc)

        return SampleAllocationResponse(
            id=alloc.id,
            user_id=alloc.user_id,
            user_name=emp.full_name,
            employee_code=f"EMP-{emp.id:04d}",
            product_id=alloc.product_id,
            product_name=prod.name,
            product_code=prod.code,
            month=alloc.month,
            year=alloc.year,
            allocated_quantity=alloc.allocated_quantity,
            issued_quantity=alloc.issued_quantity,
            distributed_quantity=alloc.distributed_quantity,
            balance_quantity=alloc.balance_quantity,
            allocated_by_name=current_user.full_name,
            created_at=alloc.created_at,
            updated_at=alloc.updated_at,
        )

    def bulk_allocate(
        self, payload: SampleAllocationBulkCreate, current_user: User
    ) -> dict[str, Any]:
        """Bulk create or update allocations across multiple representatives."""
        processed_count = 0
        for item in payload.allocations:
            alloc_item = SampleAllocationCreate(
                user_id=item.user_id,
                product_id=item.product_id,
                month=payload.month,
                year=payload.year,
                allocated_quantity=item.allocated_quantity,
            )
            self.create_or_update_allocation(alloc_item, current_user)
            processed_count += 1

        return {
            "success": True,
            "processed_count": processed_count,
            "month": payload.month,
            "year": payload.year,
        }

    def list_allocations(
        self,
        user_id: int | None = None,
        product_id: int | None = None,
        month: int | None = None,
        year: int | None = None,
        page: int = 1,
        page_size: int = 15,
    ) -> SampleAllocationListResponse:
        """List monthly sample allocations with filters and pagination."""
        query = self.db.query(SampleAllocation).join(User, SampleAllocation.user_id == User.id).join(
            Product, SampleAllocation.product_id == Product.id
        )

        if user_id:
            query = query.filter(SampleAllocation.user_id == user_id)
        if product_id:
            query = query.filter(SampleAllocation.product_id == product_id)
        if month:
            query = query.filter(SampleAllocation.month == month)
        if year:
            query = query.filter(SampleAllocation.year == year)

        total = query.count()
        total_pages = max(1, math.ceil(total / page_size))
        records = (
            query.order_by(
                SampleAllocation.year.desc(),
                SampleAllocation.month.desc(),
                SampleAllocation.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        items = []
        for r in records:
            items.append(
                SampleAllocationResponse(
                    id=r.id,
                    user_id=r.user_id,
                    user_name=r.user.full_name if r.user else None,
                    employee_code=f"EMP-{r.user_id:04d}",
                    product_id=r.product_id,
                    product_name=r.product.name if r.product else None,
                    product_code=r.product.code if r.product else None,
                    month=r.month,
                    year=r.year,
                    allocated_quantity=r.allocated_quantity,
                    issued_quantity=r.issued_quantity,
                    distributed_quantity=r.distributed_quantity,
                    balance_quantity=r.balance_quantity,
                    allocated_by_name=r.allocated_by.full_name if r.allocated_by else None,
                    created_at=r.created_at,
                    updated_at=r.updated_at,
                )
            )

        return SampleAllocationListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    # ==================== ISSUE MANAGEMENT ====================

    def create_issue(
        self, payload: SampleIssueCreate, current_user: User
    ) -> SampleIssueResponse:
        """Issue / dispatch samples from depot to field staff, deducting inventory."""
        # 1. Validate User
        emp = self.db.query(User).filter(User.id == payload.user_id).first()
        if not emp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipient user with ID {payload.user_id} not found",
            )

        # 2. Validate Product & Stock Balance
        stock = (
            self.db.query(SampleStock)
            .filter(
                SampleStock.product_id == payload.product_id,
                SampleStock.batch_number == payload.batch_number.strip().upper(),
            )
            .first()
        )
        if not stock:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No stock found for product #{payload.product_id} and batch {payload.batch_number}",
            )

        if stock.quantity_balance < payload.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient sample stock. Available balance is {stock.quantity_balance}, requested {payload.quantity}",
            )

        # 3. Generate Issue Number
        issue_date_str = date.today().strftime("%Y%m%d")
        seq_count = self.db.query(SampleIssue).count() + 1
        issue_number = f"ISS-{issue_date_str}-{seq_count:04d}"

        # 4. Create Issue Record
        issue = SampleIssue(
            issue_number=issue_number,
            issue_date=date.today(),
            user_id=payload.user_id,
            product_id=payload.product_id,
            batch_number=stock.batch_number,
            quantity=payload.quantity,
            dispatch_mode=payload.dispatch_mode,
            tracking_reference=payload.tracking_reference,
            status="DISPATCHED",
            remarks=payload.remarks,
            issued_by_id=current_user.id,
            created_by=current_user.id,
        )
        self.db.add(issue)

        # 5. Deduct Central Stock
        stock.quantity_balance -= payload.quantity
        stock.quantity_issued += payload.quantity
        stock.updated_at = datetime.utcnow()
        stock.updated_by = current_user.id

        # 6. Update Monthly Allocation if exists
        current_month = date.today().month
        current_year = date.today().year
        alloc = (
            self.db.query(SampleAllocation)
            .filter(
                SampleAllocation.user_id == payload.user_id,
                SampleAllocation.product_id == payload.product_id,
                SampleAllocation.month == current_month,
                SampleAllocation.year == current_year,
            )
            .first()
        )
        if alloc:
            alloc.issued_quantity += payload.quantity
            alloc.updated_at = datetime.utcnow()

        self.db.flush()

        # 7. Record Audit Ledger
        ledger = SampleLedger(
            transaction_type="ISSUE",
            product_id=payload.product_id,
            batch_number=stock.batch_number,
            user_id=payload.user_id,
            quantity=-payload.quantity,
            balance_after=stock.quantity_balance,
            reference_id=issue.id,
            reference_type="SAMPLE_ISSUE",
            notes=f"Issued to {emp.full_name} via {payload.dispatch_mode}",
            created_by=current_user.id,
        )
        self.db.add(ledger)

        # 8. Audit Log
        AuditService.record(
            self.db,
            module="STOCK",
            action="SAMPLE_ISSUE",
            user_id=current_user.id,
            summary=f"Issued {payload.quantity} units of {stock.product.name} to {emp.full_name}",
            details=f"Issue #{issue.issue_number}",
        )

        self.db.commit()
        self.db.refresh(issue)

        return SampleIssueResponse(
            id=issue.id,
            issue_number=issue.issue_number,
            issue_date=issue.issue_date,
            user_id=issue.user_id,
            user_name=emp.full_name,
            employee_code=f"EMP-{emp.id:04d}",
            product_id=issue.product_id,
            product_name=stock.product.name if stock.product else None,
            product_code=stock.product.code if stock.product else None,
            batch_number=issue.batch_number,
            quantity=issue.quantity,
            dispatch_mode=issue.dispatch_mode,
            tracking_reference=issue.tracking_reference,
            status=issue.status,
            received_date=issue.received_date,
            remarks=issue.remarks,
            issued_by_name=current_user.full_name,
            created_at=issue.created_at,
        )

    def acknowledge_issue(
        self, issue_id: int, payload: SampleIssueAcknowledgeRequest, current_user: User
    ) -> SampleIssueResponse:
        """Field representative confirms physical arrival and acknowledgment of samples."""
        issue = self.db.query(SampleIssue).filter(SampleIssue.id == issue_id).first()
        if not issue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sample issue with ID {issue_id} not found",
            )

        issue.status = "ACKNOWLEDGED"
        issue.received_date = payload.received_date
        if payload.remarks:
            issue.remarks = f"{issue.remarks or ''} | Acknowledgment: {payload.remarks}".strip(" | ")
        issue.updated_at = datetime.utcnow()
        issue.updated_by = current_user.id

        self.db.commit()
        self.db.refresh(issue)

        return SampleIssueResponse(
            id=issue.id,
            issue_number=issue.issue_number,
            issue_date=issue.issue_date,
            user_id=issue.user_id,
            user_name=issue.user.full_name if issue.user else None,
            employee_code=f"EMP-{issue.user_id:04d}",
            product_id=issue.product_id,
            product_name=issue.product.name if issue.product else None,
            product_code=issue.product.code if issue.product else None,
            batch_number=issue.batch_number,
            quantity=issue.quantity,
            dispatch_mode=issue.dispatch_mode,
            tracking_reference=issue.tracking_reference,
            status=issue.status,
            received_date=issue.received_date,
            remarks=issue.remarks,
            issued_by_name=issue.issued_by.full_name if issue.issued_by else None,
            created_at=issue.created_at,
        )

    def list_issues(
        self,
        user_id: int | None = None,
        product_id: int | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> SampleIssueListResponse:
        """List sample issues with filters and pagination."""
        query = self.db.query(SampleIssue).join(User, SampleIssue.user_id == User.id).join(
            Product, SampleIssue.product_id == Product.id
        )

        if user_id:
            query = query.filter(SampleIssue.user_id == user_id)
        if product_id:
            query = query.filter(SampleIssue.product_id == product_id)
        if status and status != "ALL":
            query = query.filter(SampleIssue.status == status)

        total = query.count()
        total_pages = max(1, math.ceil(total / page_size))
        records = (
            query.order_by(SampleIssue.issue_date.desc(), SampleIssue.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        items = []
        for r in records:
            items.append(
                SampleIssueResponse(
                    id=r.id,
                    issue_number=r.issue_number,
                    issue_date=r.issue_date,
                    user_id=r.user_id,
                    user_name=r.user.full_name if r.user else None,
                    employee_code=f"EMP-{r.user_id:04d}",
                    product_id=r.product_id,
                    product_name=r.product.name if r.product else None,
                    product_code=r.product.code if r.product else None,
                    batch_number=r.batch_number,
                    quantity=r.quantity,
                    dispatch_mode=r.dispatch_mode,
                    tracking_reference=r.tracking_reference,
                    status=r.status,
                    received_date=r.received_date,
                    remarks=r.remarks,
                    issued_by_name=r.issued_by.full_name if r.issued_by else None,
                    created_at=r.created_at,
                )
            )

        return SampleIssueListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    # ==================== BATCH & BALANCE REPORTS ====================

    def get_batches(self, product_id: int | None = None) -> list[SampleBatchResponse]:
        """List active sample batches with expiry status."""
        query = self.db.query(SampleStock).join(Product, SampleStock.product_id == Product.id)
        if product_id:
            query = query.filter(SampleStock.product_id == product_id)

        records = query.order_by(SampleStock.expiry_date.asc()).all()
        today = date.today()

        batches = []
        for r in records:
            days_left = (r.expiry_date - today).days
            if days_left < 0:
                exp_status = "EXPIRED"
            elif days_left <= 90:
                exp_status = "NEAR_EXPIRY"
            else:
                exp_status = "ACTIVE"

            batches.append(
                SampleBatchResponse(
                    id=r.id,
                    product_id=r.product_id,
                    product_name=r.product.name if r.product else None,
                    batch_number=r.batch_number,
                    mfg_date=r.mfg_date,
                    expiry_date=r.expiry_date,
                    quantity_received=r.quantity_received,
                    quantity_allocated=r.quantity_allocated,
                    quantity_issued=r.quantity_issued,
                    quantity_balance=r.quantity_balance,
                    days_to_expiry=days_left,
                    expiry_status=exp_status,
                )
            )
        return batches

    def get_sample_stock_balance_report(self) -> list[SampleStockBalanceResponse]:
        """Aggregate total sample stock balance across products."""
        products = self.db.query(Product).filter(Product.is_active == True).all()

        report_items = []
        for p in products:
            # HO balance
            ho_bal = (
                self.db.query(func.coalesce(func.sum(SampleStock.quantity_balance), 0))
                .filter(SampleStock.product_id == p.id)
                .scalar()
                or 0
            )

            # Total allocated
            tot_alloc = (
                self.db.query(func.coalesce(func.sum(SampleAllocation.allocated_quantity), 0))
                .filter(SampleAllocation.product_id == p.id)
                .scalar()
                or 0
            )

            # Total issued
            tot_issued = (
                self.db.query(func.coalesce(func.sum(SampleIssue.quantity), 0))
                .filter(SampleIssue.product_id == p.id)
                .scalar()
                or 0
            )

            # Total sampled in DCR visits
            tot_sampled_dcr = (
                self.db.query(func.coalesce(func.sum(DcrProductDetail.sample_quantity), 0))
                .filter(DcrProductDetail.product_name == p.name)
                .scalar()
                or 0
            )

            # Active batches
            batch_count = (
                self.db.query(func.count(SampleStock.id))
                .filter(SampleStock.product_id == p.id, SampleStock.quantity_balance > 0)
                .scalar()
                or 0
            )

            mr_holding = max(0, tot_issued - tot_sampled_dcr)

            report_items.append(
                SampleStockBalanceResponse(
                    product_id=p.id,
                    product_name=p.name,
                    product_code=p.code,
                    category=p.category,
                    packaging=p.packaging,
                    ho_balance=ho_bal,
                    total_allocated=tot_alloc,
                    total_issued=tot_issued,
                    total_sampled_dcr=tot_sampled_dcr,
                    mr_holding_balance=mr_holding,
                    active_batches_count=batch_count,
                )
            )

        return report_items
