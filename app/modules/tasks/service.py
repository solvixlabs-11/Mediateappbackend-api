"""Task service implementing business logic, permission scoping, and status transitions."""

from __future__ import annotations

from datetime import date, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.scope import ScopeContext, get_accessible_user_ids
from app.modules.tasks.models import Task, TaskComment
from app.modules.tasks.repository import TaskRepository
from app.modules.tasks.schemas import (
    TaskCommentCreate,
    TaskCommentResponse,
    TaskCreate,
    TaskResponse,
    TaskSummaryResponse,
    TaskUpdate,
)


class TaskService:
    """Service layer for tasks and in-task collaboration."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = TaskRepository(db)

    def _to_comment_response(self, comment: TaskComment) -> TaskCommentResponse:
        user_name = None
        if comment.user:
            user_name = comment.user.full_name or comment.user.email
        return TaskCommentResponse(
            id=comment.id,
            task_id=comment.task_id,
            user_id=comment.user_id,
            user_name=user_name,
            message=comment.message,
            created_at=comment.created_at,
        )

    def _to_task_response(self, task: Task) -> TaskResponse:
        assigned_name = None
        if task.assigned_to:
            assigned_name = task.assigned_to.full_name or task.assigned_to.email

        created_name = None
        if task.created_by:
            created_name = task.created_by.full_name or task.created_by.email

        comments_resp = [self._to_comment_response(c) for c in (task.comments or [])]

        return TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            due_date=task.due_date,
            priority=task.priority,
            status=task.status,
            completed_at=task.completed_at,
            assigned_to_id=task.assigned_to_id,
            assigned_to_name=assigned_name,
            created_by_id=task.created_by_id,
            created_by_name=created_name,
            customer_type=task.customer_type,
            customer_id=task.customer_id,
            client_uuid=task.client_uuid,
            comments_count=len(comments_resp),
            comments=comments_resp,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    def list_tasks(
        self,
        context: ScopeContext,
        status_filter: str | None = None,
        priority: str | None = None,
        due_date: date | None = None,
        overdue_only: bool = False,
        today_only: bool = False,
        upcoming_only: bool = False,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[TaskResponse]:
        """List tasks accessible by the active user."""
        accessible_ids = get_accessible_user_ids(context)
        tasks = self.repo.list_tasks(
            accessible_user_ids=list(accessible_ids) if accessible_ids is not None else None,
            status=status_filter,
            priority=priority,
            due_date=due_date,
            overdue_only=overdue_only,
            today_only=today_only,
            upcoming_only=upcoming_only,
            search=search,
            skip=skip,
            limit=limit,
        )
        return [self._to_task_response(t) for t in tasks]

    def _can_access_task(self, context: ScopeContext, task: Task) -> bool:
        """Check if user has access to task by assignment, creation, or team scope."""
        if task.assigned_to_id == context.user_id or task.created_by_id == context.user_id:
            return True
        accessible_ids = get_accessible_user_ids(context)
        if accessible_ids is None:
            return True
        return task.assigned_to_id in accessible_ids or (
            task.created_by_id in accessible_ids if task.created_by_id else False
        )

    def get_task(self, context: ScopeContext, task_id: int) -> TaskResponse:
        """Get a single task by ID with accessibility check."""
        task = self.repo.get_by_id(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found.",
            )

        if not self._can_access_task(context, task):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this task.",
            )

        return self._to_task_response(task)

    def create_task(self, context: ScopeContext, payload: TaskCreate) -> TaskResponse:
        """Create a new task, assigning to self or subordinate."""
        if payload.client_uuid:
            existing = self.repo.get_by_client_uuid(payload.client_uuid)
            if existing:
                return self._to_task_response(existing)

        # Default assignment to current user if not specified
        assigned_to_id = payload.assigned_to_id or context.user_id

        # Hierarchy validation
        accessible_ids = get_accessible_user_ids(context)
        if accessible_ids is not None and assigned_to_id not in accessible_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot assign task to a user outside your scope.",
            )

        task = self.repo.create(
            title=payload.title,
            due_date=payload.due_date,
            assigned_to_id=assigned_to_id,
            created_by_id=context.user_id,
            description=payload.description,
            priority=payload.priority,
            customer_type=payload.customer_type,
            customer_id=payload.customer_id,
            client_uuid=payload.client_uuid,
        )
        self.db.commit()
        reloaded = self.repo.get_by_id(task.id)
        return self._to_task_response(reloaded or task)

    def update_task(self, context: ScopeContext, task_id: int, payload: TaskUpdate) -> TaskResponse:
        """Update task details."""
        task = self.repo.get_by_id(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found.",
            )

        if not self._can_access_task(context, task):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update this task.",
            )

        if payload.title is not None:
            task.title = payload.title.strip()
        if payload.description is not None:
            task.description = payload.description.strip()
        if payload.due_date is not None:
            task.due_date = payload.due_date
        if payload.priority is not None:
            task.priority = payload.priority.upper()
        if payload.status is not None:
            task.status = payload.status.upper()
            if task.status == "COMPLETED" and not task.completed_at:
                task.completed_at = datetime.utcnow()
            elif task.status != "COMPLETED":
                task.completed_at = None
        if payload.assigned_to_id is not None:
            accessible_ids = get_accessible_user_ids(context)
            if accessible_ids is not None and payload.assigned_to_id not in accessible_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot reassign task to a user outside your scope.",
                )
            task.assigned_to_id = payload.assigned_to_id

        task.updated_at = datetime.utcnow()
        self.db.commit()
        task = self.repo.get_by_id(task.id)
        return self._to_task_response(task)  # type: ignore

    def complete_task(self, context: ScopeContext, task_id: int) -> TaskResponse:
        """Toggle or mark task completed."""
        task = self.repo.get_by_id(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found.",
            )

        if not self._can_access_task(context, task):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to modify this task.",
            )

        if task.status == "COMPLETED":
            task.status = "PENDING"
            task.completed_at = None
        else:
            task.status = "COMPLETED"
            task.completed_at = datetime.utcnow()

        task.updated_at = datetime.utcnow()
        self.db.commit()
        task = self.repo.get_by_id(task.id)
        return self._to_task_response(task)  # type: ignore

    def delete_task(self, context: ScopeContext, task_id: int) -> None:
        """Delete task."""
        task = self.repo.get_by_id(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found.",
            )

        if not self._can_access_task(context, task):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this task.",
            )

        self.repo.delete(task)
        self.db.commit()

    def add_comment(
        self, context: ScopeContext, task_id: int, payload: TaskCommentCreate
    ) -> TaskCommentResponse:
        """Post a comment or discussion thread message to a task."""
        task = self.repo.get_by_id(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found.",
            )

        if not self._can_access_task(context, task):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to comment on this task.",
            )

        comment = self.repo.add_comment(
            task_id=task.id,
            user_id=context.user_id,
            message=payload.message,
        )
        self.db.commit()
        # Load user
        self.db.refresh(comment)
        return self._to_comment_response(comment)

    def get_summary(self, context: ScopeContext) -> TaskSummaryResponse:
        """Get summary badge counts."""
        accessible_ids = get_accessible_user_ids(context)
        data = self.repo.get_summary(
            accessible_user_ids=list(accessible_ids) if accessible_ids is not None else None
        )
        return TaskSummaryResponse(**data)
