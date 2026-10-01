"""Territory Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.masters.schemas import AreaResponse


class TerritoryResponse(BaseModel):
    """Territory response with mapped areas."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    headquarters: str
    state_id: int | None = None
    description: str | None = None
    is_active: bool
    areas: list[AreaResponse] = []
    created_at: datetime


class TerritoryCreate(BaseModel):
    """Payload to create a Territory."""

    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=50)
    headquarters: str = Field(..., max_length=100)
    state_id: int | None = None
    description: str | None = Field(default=None, max_length=255)
    area_ids: list[int] = Field(default_factory=list)


class TerritoryUpdate(BaseModel):
    """Payload to update a Territory."""

    name: str | None = Field(default=None, max_length=100)
    headquarters: str | None = Field(default=None, max_length=100)
    state_id: int | None = None
    description: str | None = Field(default=None, max_length=255)
    area_ids: list[int] | None = None
    is_active: bool | None = None


class AssignTerritoryRequest(BaseModel):
    """Request to assign an MR or Manager to a Territory."""

    user_id: int


class TerritoryAssignmentResponse(BaseModel):
    """Record of user territory allocation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    user_name: str
    territory_id: int
    territory_name: str
    assigned_at: datetime
    unassigned_at: datetime | None = None
    is_active: bool
