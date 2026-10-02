"""Customer service layer with Haversine distance, scoping, and batch import."""

import csv
import io
import math
from collections.abc import Sequence

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.modules.customers.models import (
    Chemist,
    Doctor,
    Hospital,
    Stockist,
)
from app.modules.customers.repository import CustomerRepository
from app.modules.customers.schemas import (
    ChemistCreate,
    ChemistResponse,
    ChemistUpdate,
    DoctorCreate,
    DoctorResponse,
    DoctorUpdate,
    HospitalCreate,
    HospitalDoctorMapRequest,
    HospitalResponse,
    HospitalSummary,
    HospitalUpdate,
    ImportReportResponse,
    ImportRowError,
    NearbyCustomerItem,
    StockistCreate,
    StockistResponse,
    StockistUpdate,
)
from app.modules.territories.repository import TerritoryRepository
from app.modules.users.models import User


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two GPS coordinates in meters."""
    radius_earth_m = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return radius_earth_m * c


class CustomerService:
    """Business service for Doctors, Hospitals, Chemists, Stockists, and Nearby queries."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CustomerRepository(db)
        self.territory_repo = TerritoryRepository(db)
        self.settings = get_settings()

    def get_user_accessible_territories(self, current_user: User) -> Sequence[int] | None:
        """Resolve accessible territory IDs based on user role."""
        if current_user.role and current_user.role.code in ("ADMIN", "MANAGER"):
            return None  # Unrestricted access for admin and manager

        territories = self.territory_repo.get_user_territories(current_user.id)
        if not territories:
            # Fallback: if user has no assigned territory yet, allow access to all territories
            return None
        return [t.id for t in territories]

    # DOCTORS
    def list_doctors(
        self,
        current_user: User,
        search: str | None = None,
        specialization: str | None = None,
        category: str | None = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 50,
    ) -> list[DoctorResponse]:
        """List doctors respecting territory scoping."""
        t_ids = self.get_user_accessible_territories(current_user)
        doctors = self.repo.list_doctors(
            accessible_territory_ids=t_ids,
            search=search,
            specialization=specialization,
            category=category,
            active_only=active_only,
            skip=skip,
            limit=limit,
        )
        return [self.to_doctor_response(d) for d in doctors]

    def get_doctor_by_id(self, doctor_id: int, current_user: User) -> DoctorResponse:
        """Get doctor details."""
        doc = self.repo.get_doctor_by_id(doctor_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Doctor with ID {doctor_id} not found",
            )
        t_ids = self.get_user_accessible_territories(current_user)
        if t_ids is not None and doc.territory_id not in t_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Doctor is outside your assigned territory scope",
            )
        return self.to_doctor_response(doc)

    def create_doctor(self, payload: DoctorCreate, current_user: User) -> DoctorResponse:
        """Create new doctor."""
        doc = self.repo.create_doctor(
            full_name=payload.full_name,
            qualification=payload.qualification,
            specialization=payload.specialization,
            category=payload.category,
            phone=payload.phone,
            email=payload.email,
            clinic_name=payload.clinic_name,
            address=payload.address,
            area_id=payload.area_id,
            territory_id=payload.territory_id,
            pincode=payload.pincode,
            latitude=payload.latitude,
            longitude=payload.longitude,
            date_of_birth=payload.date_of_birth,
            anniversary_date=payload.anniversary_date,
            created_by_user_id=current_user.id,
        )
        self.db.commit()
        self.db.refresh(doc)
        return self.to_doctor_response(doc)

    def update_doctor(
        self, doctor_id: int, payload: DoctorUpdate, current_user: User
    ) -> DoctorResponse:
        """Update doctor."""
        doc = self.repo.get_doctor_by_id(doctor_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Doctor with ID {doctor_id} not found",
            )
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(doc, key, value)
        doc.updated_by = current_user.id
        self.db.commit()
        self.db.refresh(doc)
        return self.to_doctor_response(doc)

    def to_doctor_response(self, doc: Doctor) -> DoctorResponse:
        """Convert Doctor model to DoctorResponse with hospital mappings."""
        hospitals = [
            HospitalSummary(
                hospital_id=hd.hospital.id,
                hospital_name=hd.hospital.name,
                department=hd.department,
                visiting_hours=hd.visiting_hours,
                is_primary=hd.is_primary,
            )
            for hd in doc.hospital_doctors
            if hd.hospital
        ]
        return DoctorResponse(
            id=doc.id,
            code=doc.code,
            full_name=doc.full_name,
            qualification=doc.qualification,
            specialization=doc.specialization,
            category=doc.category,
            phone=doc.phone,
            email=doc.email,
            clinic_name=doc.clinic_name,
            address=doc.address,
            area_id=doc.area_id,
            territory_id=doc.territory_id,
            pincode=doc.pincode,
            latitude=doc.latitude,
            longitude=doc.longitude,
            date_of_birth=doc.date_of_birth,
            anniversary_date=doc.anniversary_date,
            is_active=doc.is_active,
            hospitals=hospitals,
            created_at=doc.created_at,
        )

    # HOSPITALS
    def list_hospitals(
        self,
        current_user: User,
        search: str | None = None,
        hospital_type: str | None = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 50,
    ) -> list[HospitalResponse]:
        """List hospitals."""
        t_ids = self.get_user_accessible_territories(current_user)
        hospitals = self.repo.list_hospitals(
            accessible_territory_ids=t_ids,
            search=search,
            hospital_type=hospital_type,
            active_only=active_only,
            skip=skip,
            limit=limit,
        )
        return [HospitalResponse.model_validate(h) for h in hospitals]

    def create_hospital(self, payload: HospitalCreate, current_user: User) -> HospitalResponse:
        """Create new hospital."""
        hsp = self.repo.create_hospital(
            name=payload.name,
            hospital_type=payload.type,
            contact_person=payload.contact_person,
            phone=payload.phone,
            email=payload.email,
            address=payload.address,
            area_id=payload.area_id,
            territory_id=payload.territory_id,
            pincode=payload.pincode,
            latitude=payload.latitude,
            longitude=payload.longitude,
            bed_count=payload.bed_count,
            created_by_user_id=current_user.id,
        )
        self.db.commit()
        self.db.refresh(hsp)
        return HospitalResponse.model_validate(hsp)

    def map_doctor_to_hospital(
        self, payload: HospitalDoctorMapRequest, current_user: User
    ) -> dict[str, str]:
        """Map a doctor to a hospital."""
        self.repo.map_doctor_to_hospital(
            hospital_id=payload.hospital_id,
            doctor_id=payload.doctor_id,
            department=payload.department,
            visiting_hours=payload.visiting_hours,
            is_primary=payload.is_primary,
        )
        self.db.commit()
        return {"message": "Doctor mapped to hospital successfully"}

    def get_hospital_by_id(self, hospital_id: int, current_user: User) -> HospitalResponse:
        """Get hospital by ID with territory scoping."""
        hsp = self.repo.get_hospital_by_id(hospital_id)
        if not hsp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hospital with ID {hospital_id} not found",
            )
        t_ids = self.get_user_accessible_territories(current_user)
        if t_ids is not None and hsp.territory_id is not None and hsp.territory_id not in t_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hospital is outside your assigned territory scope",
            )
        return HospitalResponse.model_validate(hsp)

    def update_hospital(
        self, hospital_id: int, payload: HospitalUpdate, current_user: User
    ) -> HospitalResponse:
        """Update hospital details."""
        hsp = self.repo.get_hospital_by_id(hospital_id)
        if not hsp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hospital with ID {hospital_id} not found",
            )
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(hsp, key, value)
        hsp.updated_by = current_user.id
        self.db.commit()
        self.db.refresh(hsp)
        return HospitalResponse.model_validate(hsp)

    # CHEMISTS
    def list_chemists(
        self,
        current_user: User,
        search: str | None = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ChemistResponse]:
        """List chemists."""
        t_ids = self.get_user_accessible_territories(current_user)
        chemists = self.repo.list_chemists(
            accessible_territory_ids=t_ids,
            search=search,
            active_only=active_only,
            skip=skip,
            limit=limit,
        )
        return [ChemistResponse.model_validate(c) for c in chemists]

    def create_chemist(self, payload: ChemistCreate, current_user: User) -> ChemistResponse:
        """Create chemist."""
        chm = self.repo.create_chemist(
            shop_name=payload.shop_name,
            contact_person=payload.contact_person,
            phone=payload.phone,
            email=payload.email,
            dl_number=payload.dl_number,
            gstin=payload.gstin,
            address=payload.address,
            area_id=payload.area_id,
            territory_id=payload.territory_id,
            pincode=payload.pincode,
            latitude=payload.latitude,
            longitude=payload.longitude,
            created_by_user_id=current_user.id,
        )
        self.db.commit()
        self.db.refresh(chm)
        return ChemistResponse.model_validate(chm)

    def get_chemist_by_id(self, chemist_id: int, current_user: User) -> ChemistResponse:
        """Get chemist by ID with territory scoping."""
        chm = self.repo.get_chemist_by_id(chemist_id)
        if not chm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chemist with ID {chemist_id} not found",
            )
        t_ids = self.get_user_accessible_territories(current_user)
        if t_ids is not None and chm.territory_id is not None and chm.territory_id not in t_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Chemist is outside your assigned territory scope",
            )
        return ChemistResponse.model_validate(chm)

    def update_chemist(
        self, chemist_id: int, payload: ChemistUpdate, current_user: User
    ) -> ChemistResponse:
        """Update chemist details."""
        chm = self.repo.get_chemist_by_id(chemist_id)
        if not chm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chemist with ID {chemist_id} not found",
            )
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(chm, key, value)
        chm.updated_by = current_user.id
        self.db.commit()
        self.db.refresh(chm)
        return ChemistResponse.model_validate(chm)

    # STOCKISTS
    def list_stockists(
        self,
        current_user: User,
        search: str | None = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 50,
    ) -> list[StockistResponse]:
        """List stockists."""
        t_ids = self.get_user_accessible_territories(current_user)
        stockists = self.repo.list_stockists(
            accessible_territory_ids=t_ids,
            search=search,
            active_only=active_only,
            skip=skip,
            limit=limit,
        )
        return [StockistResponse.model_validate(s) for s in stockists]

    def create_stockist(self, payload: StockistCreate, current_user: User) -> StockistResponse:
        """Create stockist."""
        stk = self.repo.create_stockist(
            agency_name=payload.agency_name,
            contact_person=payload.contact_person,
            phone=payload.phone,
            email=payload.email,
            dl_number=payload.dl_number,
            gstin=payload.gstin,
            address=payload.address,
            area_id=payload.area_id,
            territory_id=payload.territory_id,
            pincode=payload.pincode,
            latitude=payload.latitude,
            longitude=payload.longitude,
            credit_days=payload.credit_days,
            created_by_user_id=current_user.id,
        )
        self.db.commit()
        self.db.refresh(stk)
        return StockistResponse.model_validate(stk)

    def get_stockist_by_id(self, stockist_id: int, current_user: User) -> StockistResponse:
        """Get stockist by ID with territory scoping."""
        stk = self.repo.get_stockist_by_id(stockist_id)
        if not stk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stockist with ID {stockist_id} not found",
            )
        t_ids = self.get_user_accessible_territories(current_user)
        if t_ids is not None and stk.territory_id is not None and stk.territory_id not in t_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Stockist is outside your assigned territory scope",
            )
        return StockistResponse.model_validate(stk)

    def update_stockist(
        self, stockist_id: int, payload: StockistUpdate, current_user: User
    ) -> StockistResponse:
        """Update stockist details."""
        stk = self.repo.get_stockist_by_id(stockist_id)
        if not stk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stockist with ID {stockist_id} not found",
            )
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(stk, key, value)
        stk.updated_by = current_user.id
        self.db.commit()
        self.db.refresh(stk)
        return StockistResponse.model_validate(stk)

    # NEARBY CUSTOMERS (P2-B-05)
    def get_nearby_customers(
        self,
        latitude: float,
        longitude: float,
        radius_meters: float = 2000.0,
        current_user: User | None = None,
    ) -> list[NearbyCustomerItem]:
        """Find doctors, chemists, stockists, and hospitals within radius_meters."""
        results: list[NearbyCustomerItem] = []
        doc_radius = self.settings.DEFAULT_GEOFENCE_DOCTOR_RADIUS_METERS
        chm_radius = self.settings.DEFAULT_GEOFENCE_CHEMIST_RADIUS_METERS

        # 1. Doctors
        doctors = (
            self.db.query(Doctor)
            .filter(
                Doctor.is_active == True,  # noqa: E712
                Doctor.is_deleted == False,  # noqa: E712
                Doctor.latitude.isnot(None),
                Doctor.longitude.isnot(None),
            )
            .all()
        )
        for d in doctors:
            if d.latitude is not None and d.longitude is not None:
                dist = haversine_distance_meters(latitude, longitude, d.latitude, d.longitude)
                if dist <= radius_meters:
                    results.append(
                        NearbyCustomerItem(
                            id=d.id,
                            customer_type="DOCTOR",
                            name=f"Dr. {d.full_name}",
                            category_or_type=d.specialization or d.category,
                            address=d.clinic_name or d.address,
                            phone=d.phone,
                            latitude=d.latitude,
                            longitude=d.longitude,
                            distance_meters=round(dist, 1),
                            in_geofence=dist <= doc_radius,
                        )
                    )

        # 2. Chemists
        chemists = (
            self.db.query(Chemist)
            .filter(
                Chemist.is_active == True,  # noqa: E712
                Chemist.is_deleted == False,  # noqa: E712
                Chemist.latitude.isnot(None),
                Chemist.longitude.isnot(None),
            )
            .all()
        )
        for c in chemists:
            if c.latitude is not None and c.longitude is not None:
                dist = haversine_distance_meters(latitude, longitude, c.latitude, c.longitude)
                if dist <= radius_meters:
                    results.append(
                        NearbyCustomerItem(
                            id=c.id,
                            customer_type="CHEMIST",
                            name=c.shop_name,
                            category_or_type="Chemist",
                            address=c.address,
                            phone=c.phone,
                            latitude=c.latitude,
                            longitude=c.longitude,
                            distance_meters=round(dist, 1),
                            in_geofence=dist <= chm_radius,
                        )
                    )

        # 3. Hospitals
        hospitals = (
            self.db.query(Hospital)
            .filter(
                Hospital.is_active == True,  # noqa: E712
                Hospital.is_deleted == False,  # noqa: E712
                Hospital.latitude.isnot(None),
                Hospital.longitude.isnot(None),
            )
            .all()
        )
        for h in hospitals:
            if h.latitude is not None and h.longitude is not None:
                dist = haversine_distance_meters(latitude, longitude, h.latitude, h.longitude)
                if dist <= radius_meters:
                    results.append(
                        NearbyCustomerItem(
                            id=h.id,
                            customer_type="HOSPITAL",
                            name=h.name,
                            category_or_type=h.type,
                            address=h.address,
                            phone=h.phone,
                            latitude=h.latitude,
                            longitude=h.longitude,
                            distance_meters=round(dist, 1),
                            in_geofence=dist <= doc_radius,
                        )
                    )

        # 4. Stockists
        stockists = (
            self.db.query(Stockist)
            .filter(
                Stockist.is_active == True,  # noqa: E712
                Stockist.is_deleted == False,  # noqa: E712
                Stockist.latitude.isnot(None),
                Stockist.longitude.isnot(None),
            )
            .all()
        )
        for s in stockists:
            if s.latitude is not None and s.longitude is not None:
                dist = haversine_distance_meters(latitude, longitude, s.latitude, s.longitude)
                if dist <= radius_meters:
                    results.append(
                        NearbyCustomerItem(
                            id=s.id,
                            customer_type="STOCKIST",
                            name=s.agency_name,
                            category_or_type="Stockist",
                            address=s.address,
                            phone=s.phone,
                            latitude=s.latitude,
                            longitude=s.longitude,
                            distance_meters=round(dist, 1),
                            in_geofence=dist <= chm_radius,
                        )
                    )

        # Sort ascending by closest distance
        results.sort(key=lambda x: x.distance_meters)
        return results

    # CSV/EXCEL BATCH IMPORT (P2-B-06)
    def import_customers_csv(
        self,
        csv_content: str,
        entity_type: str,
        current_user: User,
    ) -> ImportReportResponse:
        """Parse CSV rows and import customer entities with row-by-row error report."""
        f = io.StringIO(csv_content)
        reader = csv.DictReader(f)

        imported_count = 0
        failed_count = 0
        errors: list[ImportRowError] = []
        row_num = 1

        for row in reader:
            row_num += 1
            try:
                if entity_type.upper() == "DOCTOR":
                    name = row.get("full_name") or row.get("name")
                    if not name or not name.strip():
                        raise ValueError("full_name is required")
                    lat = float(row["latitude"]) if row.get("latitude") else None
                    lon = float(row["longitude"]) if row.get("longitude") else None
                    self.repo.create_doctor(
                        full_name=name.strip(),
                        specialization=row.get("specialization"),
                        category=row.get("category", "A"),
                        phone=row.get("phone"),
                        clinic_name=row.get("clinic_name"),
                        address=row.get("address"),
                        latitude=lat,
                        longitude=lon,
                        created_by_user_id=current_user.id,
                    )
                elif entity_type.upper() == "CHEMIST":
                    shop_name = row.get("shop_name") or row.get("name")
                    if not shop_name or not shop_name.strip():
                        raise ValueError("shop_name is required")
                    lat = float(row["latitude"]) if row.get("latitude") else None
                    lon = float(row["longitude"]) if row.get("longitude") else None
                    self.repo.create_chemist(
                        shop_name=shop_name.strip(),
                        contact_person=row.get("contact_person"),
                        phone=row.get("phone"),
                        address=row.get("address"),
                        latitude=lat,
                        longitude=lon,
                        created_by_user_id=current_user.id,
                    )
                imported_count += 1
            except Exception as e:
                failed_count += 1
                errors.append(
                    ImportRowError(
                        row_number=row_num,
                        entity=entity_type,
                        error_message=str(e),
                    )
                )

        self.db.commit()
        return ImportReportResponse(
            total_rows=imported_count + failed_count,
            imported_count=imported_count,
            failed_count=failed_count,
            errors=errors,
        )
