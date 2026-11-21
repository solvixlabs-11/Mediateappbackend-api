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
    territory_id: int
    assigned_at: datetime
    unassigned_at: datetime | None = None


class TerritoryTreeNode(BaseModel):
    """Hierarchical territory org chart node."""

    id: int | str
    code: str
    name: str
    headquarters: str | None = None
    level: str = "TERRITORY"  # ROOT, STATE, TERRITORY
    is_active: bool = True
    children: list["TerritoryTreeNode"] = []


class TerritoryTreeResponse(BaseModel):
    """Complete territory hierarchy tree with total nodes count."""

    total_count: int
    root: TerritoryTreeNode
