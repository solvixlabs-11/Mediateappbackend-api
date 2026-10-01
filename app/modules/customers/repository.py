"""Customers database repository."""

from collections.abc import Sequence
from datetime import date

from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.modules.customers.models import (
    Chemist,
    Doctor,
    Hospital,
    HospitalDoctor,
    Stockist,
)


class CustomerRepository:
    """Repository handling CRUD, scoping, and relationships for customers."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # Sequential Code Generation Helper
    def _next_code(self, prefix: str, model: type) -> str:
        count = self.db.query(model).count()
        return f"{prefix}-{1001 + count}"

    # DOCTORS
    def list_doctors(
        self,
        accessible_territory_ids: Sequence[int] | None = None,
        search: str | None = None,
        specialization: str | None = None,
        category: str | None = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Doctor]:
        """List doctors respecting territory scope and search filters."""
        query = (
            self.db.query(Doctor)
            .options(selectinload(Doctor.hospital_doctors).joinedload(HospitalDoctor.hospital))
            .filter(Doctor.is_deleted == False)  # noqa: E712
        )
        if accessible_territory_ids is not None:
            query = query.filter(Doctor.territory_id.in_(accessible_territory_ids))
        if active_only:
            query = query.filter(Doctor.is_active == True)  # noqa: E712
        if specialization:
            query = query.filter(Doctor.specialization.ilike(f"%{specialization.strip()}%"))
        if category:
            query = query.filter(Doctor.category == category.upper().strip())
        if search:
            pat = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Doctor.full_name.ilike(pat),
                    Doctor.code.ilike(pat),
                    Doctor.clinic_name.ilike(pat),
                    Doctor.phone.ilike(pat),
                )
            )
        return query.order_by(Doctor.full_name.asc()).offset(skip).limit(limit).all()

    def get_doctor_by_id(self, doctor_id: int) -> Doctor | None:
        """Get doctor by ID."""
        return (
            self.db.query(Doctor)
            .options(selectinload(Doctor.hospital_doctors).joinedload(HospitalDoctor.hospital))
            .filter(Doctor.id == doctor_id, Doctor.is_deleted == False)  # noqa: E712
            .first()
        )

    def create_doctor(
        self,
        full_name: str,
        qualification: str | None = None,
        specialization: str | None = None,
        category: str = "A",
        phone: str | None = None,
        email: str | None = None,
        clinic_name: str | None = None,
        address: str | None = None,
        area_id: int | None = None,
        territory_id: int | None = None,
        pincode: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        date_of_birth: date | None = None,
        anniversary_date: date | None = None,
        created_by_user_id: int | None = None,
    ) -> Doctor:
        """Create new Doctor entity with unique code."""
        code = self._next_code("DOC", Doctor)
        doc = Doctor(
            code=code,
            full_name=full_name.strip(),
            qualification=qualification.strip() if qualification else None,
            specialization=specialization.strip() if specialization else None,
            category=category.upper().strip(),
            phone=phone.strip() if phone else None,
            email=email.strip().lower() if email else None,
            clinic_name=clinic_name.strip() if clinic_name else None,
            address=address.strip() if address else None,
            area_id=area_id,
            territory_id=territory_id,
            pincode=pincode.strip() if pincode else None,
            latitude=latitude,
            longitude=longitude,
            date_of_birth=date_of_birth,
            anniversary_date=anniversary_date,
            is_active=True,
            created_by=created_by_user_id,
        )
        self.db.add(doc)
        self.db.flush()
        return doc

    # HOSPITALS
    def list_hospitals(
        self,
        accessible_territory_ids: Sequence[int] | None = None,
        search: str | None = None,
        hospital_type: str | None = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Hospital]:
        """List hospitals respecting territory scope."""
        query = self.db.query(Hospital).filter(Hospital.is_deleted == False)  # noqa: E712
        if accessible_territory_ids is not None:
            query = query.filter(Hospital.territory_id.in_(accessible_territory_ids))
        if active_only:
            query = query.filter(Hospital.is_active == True)  # noqa: E712
        if hospital_type:
            query = query.filter(Hospital.type == hospital_type.strip())
        if search:
            pat = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Hospital.name.ilike(pat),
                    Hospital.code.ilike(pat),
                    Hospital.address.ilike(pat),
                )
            )
        return query.order_by(Hospital.name.asc()).offset(skip).limit(limit).all()

    def get_hospital_by_id(self, hospital_id: int) -> Hospital | None:
        """Get hospital by ID."""
        return (
            self.db.query(Hospital)
            .filter(Hospital.id == hospital_id, Hospital.is_deleted == False)  # noqa: E712
            .first()
        )

    def create_hospital(
        self,
        name: str,
        hospital_type: str = "General",
        contact_person: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        address: str | None = None,
        area_id: int | None = None,
        territory_id: int | None = None,
        pincode: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        bed_count: int | None = None,
        created_by_user_id: int | None = None,
    ) -> Hospital:
        """Create new Hospital entity with code."""
        code = self._next_code("HSP", Hospital)
        hsp = Hospital(
            code=code,
            name=name.strip(),
            type=hospital_type.strip(),
            contact_person=contact_person.strip() if contact_person else None,
            phone=phone.strip() if phone else None,
            email=email.strip().lower() if email else None,
            address=address.strip() if address else None,
            area_id=area_id,
            territory_id=territory_id,
            pincode=pincode.strip() if pincode else None,
            latitude=latitude,
            longitude=longitude,
            bed_count=bed_count,
            is_active=True,
            created_by=created_by_user_id,
        )
        self.db.add(hsp)
        self.db.flush()
        return hsp

    def map_doctor_to_hospital(
        self,
        hospital_id: int,
        doctor_id: int,
        department: str | None = None,
        visiting_hours: str | None = None,
        is_primary: bool = False,
    ) -> HospitalDoctor:
        """Map a doctor to a hospital. If is_primary, unsets other primary flags."""
        if is_primary:
            self.db.query(HospitalDoctor).filter(HospitalDoctor.doctor_id == doctor_id).update(
                {"is_primary": False}
            )

        existing = (
            self.db.query(HospitalDoctor)
            .filter(
                HospitalDoctor.hospital_id == hospital_id,
                HospitalDoctor.doctor_id == doctor_id,
            )
            .first()
        )
        if existing:
            existing.department = department
            existing.visiting_hours = visiting_hours
            existing.is_primary = is_primary
            self.db.flush()
            return existing

        mapping = HospitalDoctor(
            hospital_id=hospital_id,
            doctor_id=doctor_id,
            department=department,
            visiting_hours=visiting_hours,
            is_primary=is_primary,
        )
        self.db.add(mapping)
        self.db.flush()
        return mapping

    # CHEMISTS
    def list_chemists(
        self,
        accessible_territory_ids: Sequence[int] | None = None,
        search: str | None = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Chemist]:
        """List chemists with scope."""
        query = self.db.query(Chemist).filter(Chemist.is_deleted == False)  # noqa: E712
        if accessible_territory_ids is not None:
            query = query.filter(Chemist.territory_id.in_(accessible_territory_ids))
        if active_only:
            query = query.filter(Chemist.is_active == True)  # noqa: E712
        if search:
            pat = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Chemist.shop_name.ilike(pat),
                    Chemist.code.ilike(pat),
                    Chemist.phone.ilike(pat),
                )
            )
        return query.order_by(Chemist.shop_name.asc()).offset(skip).limit(limit).all()

    def get_chemist_by_id(self, chemist_id: int) -> Chemist | None:
        """Get chemist by ID."""
        return (
            self.db.query(Chemist)
            .filter(Chemist.id == chemist_id, Chemist.is_deleted == False)  # noqa: E712
            .first()
        )

    def create_chemist(
        self,
        shop_name: str,
        contact_person: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        dl_number: str | None = None,
        gstin: str | None = None,
        address: str | None = None,
        area_id: int | None = None,
        territory_id: int | None = None,
        pincode: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        created_by_user_id: int | None = None,
    ) -> Chemist:
        """Create new Chemist entity."""
        code = self._next_code("CHM", Chemist)
        chm = Chemist(
            code=code,
            shop_name=shop_name.strip(),
            contact_person=contact_person.strip() if contact_person else None,
            phone=phone.strip() if phone else None,
            email=email.strip().lower() if email else None,
            dl_number=dl_number.strip() if dl_number else None,
            gstin=gstin.strip().upper() if gstin else None,
            address=address.strip() if address else None,
            area_id=area_id,
            territory_id=territory_id,
            pincode=pincode.strip() if pincode else None,
            latitude=latitude,
            longitude=longitude,
            is_active=True,
            created_by=created_by_user_id,
        )
        self.db.add(chm)
        self.db.flush()
        return chm

    # STOCKISTS
    def list_stockists(
        self,
        accessible_territory_ids: Sequence[int] | None = None,
        search: str | None = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Stockist]:
        """List stockists with scope."""
        query = self.db.query(Stockist).filter(Stockist.is_deleted == False)  # noqa: E712
        if accessible_territory_ids is not None:
            query = query.filter(Stockist.territory_id.in_(accessible_territory_ids))
        if active_only:
            query = query.filter(Stockist.is_active == True)  # noqa: E712
        if search:
            pat = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Stockist.agency_name.ilike(pat),
                    Stockist.code.ilike(pat),
                    Stockist.phone.ilike(pat),
                )
            )
        return query.order_by(Stockist.agency_name.asc()).offset(skip).limit(limit).all()

    def get_stockist_by_id(self, stockist_id: int) -> Stockist | None:
        """Get stockist by ID."""
        return (
            self.db.query(Stockist)
            .filter(Stockist.id == stockist_id, Stockist.is_deleted == False)  # noqa: E712
            .first()
        )

    def create_stockist(
        self,
        agency_name: str,
        contact_person: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        dl_number: str | None = None,
        gstin: str | None = None,
        address: str | None = None,
        area_id: int | None = None,
        territory_id: int | None = None,
        pincode: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        credit_days: int = 30,
        created_by_user_id: int | None = None,
    ) -> Stockist:
        """Create new Stockist entity."""
        code = self._next_code("STK", Stockist)
        stk = Stockist(
            code=code,
            agency_name=agency_name.strip(),
            contact_person=contact_person.strip() if contact_person else None,
            phone=phone.strip() if phone else None,
            email=email.strip().lower() if email else None,
            dl_number=dl_number.strip() if dl_number else None,
            gstin=gstin.strip().upper() if gstin else None,
            address=address.strip() if address else None,
            area_id=area_id,
            territory_id=territory_id,
            pincode=pincode.strip() if pincode else None,
            latitude=latitude,
            longitude=longitude,
            credit_days=credit_days,
            is_active=True,
            created_by=created_by_user_id,
        )
        self.db.add(stk)
        self.db.flush()
        return stk
