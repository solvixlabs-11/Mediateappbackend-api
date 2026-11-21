"""Seeder for Designation Expense Limits."""

from datetime import date
from sqlalchemy.orm import Session
from app.modules.expenses.models import ExpenseLimit
from app.modules.masters.models import MasterItem
from seed.base import SeedResult, load_json


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="expense_limits")
    data = load_json("expense_limits.json")

    # Cache designations and expense types IDs from master_items
    desigs = {
        m.code: m.id
        for m in session.query(MasterItem).filter(MasterItem.type == "DESIGNATION").all()
    }
    exp_types = {
        m.code: m.id
        for m in session.query(MasterItem).filter(MasterItem.type == "EXPENSE_TYPE").all()
    }

    effective_date = date(2026, 1, 1)

    for row in data:
        desig_code = row["designation_code"].upper()
        type_code = row["expense_type_code"].upper()

        existing = (
            session.query(ExpenseLimit)
            .filter(
                ExpenseLimit.designation_code == desig_code,
                ExpenseLimit.expense_type_code == type_code,
            )
            .first()
        )

        if existing:
            changed = False
            if existing.daily_limit != row["daily_limit"]:
                existing.daily_limit = row["daily_limit"]
                changed = True
            if existing.monthly_limit != row["monthly_limit"]:
                existing.monthly_limit = row["monthly_limit"]
                changed = True
            if existing.is_provisional != row.get("is_provisional", False):
                existing.is_provisional = row.get("is_provisional", False)
                changed = True
            if existing.designation_id != desigs.get(desig_code):
                existing.designation_id = desigs.get(desig_code)
                changed = True
            if existing.expense_type_id != exp_types.get(type_code):
                existing.expense_type_id = exp_types.get(type_code)
                changed = True
            if changed:
                result.updated += 1
            else:
                result.unchanged += 1
        else:
            item = ExpenseLimit(
                designation_id=desigs.get(desig_code),
                designation_code=desig_code,
                expense_type_id=exp_types.get(type_code),
                expense_type_code=type_code,
                daily_limit=row["daily_limit"],
                monthly_limit=row["monthly_limit"],
                effective_from=effective_date,
                is_provisional=row.get("is_provisional", True),
                is_active=True,
            )
            session.add(item)
            result.created += 1

    session.flush()
    return result
