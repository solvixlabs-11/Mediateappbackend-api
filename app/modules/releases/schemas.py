"""Pydantic schemas for App Releases / What's New."""

import json
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


class AppReleaseBase(BaseModel):
    version: str = Field(..., min_length=2, max_length=30, description="Semantic version e.g. v2.2.0")
    title: str = Field(..., min_length=3, max_length=200, description="Headline of the release")
    release_date: date = Field(..., description="Release deployment date")
    release_type: str = Field("WEB_UPDATE", description="Release type: WEB_UPDATE, MOBILE_APK, MAJOR_RELEASE, PATCH")
    summary: str = Field(..., min_length=5, max_length=500, description="Summary paragraph")
    highlights: list[str] = Field(default_factory=list, description="List of key feature bullets")
    target_audience: str = Field("ALL", description="Target audience: ALL, ADMIN, MR, MANAGER")
    is_published: bool = Field(True, description="Publish status")
    apk_download_url: str | None = Field(None, max_length=500, description="Optional APK download link")


class AppReleaseCreate(AppReleaseBase):
    pass


class AppReleaseUpdate(BaseModel):
    version: str | None = Field(None, min_length=2, max_length=30)
    title: str | None = Field(None, min_length=3, max_length=200)
    release_date: date | None = None
    release_type: str | None = None
    summary: str | None = Field(None, min_length=5, max_length=500)
    highlights: list[str] | None = None
    target_audience: str | None = None
    is_published: bool | None = None
    apk_download_url: str | None = None


class AppReleaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    version: str
    title: str
    release_date: date
    release_type: str
    summary: str
    highlights: list[str] = Field(default_factory=list)
    target_audience: str
    is_published: bool
    apk_download_url: str | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_model(cls, record) -> "AppReleaseResponse":
        highlights = []
        if record.highlights_json:
            try:
                parsed = json.loads(record.highlights_json)
                if isinstance(parsed, list):
                    highlights = parsed
            except Exception:
                highlights = [record.highlights_json]

        return cls(
            id=record.id,
            version=record.version,
            title=record.title,
            release_date=record.release_date,
            release_type=record.release_type,
            summary=record.summary,
            highlights=highlights,
            target_audience=record.target_audience,
            is_published=record.is_published,
            apk_download_url=record.apk_download_url,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )


class AppReleaseListResponse(BaseModel):
    items: list[AppReleaseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
