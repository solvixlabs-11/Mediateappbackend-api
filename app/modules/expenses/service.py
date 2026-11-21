"""Expense Claims business logic service."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.approvals.repository import ApprovalRepository
from app.modules.audit.service import AuditService
from app.modules.expenses.models import Expense, ExpenseLimit, ExpensePayout
from app.modules.expenses.repository import ExpenseRepository
from app.modules.expenses.schemas import (
    ExpenseCreateRequest,
    ExpenseLimitBulkUpsertRequest,
    ExpenseLimitMatrixCell,
    ExpenseLimitMatrixResponse,
    ExpenseLimitMatrixRow,
    ExpenseLimitResponse,
    ExpensePayoutRequest,
    ExpenseResponse,
    MonthlyExpenseSummaryResponse,
)
from app.modules.masters.models import MasterItem
from app.modules.settings.service import SettingsService
from app.modules.users.models import User


class ExpenseService:
    """Service handling daily field expense claims and approval creation."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ExpenseRepository(db)
        self.approval_repo = ApprovalRepository(db)

    def _to_response(self, exp: Expense) -> ExpenseResponse:
        return ExpenseResponse(
            id=exp.id,
            user_id=exp.user_id,
            user_name=exp.user.full_name if exp.user else None,
            expense_date=exp.expense_date,
            expense_type=exp.expense_type,
            amount=exp.amount,
            description=exp.description,
            receipt_file_id=exp.receipt_file_id,
            status=exp.status,
            approval_request_id=exp.approval_request_id,
            rejection_reason=exp.rejection_reason,
            created_at=exp.created_at,
            updated_at=exp.updated_at,
        )

    def create_expense(self, payload: ExpenseCreateRequest, user: User) -> ExpenseResponse:
        """Create and submit an expense claim with idempotency support (BR-12)."""
        # Idempotency check with client_uuid
        if payload.client_uuid:
            existing = self.repo.get_by_client_uuid(payload.client_uuid)
            if existing:
                return self._to_response(existing)

        if payload.amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Expense amount must be greater than zero.",
            )

        # Limit enforcement checks via SettingsService
        settings_svc = SettingsService(self.db)
        enforcement_mode = settings_svc.get_setting_value("expense.limit_enforcement", "WARN").upper().strip()
        description_text = payload.description or ""

        # Determine user's designation code from role or master
        designation_code = user.role.code if user.role else "MR"
        norm_exp_type = payload.expense_type.upper().strip()

        # Fetch effective limit
        limit_record = self.db.scalar(
            select(ExpenseLimit).where(
                ExpenseLimit.designation_code == designation_code,
                ExpenseLimit.expense_type_code == norm_exp_type,
            )
        )

        warning_flags = []
        if limit_record and enforcement_mode != "OFF":
            # 1. Daily limit check
            if limit_record.daily_limit > 0 and payload.amount > limit_record.daily_limit:
                msg = f"Claim of ₹{payload.amount:,.2f} exceeds daily limit of ₹{limit_record.daily_limit:,.2f} for {designation_code} ({norm_exp_type})."
                if enforcement_mode == "BLOCK":
                    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)
                warning_flags.append(f"[LIMIT_WARN: Exceeds daily limit ₹{limit_record.daily_limit:,.2f}]")

            # 2. Monthly limit check
            if limit_record.monthly_limit > 0:
                month_start = payload.expense_date.replace(day=1)
                existing_month_total = (
                    self.db.scalar(
                        select(func.coalesce(func.sum(Expense.amount), 0.0)).where(
                            Expense.user_id == user.id,
                            Expense.expense_type == payload.expense_type,
                            Expense.expense_date >= month_start,
                            Expense.expense_date <= payload.expense_date,
                            Expense.status != "REJECTED",
                        )
                    )
                    or 0.0
                )
                if (existing_month_total + payload.amount) > limit_record.monthly_limit:
                    msg = f"Monthly total ₹{existing_month_total + payload.amount:,.2f} exceeds monthly limit of ₹{limit_record.monthly_limit:,.2f} for {designation_code}."
                    if enforcement_mode == "BLOCK":
                        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)
                    warning_flags.append(f"[LIMIT_WARN: Exceeds monthly limit ₹{limit_record.monthly_limit:,.2f}]")

        if warning_flags:
            description_text = f"{description_text} {' '.join(warning_flags)}".strip()

        exp = self.repo.create(
            user_id=user.id,
            expense_date=payload.expense_date,
            expense_type=payload.expense_type,
            amount=payload.amount,
            description=description_text,
            receipt_file_id=payload.receipt_file_id,
            client_uuid=payload.client_uuid,
        )

        # Dispatch approval request into the manager's inbox
        approval_req = self.approval_repo.create_request(
            entity_type="EXPENSE",
            entity_id=exp.id,
            requester_id=user.id,
            title=f"Expense: ₹{exp.amount:,.2f} - {exp.expense_type.replace('_', ' ')}",
            details=f"Date: {exp.expense_date}. Description: {exp.description or 'N/A'}.",
        )
        exp.approval_request_id = approval_req.id

        self.db.commit()
        self.db.refresh(exp)
        return self._to_response(exp)

    def list_expenses(
        self,
        current_user: User,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[ExpenseResponse]:
        """List expenses scoped to role."""
        role_code = current_user.role.code if current_user.role else "MR"
        user_id = None if role_code in ("ADMIN", "MANAGER") else current_user.id
        expenses = self.repo.list_expenses(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )
        return [self._to_response(e) for e in expenses]

    def get_monthly_summary(
        self,
        current_user: User,
        year: int | None = None,
        month: int | None = None,
    ) -> MonthlyExpenseSummaryResponse:
        """Fetch monthly expense total and claim breakdown."""
        today = date.today()
        target_year = year or today.year
        target_month = month or today.month

        summary_dict = self.repo.get_monthly_summary(
            user_id=current_user.id,
            year=target_year,
            month=target_month,
        )
        return MonthlyExpenseSummaryResponse(**summary_dict)  # type: ignore[arg-type]

    # Expense Limits Matrix Methods
    def list_limits(
        self,
        designation_id: int | None = None,
        expense_type_id: int | None = None,
    ) -> list[ExpenseLimitResponse]:
        """List expense limits with optional filters."""
        query = select(ExpenseLimit)
        if designation_id is not None:
            query = query.where(ExpenseLimit.designation_id == designation_id)
        if expense_type_id is not None:
            query = query.where(ExpenseLimit.expense_type_id == expense_type_id)

        limits = self.db.scalars(
            query.order_by(ExpenseLimit.designation_code, ExpenseLimit.expense_type_code)
        ).all()
        return [
            ExpenseLimitResponse(
                id=lim_item.id,
                designation_id=lim_item.designation_id,
                designation_code=lim_item.designation_code,
                expense_type_id=lim_item.expense_type_id,
                expense_type_code=lim_item.expense_type_code,
                daily_limit=lim_item.daily_limit,
                monthly_limit=lim_item.monthly_limit,
                effective_from=lim_item.effective_from,
                is_provisional=lim_item.is_provisional,
                updated_at=lim_item.updated_at,
            )
            for lim_item in limits
        ]

    def get_limits_matrix(self) -> ExpenseLimitMatrixResponse:
        """Construct full matrix of all designations x all expense types."""
        # 1. Fetch designations from MasterItem
        designation_items = self.db.scalars(
            select(MasterItem)
            .where(
                MasterItem.type == "DESIGNATION",
                MasterItem.is_active == True,  # noqa: E712
                MasterItem.is_deleted == False,  # noqa: E712
            )
            .order_by(MasterItem.sort_order, MasterItem.name)
        ).all()
        desigs = [{"code": d.code, "name": d.name} for d in designation_items]

        # 2. Fetch standard expense types
        exp_types = [
            {"code": "DAILY_ALLOWANCE", "name": "Daily Allowance (DA)"},
            {"code": "TRAVEL_FARE", "name": "Travel / Fare (TA)"},
            {"code": "LODGING", "name": "Hotel / Lodging"},
            {"code": "MISCELLANEOUS", "name": "Miscellaneous"},
        ]

        # 3. Fetch all current limits
        limits = self.db.scalars(select(ExpenseLimit)).all()
        limit_map = {(entry.designation_code, entry.expense_type_code): entry for entry in limits}

        rows: list[ExpenseLimitMatrixRow] = []
        for d in desigs:
            cells: dict[str, ExpenseLimitMatrixCell] = {}
            for et in exp_types:
                lim = limit_map.get((d["code"], et["code"]))
                if lim:
                    cells[et["code"]] = ExpenseLimitMatrixCell(
                        id=lim.id,
                        daily_limit=lim.daily_limit,
                        monthly_limit=lim.monthly_limit,
                        is_provisional=lim.is_provisional,
                    )
                else:
                    cells[et["code"]] = ExpenseLimitMatrixCell(
                        id=None,
                        daily_limit=0.0,
                        monthly_limit=0.0,
                        is_provisional=True,
                    )
            rows.append(
                ExpenseLimitMatrixRow(
                    designation_code=d["code"],
                    designation_name=d["name"],
                    limits=cells,
                )
            )

        return ExpenseLimitMatrixResponse(
            designations=desigs,
            expense_types=exp_types,
            rows=rows,
        )

    def bulk_upsert_limits(
        self,
        payload: ExpenseLimitBulkUpsertRequest,
        user: User,
    ) -> list[ExpenseLimitResponse]:
        """Upsert matrix of expense limits with server validation."""
        results: list[ExpenseLimit] = []
        today = date.today()

        for item in payload.items:
            if item.daily_limit < 0 or item.monthly_limit < 0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Limit amounts cannot be negative.",
                )
            if item.monthly_limit > 0 and item.daily_limit > item.monthly_limit:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Daily limit (₹{item.daily_limit}) cannot exceed monthly limit (₹{item.monthly_limit}) for {item.designation_code} - {item.expense_type_code}.",
                )

            eff_date = item.effective_from or today
            existing = self.db.scalar(
                select(ExpenseLimit).where(
                    ExpenseLimit.designation_code == item.designation_code,
                    ExpenseLimit.expense_type_code == item.expense_type_code,
                )
            )

            if existing:
                existing.daily_limit = item.daily_limit
                existing.monthly_limit = item.monthly_limit
                existing.effective_from = eff_date
                if item.is_provisional is not None:
                    existing.is_provisional = item.is_provisional
                results.append(existing)
            else:
                new_lim = ExpenseLimit(
                    designation_code=item.designation_code,
                    expense_type_code=item.expense_type_code,
                    daily_limit=item.daily_limit,
                    monthly_limit=item.monthly_limit,
                    effective_from=eff_date,
                    is_provisional=item.is_provisional if item.is_provisional is not None else False,
                )
                self.db.add(new_lim)
                results.append(new_lim)

        AuditService.record(
            self.db,
            user_id=user.id,
            module="EXPENSE",
            action="UPDATE",
            entity_type="ExpenseLimit",
            entity_id="MATRIX",
            summary=f"Bulk upserted {len(payload.items)} expense limits",
            channel="WEB",
        )

        self.db.commit()
        for r in results:
            self.db.refresh(r)

        return [
            ExpenseLimitResponse(
                id=item_lim.id,
                designation_id=item_lim.designation_id,
                designation_code=item_lim.designation_code,
                expense_type_id=item_lim.expense_type_id,
                expense_type_code=item_lim.expense_type_code,
                daily_limit=item_lim.daily_limit,
                monthly_limit=item_lim.monthly_limit,
                effective_from=item_lim.effective_from,
                is_provisional=item_lim.is_provisional,
                updated_at=item_lim.updated_at,
            )
            for item_lim in results
        ]

    def confirm_limit(self, limit_id: int, user: User) -> ExpenseLimitResponse:
        """Mark a provisional expense limit as formally confirmed."""
        limit = self.db.scalar(select(ExpenseLimit).where(ExpenseLimit.id == limit_id))
        if not limit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Expense limit with ID {limit_id} not found.",
            )

        limit.is_provisional = False
        AuditService.record(
            self.db,
            user_id=user.id,
            module="EXPENSE",
            action="CONFIRM",
            entity_type="ExpenseLimit",
            entity_id=str(limit_id),
            summary=f"Provisional expense limit for {limit.designation_code} - {limit.expense_type_code} confirmed by {user.full_name}",
            channel="WEB",
        )
        self.db.commit()
        self.db.refresh(limit)
        return ExpenseLimitResponse(
            id=limit.id,
            designation_id=limit.designation_id,
            designation_code=limit.designation_code,
            expense_type_id=limit.expense_type_id,
            expense_type_code=limit.expense_type_code,
            daily_limit=limit.daily_limit,
            monthly_limit=limit.monthly_limit,
            effective_from=limit.effective_from,
            is_provisional=limit.is_provisional,
            updated_at=limit.updated_at,
        )

    def process_payout(
        self, expense_id: int, payload: ExpensePayoutRequest, user: User
    ) -> ExpenseResponse:
        settings_svc = SettingsService(self.db)
        is_payout_enabled = str(
            settings_svc.get_setting_value("reimbursement.payout_enabled", "true")
        ).lower() in ["true", "1", "yes"]
        if not is_payout_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reimbursement payout is currently disabled by system settings.",
            )

        exp = self.db.query(Expense).filter(Expense.id == expense_id).first()
        if not exp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Expense with ID {expense_id} not found.",
            )

        # Check existing payout on this expense or by idempotency key
        existing_payout = (
            self.db.query(ExpensePayout)
            .filter(ExpensePayout.expense_id == expense_id)
            .first()
        )
        if not existing_payout and payload.idempotency_key:
            existing_payout = (
                self.db.query(ExpensePayout)
                .filter(ExpensePayout.idempotency_key == payload.idempotency_key)
                .first()
            )

        if existing_payout:
            # Idempotent return - do not post second payout
            return self._to_response(exp)

        if exp.status != "APPROVED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only APPROVED expenses can be paid out. Current status: {exp.status}",
            )

        mode = (payload.payment_mode or "NEFT").upper().strip()
        allowed_modes = ["NEFT", "RTGS", "UPI", "CHEQUE", "CASH"]
        if mode not in allowed_modes:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid payment mode '{mode}'. Allowed modes: {allowed_modes}",
            )

        if mode != "CASH" and not (payload.reference_no and payload.reference_no.strip()):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="UTR / Reference number is required for non-cash payment modes.",
            )

        payout = ExpensePayout(
            expense_id=exp.id,
            amount=Decimal(str(exp.amount)),
            payment_mode=mode,
            reference_no=payload.reference_no.strip() if payload.reference_no else "CASH",
            payment_date=payload.payment_date or date.today(),
            processed_by_id=user.id,
            idempotency_key=payload.idempotency_key,
            remarks=payload.remarks,
        )
        self.db.add(payout)

        exp.status = "PAID"
        payout_note = f"Settled via {mode} | Ref: {payout.reference_no} on {payout.payment_date}"
        if payload.remarks:
            payout_note += f" | {payload.remarks}"
        exp.rejection_reason = payout_note

        AuditService.record(
            self.db,
            user_id=user.id,
            module="REIMBURSEMENT",
            action="PAYOUT",
            entity_type="Expense",
            entity_id=str(expense_id),
            summary=f"Reimbursement claim #{expense_id} (₹{exp.amount:,.2f}) marked as PAID by {user.full_name}: {payout_note}",
            channel="WEB",
        )
        self.db.commit()
        self.db.refresh(exp)
        return self._to_response(exp)
