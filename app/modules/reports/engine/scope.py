"""Scope enforcement helper for reports using core/scope.py."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from app.core.scope import ScopeContext, UserRole


def validate_report_scope(
    context: ScopeContext,
    filters: dict[str, Any],
) -> tuple[list[int] | None, str]:
    """Validate requested employee/territory filters against the caller's scope.

    Returns:
        tuple of (allowed_user_ids, scope_label)
    Raises:
        HTTPException(403) with code REPORT_SCOPE_DENIED if any requested employee is outside scope.
    """
    # 1. MR Scope (Self only)
    if context.role == UserRole.MR:
        # Check single employee
        req_emp = filters.get("employee")
        if req_emp is not None and str(req_emp) != str(context.user_id):
            raise HTTPException(
                status_code=403,
                detail=f"Requested employee ID {req_emp} is outside your assigned scope",
                headers={"X-Error-Code": "REPORT_SCOPE_DENIED"},
            )
        # Check multi-select employees
        req_emps = filters.get("employees")
        if req_emps and isinstance(req_emps, list):
            for emp_id in req_emps:
                if str(emp_id) != str(context.user_id):
                    raise HTTPException(
                        status_code=403,
                        detail=f"Employee ID {emp_id} is outside your assigned scope",
                        headers={"X-Error-Code": "REPORT_SCOPE_DENIED"},
                    )
        return [context.user_id], "Self (Own Territory)"

    # 2. MANAGER Scope (Team only)
    if context.role == UserRole.MANAGER:
        allowed_team = {context.user_id, *context.team_member_ids}
        allowed_team_str = {str(uid) for uid in allowed_team}

        req_emp = filters.get("employee")
        if req_emp is not None and str(req_emp) not in allowed_team_str:
            raise HTTPException(
                status_code=403,
                detail=f"Requested employee ID {req_emp} is outside your assigned team",
                headers={"X-Error-Code": "REPORT_SCOPE_DENIED"},
            )

        req_emps = filters.get("employees")
        if req_emps and isinstance(req_emps, list) and len(req_emps) > 0:
            for emp_id in req_emps:
                if str(emp_id) not in allowed_team_str:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Employee ID {emp_id} is outside your assigned team",
                        headers={"X-Error-Code": "REPORT_SCOPE_DENIED"},
                    )
            return [int(x) for x in req_emps], f"Selected ({len(req_emps)} team members)"

        if req_emp is not None:
            return [int(req_emp)], f"Employee #{req_emp}"

        return list(allowed_team), f"Your assigned team ({len(context.team_member_ids)} MRs)"

    # 3. ADMIN Scope (All)
    req_emp = filters.get("employee")
    req_emps = filters.get("employees")

    if req_emps and isinstance(req_emps, list) and len(req_emps) > 0:
        return [int(x) for x in req_emps], f"Selected ({len(req_emps)} employees)"

    if req_emp is not None:
        return [int(req_emp)], f"Employee #{req_emp}"

    return None, "All Zones & Representatives"
