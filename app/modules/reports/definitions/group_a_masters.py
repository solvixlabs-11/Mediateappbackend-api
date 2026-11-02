"""Group A: Master lists reports (Reports 1 to 3)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.modules.customers.models import Chemist, Doctor, Hospital, HospitalDoctor, Stockist
from app.modules.dcr.models import DcrVisit
from app.modules.reports.base import BaseReport, ReportRegistry
from app.modules.reports.schemas import ReportColumn, ReportFilterParams, ReportFilterSchema
from app.modules.territories.models import Territory, UserTerritoryAssignment
from app.modules.users.models import User


class DoctorListReport(BaseReport):
    """Report 1: Doctor List (NOW).

    Columns: Name, Code, Specialization, Category, Priority, Qualification,
    Hospital or clinic, Area, City, Territory, Phone, Assigned MR, Active.
    """

    key = "doctor_list"
    title = "Doctor List"
    group = "Master Lists"
    description = "Comprehensive master list of healthcare professionals, assigned MRs, hospital affiliations, and specialties."
    landscape = True
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    report_number = 1
    status = "NOW"
    is_ready = True
    filter_schema = ReportFilterSchema(
        date_range=False,
        mr_picker=True,
        territory_picker=True,
        specialization_picker=True,
        category_picker=True,
        active_picker=True,
    )

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="name", label="Name", type="string"),
            ReportColumn(key="code", label="Code", type="string", align="center"),
            ReportColumn(key="specialization", label="Specialization", type="string"),
            ReportColumn(key="category", label="Category", type="string", align="center"),
            ReportColumn(key="priority", label="Priority", type="string", align="center"),
            ReportColumn(key="qualification", label="Qualification", type="string"),
            ReportColumn(key="hospital_clinic", label="Hospital / Clinic", type="string"),
            ReportColumn(key="area", label="Area", type="string"),
            ReportColumn(key="city", label="City", type="string"),
            ReportColumn(key="territory", label="Territory", type="string"),
            ReportColumn(key="phone", label="Phone", type="string"),
            ReportColumn(key="assigned_mr", label="Assigned MR", type="string"),
            ReportColumn(key="active", label="Active", type="status", align="center"),
        ]

    def run_query(
        self,
        db: Session,
        filters: ReportFilterParams,
        user_ids: list[int] | None,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> list[dict[str, Any]]:
        # Resolve accessible territories if scoped
        allowed_terr_ids: set[int] | None = None
        mr_doc_ids: set[int] = set()
        if user_ids is not None:
            assigns = db.execute(
                select(UserTerritoryAssignment.territory_id).where(
                    UserTerritoryAssignment.user_id.in_(user_ids),
                    UserTerritoryAssignment.unassigned_at.is_(None),
                    UserTerritoryAssignment.is_deleted.is_(False),
                )
            ).scalars().all()
            allowed_terr_ids = set(assigns)

            visited = db.execute(
                select(DcrVisit.doctor_id).where(
                    DcrVisit.user_id.in_(user_ids),
                    DcrVisit.doctor_id.isnot(None),
                    DcrVisit.is_deleted.is_(False),
                )
            ).scalars().all()
            mr_doc_ids = set(visited)

        # Pre-cache territory to MR mapping
        user_assigns = db.execute(
            select(UserTerritoryAssignment.territory_id, User.full_name)
            .join(User, UserTerritoryAssignment.user_id == User.id)
            .where(
                UserTerritoryAssignment.unassigned_at.is_(None),
                UserTerritoryAssignment.is_deleted.is_(False),
                User.is_deleted.is_(False),
            )
        ).all()
        terr_mr_map: dict[int, list[str]] = {}
        for tid, mr_name in user_assigns:
            if tid is not None and mr_name:
                terr_mr_map.setdefault(tid, []).append(mr_name)

        stmt = (
            select(Doctor)
            .options(
                selectinload(Doctor.territory),
                selectinload(Doctor.area),
                selectinload(Doctor.hospital_doctors).selectinload(HospitalDoctor.hospital),
            )
            .where(Doctor.is_deleted.is_(False))
            .order_by(Doctor.full_name.asc())
        )

        if user_ids is not None:
            conds = []
            if allowed_terr_ids:
                conds.append(Doctor.territory_id.in_(allowed_terr_ids))
            if mr_doc_ids:
                conds.append(Doctor.id.in_(mr_doc_ids))
            if conds:
                stmt = stmt.where(or_(*conds))
            else:
                stmt = stmt.where(Doctor.id == -1)

        if filters.territory_id:
            stmt = stmt.where(Doctor.territory_id == filters.territory_id)

        if filters.specialization and filters.specialization != "All":
            stmt = stmt.where(Doctor.specialization.ilike(f"%{filters.specialization}%"))

        if filters.category and filters.category != "All":
            stmt = stmt.where(Doctor.category.ilike(filters.category))

        if filters.active is not None:
            stmt = stmt.where(Doctor.is_active.is_(filters.active))

        doctors = list(db.scalars(stmt).all())
        results: list[dict[str, Any]] = []

        target_mrs = []
        if user_ids:
            target_mrs = list(
                db.scalars(
                    select(User.full_name).where(User.id.in_(user_ids), User.is_deleted.is_(False))
                ).all()
            )

        for d in doctors:
            assigned_mrs = terr_mr_map.get(d.territory_id or 0, [])
            if target_mrs:
                filtered_mrs = [m for m in assigned_mrs if m in target_mrs]
                mr_display = ", ".join(filtered_mrs) if filtered_mrs else (", ".join(target_mrs) if d.id in mr_doc_ids else (", ".join(assigned_mrs) if assigned_mrs else "Unassigned"))
            else:
                mr_display = ", ".join(assigned_mrs) if assigned_mrs else "Unassigned"

            hosp_name = d.clinic_name or "-"
            if d.hospital_doctors:
                active_hds = [hd for hd in d.hospital_doctors if not getattr(hd, "is_deleted", False)]
                if active_hds:
                    primary = next((hd for hd in active_hds if hd.is_primary), active_hds[0])
                    if primary.hospital and not getattr(primary.hospital, "is_deleted", False):
                        hosp_name = primary.hospital.name

            city_name = d.territory.headquarters if d.territory else "-"
            area_name = d.area.name if d.area else "-"
            terr_name = d.territory.name if d.territory else "-"

            full_name = (d.full_name or "").strip()
            doc_name = full_name if full_name.lower().startswith(("dr.", "dr ")) else f"Dr. {full_name}" if full_name else "-"
            cat = (d.category or "A").strip().upper()
            is_act = bool(getattr(d, "is_active", True))

            results.append({
                "name": doc_name,
                "code": d.code or "-",
                "specialization": d.specialization or d.qualification or "General",
                "category": cat,
                "priority": "HIGH" if cat == "A" else ("MEDIUM" if cat == "B" else "STANDARD"),
                "qualification": d.qualification or "-",
                "hospital_clinic": hosp_name,
                "area": area_name,
                "city": city_name,
                "territory": terr_name,
                "phone": d.phone or "-",
                "assigned_mr": mr_display,
                "active": "Active" if is_act else "Inactive",
            })

        return results

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        total = len(items)
        cat_a = sum(1 for it in items if it.get("category") == "A")
        cat_b = sum(1 for it in items if it.get("category") == "B")
        cat_c = sum(1 for it in items if it.get("category") == "C")
        active_count = sum(1 for it in items if it.get("active") == "Active")
        return {
            "total_doctors": total,
            "category_a": cat_a,
            "category_b": cat_b,
            "category_c": cat_c,
            "active_doctors": active_count,
        }


class ChemistListReport(BaseReport):
    """Report 2: Chemist List (NOW).

    Columns: Name, Code, Owner, Phone, Address, Area, Territory, Assigned MR, Active.
    """

    key = "chemist_list"
    title = "Chemist List"
    group = "Master Lists"
    description = "Retail chemist master list with licensing details, territory mapping, and responsible field representatives."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    report_number = 2
    status = "NOW"
    is_ready = True
    filter_schema = ReportFilterSchema(
        date_range=False,
        mr_picker=True,
        territory_picker=True,
        active_picker=True,
    )

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="name", label="Chemist / Shop Name", type="string"),
            ReportColumn(key="code", label="Code", type="string", align="center"),
            ReportColumn(key="owner", label="Owner / Contact", type="string"),
            ReportColumn(key="phone", label="Phone", type="string"),
            ReportColumn(key="address", label="Address", type="string"),
            ReportColumn(key="area", label="Area", type="string"),
            ReportColumn(key="territory", label="Territory", type="string"),
            ReportColumn(key="assigned_mr", label="Assigned MR", type="string"),
            ReportColumn(key="active", label="Active", type="status", align="center"),
        ]

    def run_query(
        self,
        db: Session,
        filters: ReportFilterParams,
        user_ids: list[int] | None,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> list[dict[str, Any]]:
        allowed_terr_ids: set[int] | None = None
        mr_chem_ids: set[int] = set()
        if user_ids is not None:
            assigns = db.execute(
                select(UserTerritoryAssignment.territory_id).where(
                    UserTerritoryAssignment.user_id.in_(user_ids),
                    UserTerritoryAssignment.unassigned_at.is_(None),
                    UserTerritoryAssignment.is_deleted.is_(False),
                )
            ).scalars().all()
            allowed_terr_ids = set(assigns)

            visited = db.execute(
                select(DcrVisit.chemist_id).where(
                    DcrVisit.user_id.in_(user_ids),
                    DcrVisit.chemist_id.isnot(None),
                    DcrVisit.is_deleted.is_(False),
                )
            ).scalars().all()
            mr_chem_ids = set(visited)

        user_assigns = db.execute(
            select(UserTerritoryAssignment.territory_id, User.full_name)
            .join(User, UserTerritoryAssignment.user_id == User.id)
            .where(
                UserTerritoryAssignment.unassigned_at.is_(None),
                UserTerritoryAssignment.is_deleted.is_(False),
                User.is_deleted.is_(False),
            )
        ).all()
        terr_mr_map: dict[int, list[str]] = {}
        for tid, mr_name in user_assigns:
            if tid is not None and mr_name:
                terr_mr_map.setdefault(tid, []).append(mr_name)

        stmt = (
            select(Chemist)
            .options(
                selectinload(Chemist.territory),
                selectinload(Chemist.area),
            )
            .where(Chemist.is_deleted.is_(False))
            .order_by(Chemist.shop_name.asc())
        )

        if user_ids is not None:
            conds = []
            if allowed_terr_ids:
                conds.append(Chemist.territory_id.in_(allowed_terr_ids))
            if mr_chem_ids:
                conds.append(Chemist.id.in_(mr_chem_ids))
            if conds:
                stmt = stmt.where(or_(*conds))
            else:
                stmt = stmt.where(Chemist.id == -1)

        if filters.territory_id:
            stmt = stmt.where(Chemist.territory_id == filters.territory_id)

        if filters.active is not None:
            stmt = stmt.where(Chemist.is_active.is_(filters.active))

        chemists = list(db.scalars(stmt).all())
        results: list[dict[str, Any]] = []

        target_mrs = []
        if user_ids:
            target_mrs = list(
                db.scalars(
                    select(User.full_name).where(User.id.in_(user_ids), User.is_deleted.is_(False))
                ).all()
            )

        for c in chemists:
            assigned_mrs = terr_mr_map.get(c.territory_id or 0, [])
            if target_mrs:
                filtered_mrs = [m for m in assigned_mrs if m in target_mrs]
                mr_display = ", ".join(filtered_mrs) if filtered_mrs else (", ".join(target_mrs) if c.id in mr_chem_ids else (", ".join(assigned_mrs) if assigned_mrs else "Unassigned"))
            else:
                mr_display = ", ".join(assigned_mrs) if assigned_mrs else "Unassigned"

            is_act = bool(getattr(c, "is_active", True))
            results.append({
                "name": c.shop_name or "-",
                "code": c.code or "-",
                "owner": c.contact_person or "-",
                "phone": c.phone or "-",
                "address": c.address or "-",
                "area": c.area.name if c.area else "-",
                "territory": c.territory.name if c.territory else "-",
                "assigned_mr": mr_display,
                "active": "Active" if is_act else "Inactive",
            })

        return results

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "total_chemists": len(items),
            "active_chemists": sum(1 for it in items if it.get("active") == "Active"),
        }


class MrWiseRouteMasterReport(BaseReport):
    """Report 3: MR Wise Route Master (NOW).

    Columns: MR, Territory or route, Area, City, Assigned from, Doctors count,
    Chemists count, Stockists count.
    """

    key = "mr_wise_route_master"
    title = "MR Wise Route Master"
    group = "Master Lists"
    description = "Operational routes and customer catchment density breakdown per Medical Representative."
    landscape = False
    allowed_roles = ["ADMIN", "MANAGER", "MR"]
    report_number = 3
    status = "NOW"
    is_ready = True
    filter_schema = ReportFilterSchema(
        date_range=False,
        mr_picker=True,
        territory_picker=True,
    )

    def get_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn(key="mr_name", label="MR", type="string"),
            ReportColumn(key="territory_route", label="Territory / Route", type="string"),
            ReportColumn(key="area", label="Area", type="string"),
            ReportColumn(key="city", label="City", type="string"),
            ReportColumn(key="assigned_from", label="Assigned From", type="date", align="center"),
            ReportColumn(key="doctors_count", label="Doctors", type="number", align="right"),
            ReportColumn(key="chemists_count", label="Chemists", type="number", align="right"),
            ReportColumn(key="stockists_count", label="Stockists", type="number", align="right"),
        ]

    def run_query(
        self,
        db: Session,
        filters: ReportFilterParams,
        user_ids: list[int] | None,
        start_utc: datetime | None,
        end_utc: datetime | None,
    ) -> list[dict[str, Any]]:
        stmt = (
            select(UserTerritoryAssignment)
            .join(User, UserTerritoryAssignment.user_id == User.id)
            .join(Territory, UserTerritoryAssignment.territory_id == Territory.id)
            .options(
                selectinload(UserTerritoryAssignment.user),
                selectinload(UserTerritoryAssignment.territory).selectinload(Territory.areas),
            )
            .where(
                UserTerritoryAssignment.unassigned_at.is_(None),
                UserTerritoryAssignment.is_deleted.is_(False),
                User.is_deleted.is_(False),
                Territory.is_deleted.is_(False),
            )
            .order_by(User.full_name.asc())
        )

        if user_ids is not None:
            stmt = stmt.where(UserTerritoryAssignment.user_id.in_(user_ids))

        if filters.territory_id:
            stmt = stmt.where(UserTerritoryAssignment.territory_id == filters.territory_id)

        assignments = list(db.scalars(stmt).all())
        results: list[dict[str, Any]] = []

        # Count doctors, chemists, stockists per territory
        doc_counts = dict(
            db.execute(
                select(Doctor.territory_id, func.count(Doctor.id))
                .where(Doctor.is_deleted.is_(False))
                .group_by(Doctor.territory_id)
            ).all()
        )
        chem_counts = dict(
            db.execute(
                select(Chemist.territory_id, func.count(Chemist.id))
                .where(Chemist.is_deleted.is_(False))
                .group_by(Chemist.territory_id)
            ).all()
        )
        stock_counts = dict(
            db.execute(
                select(Stockist.territory_id, func.count(Stockist.id))
                .where(Stockist.is_deleted.is_(False))
                .group_by(Stockist.territory_id)
            ).all()
        )

        for a in assignments:
            tid = a.territory_id
            t = a.territory
            if not t:
                continue
            active_areas = [ar.name for ar in (t.areas or []) if not getattr(ar, "is_deleted", False)]
            areas_str = ", ".join(active_areas) if active_areas else (t.headquarters or "-")

            results.append({
                "mr_name": a.user.full_name if a.user else f"MR #{a.user_id}",
                "territory_route": t.name,
                "area": areas_str,
                "city": t.headquarters or "-",
                "assigned_from": a.assigned_at.strftime("%d-%b-%Y") if a.assigned_at else "-",
                "doctors_count": doc_counts.get(tid, 0),
                "chemists_count": chem_counts.get(tid, 0),
                "stockists_count": stock_counts.get(tid, 0),
            })

        return results

    def calculate_summary(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "total_routes": len(items),
            "total_assigned_doctors": sum(it.get("doctors_count", 0) for it in items),
            "total_assigned_chemists": sum(it.get("chemists_count", 0) for it in items),
            "total_assigned_stockists": sum(it.get("stockists_count", 0) for it in items),
        }


ReportRegistry.register(DoctorListReport)
ReportRegistry.register(ChemistListReport)
ReportRegistry.register(MrWiseRouteMasterReport)
