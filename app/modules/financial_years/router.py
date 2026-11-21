"""Financial Year API Router."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, require_permission
from app.modules.users.models import User
from app.modules.financial_years.service import FinancialYearService
from app.modules.financial_years.schemas import (
    FinancialYearCreate,
    FinancialYearUpdate,
    FinancialYearResponse,
    FinancialYearListResponse,
)

router = APIRouter(prefix="/financial-years", tags=["Financial Years"])


@router.get(
    "",
    response_model=FinancialYearListResponse,
    summary="List financial years",
    dependencies=[Depends(get_current_user)],
)
def list_financial_years(
    search: str | None = Query(None, description="Search by name or code"),
    is_current: bool | None = Query(None, description="Filter current active fiscal year"),
    is_active: bool | None = Query(None, description="Filter active status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return FinancialYearService.list_years(
        db=db,
        search=search,
        is_current=is_current,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/current",
    response_model=FinancialYearResponse | None,
    summary="Get currently active financial year",
    dependencies=[Depends(get_current_user)],
)
def get_current_financial_year(
    db: Session = Depends(get_db),
):
    record = FinancialYearService.get_current(db)
    if not record:
        return None
    return FinancialYearResponse.model_validate(record)


@router.get(
    "/{year_id}",
    response_model=FinancialYearResponse,
    summary="Get single financial year details",
    dependencies=[Depends(get_current_user)],
)
def get_financial_year(
    year_id: int,
    db: Session = Depends(get_db),
):
    record = FinancialYearService.get_by_id(db, year_id)
    return FinancialYearResponse.model_validate(record)


@router.post(
    "",
    response_model=FinancialYearResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create financial year",
    dependencies=[Depends(require_permission("settings:write"))],
)
def create_financial_year(
    payload: FinancialYearCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return FinancialYearService.create(db=db, payload=payload, user_id=current_user.id)


@router.put(
    "/{year_id}",
    response_model=FinancialYearResponse,
    summary="Update financial year",
    dependencies=[Depends(require_permission("settings:write"))],
)
def update_financial_year(
    year_id: int,
    payload: FinancialYearUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return FinancialYearService.update(db=db, year_id=year_id, payload=payload, user_id=current_user.id)


@router.post(
    "/{year_id}/set-current",
    response_model=FinancialYearResponse,
    summary="Set financial year as the current active fiscal year",
    dependencies=[Depends(require_permission("settings:write"))],
)
def set_current_financial_year(
    year_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return FinancialYearService.set_current(db=db, year_id=year_id, user_id=current_user.id)
