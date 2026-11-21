"""Workflow Inbox business service.

Provides dynamic 3-tile counts (Drafts, Applied, Received) and scoped list
queries for Leaves, Tour Plans, and New Customer Approvals.
"""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.core.scope import ScopeContext, UserRole, get_accessible_user_ids
from app.modules.approvals.models import ApprovalRequest
from app.modules.customers.models import Chemist, Doctor, Stockist
from app.modules.expenses.models import Expense
from app.modules.leaves.models import LeaveRequest
from app.modules.tours.models import TourProgram
from app.modules.users.models import ManagerMRAssignment, User
from app.modules.workflow.schemas import WorkflowItemResponse, WorkflowSummaryResponse


class WorkflowService:
    """Service providing dynamic 3-tile workflow data."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_team_user_ids(self, current_user: User) -> list[int]:
        """Fetch accessible user IDs based on manager assignments."""
        role_code = current_user.role.code if current_user.role else "MR"
        if role_code == "ADMIN":
            return []  # Empty means all in admin mode

        assignments = (
            self.db.query(ManagerMRAssignment)
            .filter(
                ManagerMRAssignment.manager_id == current_user.id,
                ManagerMRAssignment.unassigned_at.is_(None),
                ManagerMRAssignment.is_deleted == False,  # noqa: E712
            )
            .all()
        )
        return [a.mr_id for a in assignments]

    # -------------------------------------------------------------------------
    # SUMMARY COUNTS (Dynamic Tile counts)
    # -------------------------------------------------------------------------
    def get_summary(self, module: str, current_user: User) -> WorkflowSummaryResponse:
        """Calculate dynamic counts for drafts, applied, and received tiles."""
        norm_mod = module.lower().replace("_", "-")
        role_code = current_user.role.code if current_user.role else "MR"
        team_ids = self._get_team_user_ids(current_user)

        if norm_mod in ("leaves", "leave"):
            # Leaves
            drafts = (
                self.db.query(LeaveRequest)
                .filter(
                    LeaveRequest.user_id == current_user.id,
                    LeaveRequest.status.in_(["DRAFT", "CANCELLED"]),
                )
                .count()
            )
            applied = (
                self.db.query(LeaveRequest)
                .filter(
                    LeaveRequest.user_id == current_user.id,
                    LeaveRequest.status.in_(["PENDING", "APPROVED", "REJECTED"]),
                )
                .count()
            )
            rec_q = self.db.query(LeaveRequest).filter(
                LeaveRequest.status == "PENDING",
            )
            if role_code == "MANAGER":
                rec_q = rec_q.filter(LeaveRequest.user_id.in_(team_ids))
            elif role_code != "ADMIN":
                rec_q = rec_q.filter(LeaveRequest.user_id == -1)  # MR receives 0
            received = rec_q.count()
            return WorkflowSummaryResponse(module=module, drafts=drafts, applied=applied, received=received)

        elif norm_mod in ("tours", "tour-plans", "tour-plan", "tour"):
            # Tour Programs
            drafts = (
                self.db.query(TourProgram)
                .filter(
                    TourProgram.user_id == current_user.id,
                    TourProgram.status.in_(["DRAFT", "CANCELLED"]),
                )
                .count()
            )
            applied = (
                self.db.query(TourProgram)
                .filter(
                    TourProgram.user_id == current_user.id,
                    TourProgram.status.in_(["PENDING", "APPROVED", "REJECTED", "SUBMITTED"]),
                )
                .count()
            )
            rec_q = self.db.query(TourProgram).filter(
                TourProgram.status.in_(["PENDING", "SUBMITTED"]),
            )
            if role_code == "MANAGER":
                rec_q = rec_q.filter(TourProgram.user_id.in_(team_ids))
            elif role_code != "ADMIN":
                rec_q = rec_q.filter(TourProgram.user_id == -1)
            received = rec_q.count()
            return WorkflowSummaryResponse(module=module, drafts=drafts, applied=applied, received=received)

        elif norm_mod in ("expenses", "monthly-expenses", "monthly-expense", "expense"):
            drafts = (
                self.db.query(Expense)
                .filter(
                    Expense.user_id == current_user.id,
                    Expense.status == "DRAFT",
                )
                .count()
            )
            applied = (
                self.db.query(Expense)
                .filter(
                    Expense.user_id == current_user.id,
                    Expense.status.in_(["SUBMITTED", "APPROVED", "REJECTED", "PAID"]),
                )
                .count()
            )
            rec_q = self.db.query(Expense).filter(
                Expense.status == "SUBMITTED",
            )
            if role_code == "MANAGER":
                rec_q = rec_q.filter(Expense.user_id.in_(team_ids))
            elif role_code != "ADMIN":
                rec_q = rec_q.filter(Expense.user_id == -1)
            received = rec_q.count()
            return WorkflowSummaryResponse(module=module, drafts=drafts, applied=applied, received=received)

        elif norm_mod in ("new-doctors", "new-doctor"):
            total_active = self.db.query(Doctor).filter(Doctor.is_active == True, Doctor.is_deleted == False).count()  # noqa: E712
            total_pending = self.db.query(Doctor).filter(Doctor.is_active == False, Doctor.is_deleted == False).count()  # noqa: E712
            return WorkflowSummaryResponse(module=module, drafts=0, applied=total_active, received=total_pending)

        elif norm_mod in ("new-chemists", "new-chemist"):
            total_active = self.db.query(Chemist).filter(Chemist.is_active == True, Chemist.is_deleted == False).count()  # noqa: E712
            total_pending = self.db.query(Chemist).filter(Chemist.is_active == False, Chemist.is_deleted == False).count()  # noqa: E712
            return WorkflowSummaryResponse(module=module, drafts=0, applied=total_active, received=total_pending)

        elif norm_mod in ("new-stockists", "new-stockist"):
            total_active = self.db.query(Stockist).filter(Stockist.is_active == True, Stockist.is_deleted == False).count()  # noqa: E712
            total_pending = self.db.query(Stockist).filter(Stockist.is_active == False, Stockist.is_deleted == False).count()  # noqa: E712
            return WorkflowSummaryResponse(module=module, drafts=0, applied=total_active, received=total_pending)

        return WorkflowSummaryResponse(module=module, drafts=0, applied=0, received=0)

    # -------------------------------------------------------------------------
    # WORKFLOW LIST (Dynamic Table Records)
    # -------------------------------------------------------------------------
    def list_items(
        self,
        module: str,
        box: str,
        current_user: User,
        search: str | None = None,
        status_filter: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[WorkflowItemResponse]:
        """Fetch items for the selected workflow box."""
        norm_mod = module.lower().replace("_", "-")
        norm_box = box.lower().strip()
        role_code = current_user.role.code if current_user.role else "MR"
        team_ids = self._get_team_user_ids(current_user)
        is_approver = role_code in ("ADMIN", "MANAGER")

        items: list[WorkflowItemResponse] = []

        if norm_mod in ("leaves", "leave"):
            q = (
                self.db.query(LeaveRequest)
                .options(joinedload(LeaveRequest.user))
            )
            if norm_box == "drafts":
                q = q.filter(
                    LeaveRequest.user_id == current_user.id,
                    LeaveRequest.status.in_(["DRAFT", "CANCELLED"]),
                )
            elif norm_box == "applied":
                q = q.filter(
                    LeaveRequest.user_id == current_user.id,
                    LeaveRequest.status.in_(["PENDING", "APPROVED", "REJECTED"]),
                )
            else:  # received
                q = q.filter(LeaveRequest.status == "PENDING")
                if role_code == "MANAGER":
                    q = q.filter(LeaveRequest.user_id.in_(team_ids))
                elif role_code != "ADMIN":
                    return []

            if status_filter and status_filter != "ALL":
                q = q.filter(LeaveRequest.status == status_filter.upper())

            if search:
                s = f"%{search.strip()}%"
                q = q.join(LeaveRequest.user).filter(
                    or_(
                        User.full_name.ilike(s),
                        LeaveRequest.reason.ilike(s),
                        LeaveRequest.leave_type.ilike(s),
                    )
                )

            records = q.order_by(LeaveRequest.created_at.desc()).offset(skip).limit(limit).all()

            for lr in records:
                user_name = lr.user.full_name if lr.user else f"Employee #{lr.user_id}"
                actions = ["view"]
                if is_approver and lr.status == "PENDING" and lr.user_id != current_user.id:
                    actions.extend(["approve", "reject"])
                elif lr.status == "DRAFT" and lr.user_id == current_user.id:
                    actions.extend(["edit", "revert"])

                # Resolve approval_request_id if linked
                app_req_id = lr.approval_request_id
                if not app_req_id:
                    app_rec = (
                        self.db.query(ApprovalRequest)
                        .filter(
                            ApprovalRequest.entity_type == "LEAVE",
                            ApprovalRequest.entity_id == lr.id,
                        )
                        .first()
                    )
                    if app_rec:
                        app_req_id = app_rec.id

                items.append(
                    WorkflowItemResponse(
                        id=app_req_id or lr.id,
                        module="leaves",
                        entity_type="LEAVE",
                        entity_id=lr.id,
                        approval_request_id=app_req_id,
                        title=f"Leave: {lr.leave_type.title()} ({lr.days_count} days)",
                        requester_id=lr.user_id,
                        requester_name=user_name,
                        requester_email=lr.user.email if lr.user else None,
                        details=f"From {lr.start_date} to {lr.end_date} - {lr.reason}",
                        status=lr.status,
                        created_at=lr.created_at,
                        updated_at=lr.updated_at,
                        actions=actions,
                    )
                )
            return items

        elif norm_mod in ("tours", "tour-plans", "tour-plan", "tour"):
            q = (
                self.db.query(TourProgram)
                .options(joinedload(TourProgram.user))
            )
            if norm_box == "drafts":
                q = q.filter(
                    TourProgram.user_id == current_user.id,
                    TourProgram.status.in_(["DRAFT", "CANCELLED"]),
                )
            elif norm_box == "applied":
                q = q.filter(
                    TourProgram.user_id == current_user.id,
                    TourProgram.status.in_(["PENDING", "APPROVED", "REJECTED", "SUBMITTED"]),
                )
            else:  # received
                q = q.filter(TourProgram.status.in_(["PENDING", "SUBMITTED"]))
                if role_code == "MANAGER":
                    q = q.filter(TourProgram.user_id.in_(team_ids))
                elif role_code != "ADMIN":
                    return []

            if status_filter and status_filter != "ALL":
                q = q.filter(TourProgram.status == status_filter.upper())

            if search:
                s = f"%{search.strip()}%"
                q = q.join(TourProgram.user).filter(
                    or_(
                        User.full_name.ilike(s),
                        TourProgram.title.ilike(s),
                        TourProgram.route_details.ilike(s),
                    )
                )

            tour_records = q.order_by(TourProgram.created_at.desc()).offset(skip).limit(limit).all()

            for tp in tour_records:
                user_name = tp.user.full_name if tp.user else f"Field Rep #{tp.user_id}"
                actions = ["view"]
                if is_approver and tp.status == "PENDING" and tp.user_id != current_user.id:
                    actions.extend(["approve", "reject"])

                app_req_id = tp.approval_request_id
                if not app_req_id:
                    app_rec = (
                        self.db.query(ApprovalRequest)
                        .filter(
                            ApprovalRequest.entity_type == "TOUR",
                            ApprovalRequest.entity_id == tp.id,
                        )
                        .first()
                    )
                    if app_rec:
                        app_req_id = app_rec.id

                items.append(
                    WorkflowItemResponse(
                        id=app_req_id or tp.id,
                        module="tours",
                        entity_type="TOUR",
                        entity_id=tp.id,
                        approval_request_id=app_req_id,
                        title=f"Tour: {tp.title} ({tp.total_days} days)",
                        requester_id=tp.user_id,
                        requester_name=user_name,
                        requester_email=tp.user.email if tp.user else None,
                        details=f"{tp.start_date} to {tp.end_date} | Route: {tp.route_details or 'HQ Area'}",
                        status=tp.status,
                        created_at=tp.created_at,
                        updated_at=tp.updated_at,
                        actions=actions,
                    )
                )
            return items

        elif norm_mod in ("expenses", "monthly-expenses", "monthly-expense", "expense"):
            q = (
                self.db.query(Expense)
                .options(joinedload(Expense.user))
            )
            if norm_box == "drafts":
                q = q.filter(
                    Expense.user_id == current_user.id,
                    Expense.status == "DRAFT",
                )
            elif norm_box == "applied":
                q = q.filter(
                    Expense.user_id == current_user.id,
                    Expense.status.in_(["SUBMITTED", "APPROVED", "REJECTED", "PAID"]),
                )
            else:  # received
                q = q.filter(Expense.status == "SUBMITTED")
                if role_code == "MANAGER":
                    q = q.filter(Expense.user_id.in_(team_ids))
                elif role_code != "ADMIN":
                    return []

            if status_filter and status_filter != "ALL":
                q = q.filter(Expense.status == status_filter.upper())

            if search:
                s = f"%{search.strip()}%"
                q = q.join(Expense.user).filter(
                    or_(
                        User.full_name.ilike(s),
                        Expense.expense_type.ilike(s),
                        Expense.description.ilike(s),
                    )
                )

            expense_records = (
                q.order_by(Expense.expense_date.desc(), Expense.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )

            for exp in expense_records:
                user_name = exp.user.full_name if exp.user else f"Field Rep #{exp.user_id}"
                actions = ["view"]
                if is_approver and exp.status == "SUBMITTED" and exp.user_id != current_user.id:
                    actions.extend(["approve", "reject"])

                app_req_id = exp.approval_request_id
                if not app_req_id:
                    app_rec = (
                        self.db.query(ApprovalRequest)
                        .filter(
                            ApprovalRequest.entity_type == "EXPENSE",
                            ApprovalRequest.entity_id == exp.id,
                        )
                        .first()
                    )
                    if app_rec:
                        app_req_id = app_rec.id

                head_title = exp.expense_type.replace("_", " ").title()
                items.append(
                    WorkflowItemResponse(
                        id=app_req_id or exp.id,
                        module="expenses",
                        entity_type="EXPENSE",
                        entity_id=exp.id,
                        approval_request_id=app_req_id,
                        title=f"{head_title} - ₹{exp.amount:,.2f}",
                        requester_id=exp.user_id,
                        requester_name=user_name,
                        requester_email=exp.user.email if exp.user else None,
                        details=f"Expense Date: {exp.expense_date} | {exp.description or 'Daily field claim'}",
                        status="PENDING" if exp.status == "SUBMITTED" else exp.status,
                        created_at=exp.created_at,
                        updated_at=exp.updated_at,
                        actions=actions,
                    )
                )
            return items

        elif norm_mod in ("new-doctors", "new-doctor"):
            doc_q = (
                self.db.query(Doctor)
                .options(joinedload(Doctor.territory), joinedload(Doctor.area))
                .filter(Doctor.is_deleted == False)  # noqa: E712
            )
            if norm_box == "received":
                doc_q = doc_q.filter(Doctor.is_active == False)
            else:
                doc_q = doc_q.filter(Doctor.is_active == True)

            if search:
                s = f"%{search.strip()}%"
                doc_q = doc_q.filter(
                    or_(Doctor.full_name.ilike(s), Doctor.code.ilike(s), Doctor.clinic_name.ilike(s))
                )

            docs = doc_q.order_by(Doctor.created_at.desc()).offset(skip).limit(limit).all()
            for d in docs:
                status_str = "APPROVED" if d.is_active else "PENDING"
                actions = ["view"]
                if is_approver and not d.is_active:
                    actions.extend(["approve", "reject"])

                items.append(
                    WorkflowItemResponse(
                        id=d.id,
                        module="new-doctors",
                        entity_type="DOCTOR",
                        entity_id=d.id,
                        title=f"Dr. {d.full_name} ({d.specialization or d.category})",
                        requester_id=d.created_by or 0,
                        requester_name=d.clinic_name or "Field Registration",
                        details=f"Code: {d.code} | Phone: {d.phone or 'N/A'} | Territory: {d.territory.name if d.territory else 'Unassigned'}",
                        status=status_str,
                        created_at=d.created_at,
                        updated_at=d.updated_at,
                        actions=actions,
                    )
                )
            return items

        elif norm_mod in ("new-chemists", "new-chemist"):
            chem_q = (
                self.db.query(Chemist)
                .options(joinedload(Chemist.territory), joinedload(Chemist.area))
                .filter(Chemist.is_deleted == False)  # noqa: E712
            )
            if norm_box == "received":
                chem_q = chem_q.filter(Chemist.is_active == False)
            else:
                chem_q = chem_q.filter(Chemist.is_active == True)

            if search:
                s = f"%{search.strip()}%"
                chem_q = chem_q.filter(
                    or_(Chemist.shop_name.ilike(s), Chemist.code.ilike(s), Chemist.contact_person.ilike(s))
                )

            chems = chem_q.order_by(Chemist.created_at.desc()).offset(skip).limit(limit).all()
            for c in chems:
                status_str = "APPROVED" if c.is_active else "PENDING"
                actions = ["view"]
                if is_approver and not c.is_active:
                    actions.extend(["approve", "reject"])

                items.append(
                    WorkflowItemResponse(
                        id=c.id,
                        module="new-chemists",
                        entity_type="CHEMIST",
                        entity_id=c.id,
                        title=f"Chemist: {c.shop_name}",
                        requester_id=c.created_by or 0,
                        requester_name=c.contact_person or "Field Registration",
                        details=f"DL: {c.dl_number or 'N/A'} | GSTIN: {c.gstin or 'N/A'} | Territory: {c.territory.name if c.territory else 'Unassigned'}",
                        status=status_str,
                        created_at=c.created_at,
                        updated_at=c.updated_at,
                        actions=actions,
                    )
                )
            return items

        elif norm_mod in ("new-stockists", "new-stockist"):
            stock_q = (
                self.db.query(Stockist)
                .options(joinedload(Stockist.territory), joinedload(Stockist.area))
                .filter(Stockist.is_deleted == False)  # noqa: E712
            )
            if norm_box == "received":
                stock_q = stock_q.filter(Stockist.is_active == False)
            else:
                stock_q = stock_q.filter(Stockist.is_active == True)

            if search:
                s = f"%{search.strip()}%"
                stock_q = stock_q.filter(
                    or_(Stockist.agency_name.ilike(s), Stockist.code.ilike(s), Stockist.contact_person.ilike(s))
                )

            stocks = stock_q.order_by(Stockist.created_at.desc()).offset(skip).limit(limit).all()
            for s in stocks:
                status_str = "APPROVED" if s.is_active else "PENDING"
                actions = ["view"]
                if is_approver and not s.is_active:
                    actions.extend(["approve", "reject"])

                items.append(
                    WorkflowItemResponse(
                        id=s.id,
                        module="new-stockists",
                        entity_type="STOCKIST",
                        entity_id=s.id,
                        title=f"Stockist: {s.agency_name}",
                        requester_id=s.created_by or 0,
                        requester_name=s.contact_person or "Wholesale Registration",
                        details=f"DL: {s.dl_number or 'N/A'} | Credit: {s.credit_days}d | Territory: {s.territory.name if s.territory else 'Unassigned'}",
                        status=status_str,
                        created_at=s.created_at,
                        updated_at=s.updated_at,
                        actions=actions,
                    )
                )
            return items

        return []
