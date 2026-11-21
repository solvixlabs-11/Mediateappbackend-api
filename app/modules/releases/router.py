"""App Releases & What's New API Router."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db, require_permission
from app.modules.users.models import User
from app.modules.releases.service import AppReleaseService
from app.modules.releases.schemas import (
    AppReleaseCreate,
    AppReleaseUpdate,
    AppReleaseResponse,
    AppReleaseListResponse,
)

router = APIRouter(prefix="/releases", tags=["App Releases & What's New"])


@router.get(
    "",
    response_model=AppReleaseListResponse,
    summary="List product releases & what's new entries",
    dependencies=[Depends(get_current_user)],
)
def list_releases(
    search: str | None = Query(None, description="Search by title, version, summary"),
    release_type: str | None = Query(None, description="Filter by release type"),
    is_published: bool | None = Query(None, description="Filter publication status"),
    target_audience: str | None = Query(None, description="Filter audience"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return AppReleaseService.list_releases(
        db=db,
        search=search,
        release_type=release_type,
        is_published=is_published,
        target_audience=target_audience,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/latest",
    response_model=AppReleaseResponse | None,
    summary="Get latest published release note",
    dependencies=[Depends(get_current_user)],
)
def get_latest_release(
    target_audience: str | None = Query(None),
    db: Session = Depends(get_db),
):
    return AppReleaseService.get_latest(db=db, target_audience=target_audience)


@router.get(
    "/{release_id}",
    response_model=AppReleaseResponse,
    summary="Get single release details",
    dependencies=[Depends(get_current_user)],
)
def get_release_by_id(
    release_id: int,
    db: Session = Depends(get_db),
):
    record = AppReleaseService.get_by_id(db, release_id)
    return AppReleaseResponse.from_orm_model(record)


@router.post(
    "",
    response_model=AppReleaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create release note",
    dependencies=[Depends(require_permission("settings:write"))],
)
def create_release(
    payload: AppReleaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return AppReleaseService.create(db=db, payload=payload, user_id=current_user.id)


@router.put(
    "/{release_id}",
    response_model=AppReleaseResponse,
    summary="Update release note",
    dependencies=[Depends(require_permission("settings:write"))],
)
def update_release(
    release_id: int,
    payload: AppReleaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return AppReleaseService.update(db=db, release_id=release_id, payload=payload, user_id=current_user.id)
