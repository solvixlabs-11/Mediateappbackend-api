"""Pydantic validation schemas for Tasks and Task Comments."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class TaskCommentCreate(BaseModel):
    """Payload to post a comment or chat message on a task."""

    message: str = Field(..., min_length=1, max_length=2000)


class TaskCommentResponse(BaseModel):
    """Task comment response item."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    user_id: int
    user_name: str | None = None
    message: str
    created_at: datetime


class TaskCreate(BaseModel):
    """Payload to create a new task."""

    title: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    due_date: date
    priority: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH, URGENT")
    assigned_to_id: int | None = None
    customer_type: str | None = None
    customer_id: int | None = None
    client_uuid: str | None = None


class TaskUpdate(BaseModel):
    """Payload to update an existing task."""

    title: str | None = Field(default=None, max_length=200)
    description: str | None = None
    due_date: date | None = None
    priority: str | None = None
    status: str | None = None  # PENDING, IN_PROGRESS, COMPLETED, CANCELLED
    assigned_to_id: int | None = None


class TaskResponse(BaseModel):
    """Full task record response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None = None
    due_date: date
    priority: str
    status: str
    completed_at: datetime | None = None
    assigned_to_id: int
    assigned_to_name: str | None = None
    created_by_id: int | None = None
    created_by_name: str | None = None
    customer_type: str | None = None
    customer_id: int | None = None
    client_uuid: str | None = None
    comments_count: int = 0
    comments: list[TaskCommentResponse] = []
    created_at: datetime
    updated_at: datetime


class TaskSummaryResponse(BaseModel):
    """Task counts by state for dashboard & tab badges."""

    model_config = ConfigDict(from_attributes=True)

    today_count: int = 0
    upcoming_count: int = 0
    overdue_count: int = 0
    completed_count: int = 0
    total_active: int = 0
