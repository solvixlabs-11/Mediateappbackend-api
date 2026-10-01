"""Customer Pydantic schemas (Doctors, Hospitals, Chemists, Stockists)."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class HospitalSummary(BaseModel):
    """Summary of hospital mapping for doctor."""

    model_config = ConfigDict(from_attributes=True)

    hospital_id: int
    hospital_name: str
    department: str | None = None
    visiting_hours: str | None = None
    is_primary: bool


class DoctorResponse(BaseModel):
    """Doctor details response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    full_name: str
    qualification: str | None = None
    specialization: str | None = None
    category: str
    phone: str | None = None
    email: str | None = None
    clinic_name: str | None = None
    address: str | None = None
    area_id: int | None = None
    territory_id: int | None = None
    pincode: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    date_of_birth: date | None = None
    anniversary_date: date | None = None
    is_active: bool
    hospitals: list[HospitalSummary] = []
    created_at: datetime


class DoctorCreate(BaseModel):
    """Payload to create a Doctor."""

    full_name: str = Field(..., max_length=150)
    qualification: str | None = Field(default=None, max_length=100)
    specialization: str | None = Field(default=None, max_length=100)
    category: str = Field(default="A", max_length=50)
    phone: str | None = Field(default=None, max_length=25)
    email: EmailStr | None = None
    clinic_name: str | None = Field(default=None, max_length=150)
    address: str | None = Field(default=None, max_length=255)
    area_id: int | None = None
    territory_id: int | None = None
    pincode: str | None = Field(default=None, max_length=10)
    latitude: float | None = None
    longitude: float | None = None
    date_of_birth: date | None = None
    anniversary_date: date | None = None


class DoctorUpdate(BaseModel):
    """Payload to update a Doctor."""

    full_name: str | None = Field(default=None, max_length=150)
    qualification: str | None = None
    specialization: str | None = None
    category: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    clinic_name: str | None = None
    address: str | None = None
    area_id: int | None = None
    territory_id: int | None = None
    pincode: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    date_of_birth: date | None = None
    anniversary_date: date | None = None
    is_active: bool | None = None


# Hospitals
class HospitalResponse(BaseModel):
    """Hospital response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    type: str
    contact_person: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    area_id: int | None = None
    territory_id: int | None = None
    pincode: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    bed_count: int | None = None
    is_active: bool
    created_at: datetime


class HospitalCreate(BaseModel):
    """Payload to create a Hospital."""

    name: str = Field(..., max_length=150)
    type: str = Field(default="General", max_length=50)
    contact_person: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=25)
    email: EmailStr | None = None
    address: str | None = Field(default=None, max_length=255)
    area_id: int | None = None
    territory_id: int | None = None
    pincode: str | None = Field(default=None, max_length=10)
    latitude: float | None = None
    longitude: float | None = None
    bed_count: int | None = None


class HospitalUpdate(BaseModel):
    """Payload to update a Hospital."""

    name: str | None = None
    type: str | None = None
    contact_person: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    area_id: int | None = None
    territory_id: int | None = None
    pincode: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    bed_count: int | None = None
    is_active: bool | None = None


class HospitalDoctorMapRequest(BaseModel):
    """Map a Doctor to a Hospital."""

    hospital_id: int
    doctor_id: int
    department: str | None = Field(default=None, max_length=100)
    visiting_hours: str | None = Field(default=None, max_length=100)
    is_primary: bool = False


# Chemists
class ChemistResponse(BaseModel):
    """Chemist response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    shop_name: str
    contact_person: str | None = None
    phone: str | None = None
    email: str | None = None
    dl_number: str | None = None
    gstin: str | None = None
    address: str | None = None
    area_id: int | None = None
    territory_id: int | None = None
    pincode: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    is_active: bool
    created_at: datetime


class ChemistCreate(BaseModel):
    """Payload to create a Chemist."""

    shop_name: str = Field(..., max_length=150)
    contact_person: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=25)
    email: EmailStr | None = None
    dl_number: str | None = Field(default=None, max_length=100)
    gstin: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=255)
    area_id: int | None = None
    territory_id: int | None = None
    pincode: str | None = Field(default=None, max_length=10)
    latitude: float | None = None
    longitude: float | None = None


class ChemistUpdate(BaseModel):
    """Payload to update a Chemist."""

    shop_name: str | None = None
    contact_person: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    dl_number: str | None = None
    gstin: str | None = None
    address: str | None = None
    area_id: int | None = None
    territory_id: int | None = None
    pincode: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    is_active: bool | None = None


# Stockists
class StockistResponse(BaseModel):
    """Stockist response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    agency_name: str
    contact_person: str | None = None
    phone: str | None = None
    email: str | None = None
    dl_number: str | None = None
    gstin: str | None = None
    address: str | None = None
    area_id: int | None = None
    territory_id: int | None = None
    pincode: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    credit_days: int
    is_active: bool
    created_at: datetime


class StockistCreate(BaseModel):
    """Payload to create a Stockist."""

    agency_name: str = Field(..., max_length=150)
    contact_person: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=25)
    email: EmailStr | None = None
    dl_number: str | None = Field(default=None, max_length=100)
    gstin: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=255)
    area_id: int | None = None
    territory_id: int | None = None
    pincode: str | None = Field(default=None, max_length=10)
    latitude: float | None = None
    longitude: float | None = None
    credit_days: int = 30


class StockistUpdate(BaseModel):
    """Payload to update a Stockist."""

    agency_name: str | None = None
    contact_person: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    dl_number: str | None = None
    gstin: str | None = None
    address: str | None = None
    area_id: int | None = None
    territory_id: int | None = None
    pincode: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    credit_days: int | None = None
    is_active: bool | None = None


# Nearby Customers
class NearbyCustomerItem(BaseModel):
    """Customer found nearby using Haversine calculation."""

    id: int
    customer_type: str = Field(..., description="DOCTOR, CHEMIST, STOCKIST, HOSPITAL")
    name: str
    category_or_type: str | None = None
    address: str | None = None
    phone: str | None = None
    latitude: float
    longitude: float
    distance_meters: float
    in_geofence: bool


class ImportRowError(BaseModel):
    """Error encountered during customer batch import."""

    row_number: int
    entity: str
    error_message: str


class ImportReportResponse(BaseModel):
    """Summary report of Excel/CSV batch import."""

    total_rows: int
    imported_count: int
    failed_count: int
    errors: list[ImportRowError] = []
