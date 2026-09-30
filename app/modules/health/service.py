"""Health and readiness domain service."""

import time
from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.modules.health.schemas import HealthResponse, ReadinessComponent, ReadyResponse

_START_TIME = time.time()
settings = get_settings()


class HealthService:
    """Service to evaluate system health and component readiness."""

    @staticmethod
    def get_health() -> HealthResponse:
        """Return basic liveness state."""
        return HealthResponse(
            status="ok",
            version=settings.VERSION,
            timestamp=datetime.now(UTC),
            environment=settings.ENVIRONMENT,
        )

    @staticmethod
    def get_readiness(db: Session | None = None) -> ReadyResponse:
        """Check all critical backend dependencies."""
        components: dict[str, ReadinessComponent] = {}
        all_ready = True

        # Check DB connectivity
        if db is not None:
            try:
                db.execute(text("SELECT 1"))
                components["database"] = ReadinessComponent(status="healthy", detail="connected")
            except Exception as exc:
                all_ready = False
                components["database"] = ReadinessComponent(status="unhealthy", detail=str(exc))
        else:
            components["database"] = ReadinessComponent(status="skipped", detail="no session")

        uptime = round(time.time() - _START_TIME, 2)
        return ReadyResponse(
            status="ready" if all_ready else "degraded",
            uptime_seconds=uptime,
            components=components,
        )
