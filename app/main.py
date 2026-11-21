"""FastAPI application entrypoint."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.logging import get_logger, setup_logging
from app.core.request_id import RequestIdMiddleware
from app.modules.approvals.router import router as approvals_router
from app.modules.attendance.router import router as attendance_router
from app.modules.audit.router import router as audit_router
from app.modules.auth.router import router as auth_router
from app.modules.calendar.router import router as calendar_router
from app.modules.company_profile.router import router as company_profile_router
from app.modules.customers.router import router as customers_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.dcr.admin_visits_router import router as admin_visits_router
from app.modules.dcr.router import router as dcr_router
from app.modules.expenses.router import limits_router as expense_limits_router
from app.modules.expenses.router import router as expenses_router
from app.modules.files.router import router as files_router
from app.modules.financial_years.router import router as financial_years_router
from app.modules.health.router import router as health_router
from app.modules.leaves.router import router as leaves_router
from app.modules.mappings.router import router as mappings_router
from app.modules.masters.router import router as masters_router
from app.modules.meetings.router import router as meetings_router
from app.modules.mobile_registrations.router import router as mobile_registrations_router
from app.modules.navigation.router import router as navigation_router
from app.modules.notifications.router import router as notifications_router
from app.modules.orders.router import router as orders_router
from app.modules.products.router import router as products_router
from app.modules.releases.router import router as releases_router
from app.modules.reports.router import router as reports_router
from app.modules.settings.router import router as settings_router
from app.modules.stock.router import router as stock_router
from app.modules.targets.router import router as targets_router
from app.modules.tasks.router import router as tasks_router
from app.modules.territories.router import router as territories_router
from app.modules.tours.router import router as tours_router
from app.modules.users.router import router as users_router
from app.modules.workflow.router import router as workflow_router

setup_logging()
logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown events."""
    logger.info(
        "Starting %s v%s in %s mode",
        settings.PROJECT_NAME,
        settings.VERSION,
        settings.ENVIRONMENT,
    )
    yield
    logger.info("Shutting down %s", settings.PROJECT_NAME)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
)

# Middlewares
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handlers
register_error_handlers(app)


@app.get("", include_in_schema=False)
@app.get("/", include_in_schema=False)
def root_index() -> dict[str, str]:
    """Root endpoint showing API metadata and Swagger docs location."""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": f"{settings.API_V1_PREFIX}/docs",
        "health_url": "/health",
        "api_v1": settings.API_V1_PREFIX,
    }


@app.get("/docs", include_in_schema=False)
def docs_shortcut() -> RedirectResponse:
    """Shortcut redirect to versioned Swagger documentation."""
    return RedirectResponse(url=f"{settings.API_V1_PREFIX}/docs")


# Include Routers
# Root health probe (e.g. for docker / load balancer)
app.include_router(health_router)
# Versioned API routes
app.include_router(health_router, prefix=settings.API_V1_PREFIX)
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(users_router, prefix=settings.API_V1_PREFIX)
app.include_router(files_router, prefix=settings.API_V1_PREFIX)
app.include_router(masters_router, prefix=settings.API_V1_PREFIX)
app.include_router(territories_router, prefix=settings.API_V1_PREFIX)
app.include_router(customers_router, prefix=settings.API_V1_PREFIX)
app.include_router(attendance_router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboard_router, prefix=settings.API_V1_PREFIX)
app.include_router(navigation_router, prefix=settings.API_V1_PREFIX)
app.include_router(dcr_router, prefix=settings.API_V1_PREFIX)
app.include_router(approvals_router, prefix=settings.API_V1_PREFIX)
app.include_router(tours_router, prefix=settings.API_V1_PREFIX)
app.include_router(expenses_router, prefix=settings.API_V1_PREFIX)
app.include_router(leaves_router, prefix=settings.API_V1_PREFIX)
app.include_router(tasks_router, prefix=settings.API_V1_PREFIX)
app.include_router(notifications_router, prefix=settings.API_V1_PREFIX)
app.include_router(reports_router, prefix=settings.API_V1_PREFIX)
app.include_router(products_router, prefix=settings.API_V1_PREFIX)
app.include_router(orders_router, prefix=settings.API_V1_PREFIX)
app.include_router(targets_router, prefix=settings.API_V1_PREFIX)
app.include_router(workflow_router, prefix=settings.API_V1_PREFIX)
app.include_router(settings_router, prefix=settings.API_V1_PREFIX)
app.include_router(audit_router, prefix=settings.API_V1_PREFIX)
app.include_router(expense_limits_router, prefix=settings.API_V1_PREFIX)
app.include_router(mappings_router, prefix=settings.API_V1_PREFIX)
app.include_router(company_profile_router, prefix=settings.API_V1_PREFIX)
app.include_router(meetings_router, prefix=settings.API_V1_PREFIX)
app.include_router(calendar_router, prefix=settings.API_V1_PREFIX)
app.include_router(mobile_registrations_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_visits_router, prefix=settings.API_V1_PREFIX)
app.include_router(stock_router, prefix=settings.API_V1_PREFIX)
app.include_router(financial_years_router, prefix=settings.API_V1_PREFIX)
app.include_router(releases_router, prefix=settings.API_V1_PREFIX)
