import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RoleResponse(BaseModel):
    """Role summary response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str | None = None


class ManagerSummary(BaseModel):
    """Manager summary response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    phone: str | None = None


class UserResponse(BaseModel):
    """Comprehensive user account response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    phone: str | None = None
    role_id: int
    role: RoleResponse
    is_active: bool
    force_password_change: bool
    failed_login_attempts: int
    locked_until: datetime | None = None
    last_login_at: datetime | None = None
    profile_picture_file_id: int | None = None
    profile_picture_url: str | None = None
    current_manager: ManagerSummary | None = None
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    """Paginated list of users."""

    items: list[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserCreate(BaseModel):
    """Create new user account."""

    email: EmailStr
    full_name: str = Field(min_length=2, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    role_code: str = Field(..., description="Role code: ADMIN, MANAGER, or MR")
    password: str = Field(min_length=6, description="Initial password")
    force_password_change: bool = False
    manager_id: int | None = Field(
        default=None, description="Assigned Manager ID if creating an MR"
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password contains uppercase, lowercase, number, and special character."""
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter (A-Z)")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter (a-z)")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number (0-9)")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character (@$!%*?&)")
        return v


class UserUpdate(BaseModel):
    """Update user account attributes."""

    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    role_code: str | None = None
    password: str | None = Field(default=None, min_length=6)
    profile_picture_file_id: int | None = None


class UserStatusUpdate(BaseModel):
    """Activate or deactivate user account."""

    is_active: bool
    reason: str | None = Field(default=None, max_length=255)


class AssignManagerRequest(BaseModel):
    """Request to assign or reassign an MR to a Manager."""

    manager_id: int


class ManagerMRAssignmentResponse(BaseModel):
    """Historical or active assignment record."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    manager_id: int
    manager_name: str
    mr_id: int
    mr_name: str
    assigned_at: datetime
    unassigned_at: datetime | None = None
    is_active: bool


class ProfileUpdateRequest(BaseModel):
    """Self-service profile update request."""

    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    profile_picture_file_id: int | None = None
