"""Tasks REST API endpoints."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.tasks.schemas import (
    TaskCommentCreate,
    TaskCommentResponse,
    TaskCreate,
    TaskResponse,
    TaskSummaryResponse,
    TaskUpdate,
)
from app.modules.tasks.service import TaskService
from app.modules.users.models import User
from app.modules.users.service import UserService

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get(
    "/summary",
    response_model=TaskSummaryResponse,
    summary="Get task counters for badges and cards",
)
def get_task_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskSummaryResponse:
    """Return task summary counts."""
    scope = UserService(db).get_user_scope_context(current_user)
    service = TaskService(db)
    return service.get_summary(scope)


@router.get(
    "",
    response_model=list[TaskResponse],
    summary="List tasks with filters and scoping",
)
def list_tasks(
    status: str | None = Query(None, description="PENDING, IN_PROGRESS, COMPLETED, CANCELLED"),
    priority: str | None = Query(None, description="LOW, MEDIUM, HIGH, URGENT"),
    due_date: date | None = Query(None, description="Exact due date filter"),
    overdue_only: bool = Query(False, description="Filter for overdue tasks"),
    today_only: bool = Query(False, description="Filter for tasks due today"),
    upcoming_only: bool = Query(False, description="Filter for tasks due in the future"),
    search: str | None = Query(None, description="Keyword search in title and description"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TaskResponse]:
    """List operational tasks."""
    scope = UserService(db).get_user_scope_context(current_user)
    service = TaskService(db)
    return service.list_tasks(
        context=scope,
        status_filter=status,
        priority=priority,
        due_date=due_date,
        overdue_only=overdue_only,
        today_only=today_only,
        upcoming_only=upcoming_only,
        search=search,
        skip=skip,
        limit=limit,
    )


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    """Create task."""
    scope = UserService(db).get_user_scope_context(current_user)
    service = TaskService(db)
    return service.create_task(scope, payload)


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get task details and comments",
)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    """Get single task."""
    scope = UserService(db).get_user_scope_context(current_user)
    service = TaskService(db)
    return service.get_task(scope, task_id)


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update task details",
)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    """Update task."""
    scope = UserService(db).get_user_scope_context(current_user)
    service = TaskService(db)
    return service.update_task(scope, task_id, payload)


@router.post(
    "/{task_id}/complete",
    response_model=TaskResponse,
    summary="Toggle task completion status",
)
def toggle_complete(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    """Toggle completed state."""
    scope = UserService(db).get_user_scope_context(current_user)
    service = TaskService(db)
    return service.complete_task(scope, task_id)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete task",
)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete task."""
    scope = UserService(db).get_user_scope_context(current_user)
    service = TaskService(db)
    service.delete_task(scope, task_id)


@router.post(
    "/{task_id}/comments",
    response_model=TaskCommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Post comment or chat reply to task",
)
def add_task_comment(
    task_id: int,
    payload: TaskCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskCommentResponse:
    """Add a comment/message to a task."""
    scope = UserService(db).get_user_scope_context(current_user)
    service = TaskService(db)
    return service.add_comment(scope, task_id, payload)
