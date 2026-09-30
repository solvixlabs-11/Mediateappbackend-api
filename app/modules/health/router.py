"""Health endpoints router."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.health.schemas import HealthResponse, ReadyResponse
from app.modules.health.service import HealthService

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="Returns basic liveness status and version of the API.",
)
def get_health() -> HealthResponse:
    """Return basic health status."""
    return HealthService.get_health()


@router.get(
    "/ready",
    response_model=ReadyResponse,
    summary="Service Readiness Check",
    description="Returns detailed readiness checks for external services like SQL Server.",
)
def get_ready(db: Session = Depends(get_db)) -> ReadyResponse:
    """Return dependency readiness status."""
    return HealthService.get_readiness(db=db)
