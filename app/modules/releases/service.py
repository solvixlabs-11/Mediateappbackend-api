"""App Releases Service layer."""

import json
import math
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.modules.releases.models import AppRelease
from app.modules.releases.schemas import (
    AppReleaseCreate,
    AppReleaseUpdate,
    AppReleaseResponse,
    AppReleaseListResponse,
)


class AppReleaseService:
    @staticmethod
    def list_releases(
        db: Session,
        search: str | None = None,
        release_type: str | None = None,
        is_published: bool | None = None,
        target_audience: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> AppReleaseListResponse:
        stmt = select(AppRelease).where(AppRelease.is_deleted == False)

        if search:
            q = f"%{search.strip()}%"
            stmt = stmt.where(
                (AppRelease.version.ilike(q))
                | (AppRelease.title.ilike(q))
                | (AppRelease.summary.ilike(q))
            )
        if release_type:
            stmt = stmt.where(AppRelease.release_type == release_type)
        if is_published is not None:
            stmt = stmt.where(AppRelease.is_published == is_published)
        if target_audience and target_audience != "ALL":
            stmt = stmt.where(
                (AppRelease.target_audience == target_audience)
                | (AppRelease.target_audience == "ALL")
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(count_stmt) or 0

        stmt = stmt.order_by(AppRelease.release_date.desc(), AppRelease.id.desc()).offset((page - 1) * page_size).limit(page_size)
        rows = db.scalars(stmt).all()

        return AppReleaseListResponse(
            items=[AppReleaseResponse.from_orm_model(r) for r in rows],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total > 0 else 1,
        )

    @staticmethod
    def get_by_id(db: Session, release_id: int) -> AppRelease:
        stmt = select(AppRelease).where(
            AppRelease.id == release_id,
            AppRelease.is_deleted == False,
        )
        row = db.scalar(stmt)
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Release note #{release_id} not found",
            )
        return row

    @staticmethod
    def get_latest(db: Session, target_audience: str | None = None) -> AppReleaseResponse | None:
        stmt = select(AppRelease).where(
            AppRelease.is_published == True,
            AppRelease.is_deleted == False,
        )
        if target_audience and target_audience != "ALL":
            stmt = stmt.where(
                (AppRelease.target_audience == target_audience)
                | (AppRelease.target_audience == "ALL")
            )
        stmt = stmt.order_by(AppRelease.release_date.desc(), AppRelease.id.desc()).limit(1)
        row = db.scalar(stmt)
        if not row:
            return None
        return AppReleaseResponse.from_orm_model(row)

    @staticmethod
    def create(db: Session, payload: AppReleaseCreate, user_id: int | None = None) -> AppReleaseResponse:
        highlights_json = json.dumps(payload.highlights) if payload.highlights else None

        record = AppRelease(
            version=payload.version.strip(),
            title=payload.title.strip(),
            release_date=payload.release_date,
            release_type=payload.release_type,
            summary=payload.summary.strip(),
            highlights_json=highlights_json,
            target_audience=payload.target_audience,
            is_published=payload.is_published,
            apk_download_url=payload.apk_download_url.strip() if payload.apk_download_url else None,
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return AppReleaseResponse.from_orm_model(record)

    @staticmethod
    def update(
        db: Session,
        release_id: int,
        payload: AppReleaseUpdate,
        user_id: int | None = None,
    ) -> AppReleaseResponse:
        record = AppReleaseService.get_by_id(db, release_id)

        if payload.version is not None:
            record.version = payload.version.strip()
        if payload.title is not None:
            record.title = payload.title.strip()
        if payload.release_date is not None:
            record.release_date = payload.release_date
        if payload.release_type is not None:
            record.release_type = payload.release_type
        if payload.summary is not None:
            record.summary = payload.summary.strip()
        if payload.highlights is not None:
            record.highlights_json = json.dumps(payload.highlights)
        if payload.target_audience is not None:
            record.target_audience = payload.target_audience
        if payload.is_published is not None:
            record.is_published = payload.is_published
        if payload.apk_download_url is not None:
            record.apk_download_url = payload.apk_download_url.strip() if payload.apk_download_url else None

        record.updated_by = user_id
        db.commit()
        db.refresh(record)
        return AppReleaseResponse.from_orm_model(record)
