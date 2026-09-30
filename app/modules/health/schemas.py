"""Health module response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Schema for basic service health check."""

    status: str = Field(..., examples=["ok"])
    version: str = Field(..., examples=["0.1.0"])
    timestamp: datetime
    environment: str = Field(..., examples=["development"])


class ReadinessComponent(BaseModel):
    """Component readiness status."""

    status: str
    detail: str | None = None


class ReadyResponse(BaseModel):
    """Schema for detailed system readiness."""

    status: str = Field(..., examples=["ready"])
    uptime_seconds: float
    components: dict[str, ReadinessComponent]
