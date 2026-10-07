"""Customers REST HTTP endpoints (Doctors, Hospitals, Chemists, Stockists, Nearby, Import)."""

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_permission
from app.db.session import get_db
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
    HospitalUpdate,
    ImportReportResponse,
    NearbyCustomerItem,
    StockistCreate,
    StockistResponse,
    StockistUpdate,
)
from app.modules.customers.service import CustomerService
from app.modules.users.models import User

router = APIRouter(prefix="/customers", tags=["Customers"])


# NEARBY (P2-B-05)
@router.get(
    "/nearby",
    response_model=list[NearbyCustomerItem],
    summary="Get nearby customers within radius using Haversine calculation",
)
def get_nearby_customers(
    latitude: float = Query(..., description="Current device latitude"),
    longitude: float = Query(..., description="Current device longitude"),
    radius_meters: float = Query(
        default=2000.0, ge=50, le=50000, description="Search radius in meters"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[NearbyCustomerItem]:
    """Calculate GPS distances and return nearby customers sorted by proximity."""
    service = CustomerService(db)
    return service.get_nearby_customers(
        latitude=latitude,
        longitude=longitude,
        radius_meters=radius_meters,
        current_user=current_user,
    )


# BATCH IMPORT (P2-B-06)
@router.post(
    "/import",
    response_model=ImportReportResponse,
    summary="Import customer entities from CSV file",
)
async def import_customers(
    entity_type: str = Query(..., description="DOCTOR or CHEMIST"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("customers:write")),
) -> ImportReportResponse:
    """Batch upload customers from CSV with row-by-row error report."""
    content_bytes = await file.read()
    csv_str = content_bytes.decode("utf-8-sig")
    service = CustomerService(db)
    return service.import_customers_csv(
        csv_content=csv_str,
        entity_type=entity_type,
        current_user=current_user,
    )


# DOCTORS
@router.get(
    "/doctors",
    response_model=list[DoctorResponse],
    summary="List doctors with territory scoping and filters",
)
def list_doctors(
    search: str | None = Query(default=None),
    specialization: str | None = Query(default=None),
    category: str | None = Query(default=None),
    active_only: bool = Query(default=True),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DoctorResponse]:
    """Fetch doctors list."""
    service = CustomerService(db)
    return service.list_doctors(
        current_user=current_user,
        search=search,
        specialization=specialization,
        category=category,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/doctors",
    response_model=DoctorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new doctor",
)
def create_doctor(
    payload: DoctorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("customers:write")),
) -> DoctorResponse:
    """Create a new doctor."""
    service = CustomerService(db)
    return service.create_doctor(payload, current_user)


@router.get(
    "/doctors/{doctor_id}",
    response_model=DoctorResponse,
    summary="Get doctor details by ID",
)
def get_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DoctorResponse:
    """Get doctor details."""
    service = CustomerService(db)
    return service.get_doctor_by_id(doctor_id, current_user)


@router.put(
    "/doctors/{doctor_id}",
    response_model=DoctorResponse,
    summary="Update doctor details",
)
def update_doctor(
    doctor_id: int,
    payload: DoctorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("customers:write")),
) -> DoctorResponse:
    """Update doctor details."""
    service = CustomerService(db)
    return service.update_doctor(doctor_id, payload, current_user)


# HOSPITALS
@router.get(
    "/hospitals",
    response_model=list[HospitalResponse],
    summary="List hospitals",
)
def list_hospitals(
    search: str | None = Query(default=None),
    type: str | None = Query(default=None),
    active_only: bool = Query(default=True),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[HospitalResponse]:
    """Fetch hospitals list."""
    service = CustomerService(db)
    return service.list_hospitals(
        current_user=current_user,
        search=search,
        hospital_type=type,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/hospitals",
    response_model=HospitalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new hospital",
)
def create_hospital(
    payload: HospitalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("customers:write")),
) -> HospitalResponse:
    """Create a new hospital."""
    service = CustomerService(db)
    return service.create_hospital(payload, current_user)


@router.get(
    "/hospitals/{hospital_id}",
    response_model=HospitalResponse,
    summary="Get hospital details by ID",
)
def get_hospital(
    hospital_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HospitalResponse:
    """Get hospital details."""
    service = CustomerService(db)
    return service.get_hospital_by_id(hospital_id, current_user)


@router.put(
    "/hospitals/{hospital_id}",
    response_model=HospitalResponse,
    summary="Update hospital details",
)
def update_hospital(
    hospital_id: int,
    payload: HospitalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("customers:write")),
) -> HospitalResponse:
    """Update hospital details."""
    service = CustomerService(db)
    return service.update_hospital(hospital_id, payload, current_user)


@router.post(
    "/hospitals/map-doctor",
    summary="Map doctor to hospital",
)
def map_doctor_to_hospital(
    payload: HospitalDoctorMapRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("customers:write")),
) -> dict[str, str]:
    """Associate a doctor with a hospital."""
    service = CustomerService(db)
    return service.map_doctor_to_hospital(payload, current_user)


# CHEMISTS
@router.get(
    "/chemists",
    response_model=list[ChemistResponse],
    summary="List chemists",
)
def list_chemists(
    search: str | None = Query(default=None),
    active_only: bool = Query(default=True),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ChemistResponse]:
    """Fetch chemists list."""
    service = CustomerService(db)
    return service.list_chemists(
        current_user=current_user,
        search=search,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/chemists",
    response_model=ChemistResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new chemist",
)
def create_chemist(
    payload: ChemistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("customers:write")),
) -> ChemistResponse:
    """Create a new chemist."""
    service = CustomerService(db)
    return service.create_chemist(payload, current_user)


@router.get(
    "/chemists/{chemist_id}",
    response_model=ChemistResponse,
    summary="Get chemist details by ID",
)
def get_chemist(
    chemist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChemistResponse:
    """Get chemist details."""
    service = CustomerService(db)
    return service.get_chemist_by_id(chemist_id, current_user)


@router.put(
    "/chemists/{chemist_id}",
    response_model=ChemistResponse,
    summary="Update chemist details",
)
def update_chemist(
    chemist_id: int,
    payload: ChemistUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("customers:write")),
) -> ChemistResponse:
    """Update chemist details."""
    service = CustomerService(db)
    return service.update_chemist(chemist_id, payload, current_user)


# STOCKISTS
@router.get(
    "/stockists",
    response_model=list[StockistResponse],
    summary="List stockists",
)
def list_stockists(
    search: str | None = Query(default=None),
    active_only: bool = Query(default=True),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[StockistResponse]:
    """Fetch stockists list."""
    service = CustomerService(db)
    return service.list_stockists(
        current_user=current_user,
        search=search,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/stockists",
    response_model=StockistResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new stockist",
)
def create_stockist(
    payload: StockistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("customers:write")),
) -> StockistResponse:
    """Create a new stockist."""
    service = CustomerService(db)
    return service.create_stockist(payload, current_user)


@router.get(
    "/stockists/{stockist_id}",
    response_model=StockistResponse,
    summary="Get stockist details by ID",
)
def get_stockist(
    stockist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StockistResponse:
    """Get stockist details."""
    service = CustomerService(db)
    return service.get_stockist_by_id(stockist_id, current_user)


@router.put(
    "/stockists/{stockist_id}",
    response_model=StockistResponse,
    summary="Update stockist details",
)
def update_stockist(
    stockist_id: int,
    payload: StockistUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("customers:write")),
) -> StockistResponse:
    """Update stockist details."""
    service = CustomerService(db)
    return service.update_stockist(stockist_id, payload, current_user)
