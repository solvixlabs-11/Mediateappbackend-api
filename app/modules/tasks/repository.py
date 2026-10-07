"""Database repository for Tasks and Task Comments."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload, selectinload

from app.modules.tasks.models import Task, TaskComment


class TaskRepository:
    """Repository handling CRUD, scoping, and comment threads for tasks."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_tasks(
        self,
        accessible_user_ids: list[int] | None = None,
        status: str | None = None,
        priority: str | None = None,
        due_date: date | None = None,
        overdue_only: bool = False,
        today_only: bool = False,
        upcoming_only: bool = False,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Task]:
        """Fetch tasks respecting user hierarchy and filters."""
        query = self.db.query(Task).options(
            joinedload(Task.assigned_to),
            joinedload(Task.created_by),
            selectinload(Task.comments).joinedload(TaskComment.user),
        )

        if accessible_user_ids is not None:
            query = query.filter(
                or_(
                    Task.assigned_to_id.in_(accessible_user_ids),
                    Task.created_by_id.in_(accessible_user_ids),
                )
            )

        now_date = date.today()

        if overdue_only:
            query = query.filter(Task.due_date < now_date, Task.status != "COMPLETED")
        elif today_only:
            query = query.filter(Task.due_date == now_date)
        elif upcoming_only:
            query = query.filter(Task.due_date > now_date, Task.status != "COMPLETED")

        if status:
            query = query.filter(Task.status == status.upper())
        if priority:
            query = query.filter(Task.priority == priority.upper())
        if due_date:
            query = query.filter(Task.due_date == due_date)

        if search:
            pat = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Task.title.ilike(pat),
                    Task.description.ilike(pat),
                )
            )

        return (
            query.order_by(Task.due_date.asc(), Task.priority.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_id(self, task_id: int) -> Task | None:
        """Fetch single task by ID with assigned user and comments."""
        return (
            self.db.query(Task)
            .options(
                joinedload(Task.assigned_to),
                joinedload(Task.created_by),
                selectinload(Task.comments).joinedload(TaskComment.user),
            )
            .filter(Task.id == task_id)
            .first()
        )

    def get_by_client_uuid(self, client_uuid: str) -> Task | None:
        """Fetch task by mobile client UUID for idempotent creation."""
        return self.db.query(Task).filter(Task.client_uuid == client_uuid).first()

    def create(
        self,
        title: str,
        due_date: date,
        assigned_to_id: int,
        created_by_id: int | None = None,
        description: str | None = None,
        priority: str = "MEDIUM",
        customer_type: str | None = None,
        customer_id: int | None = None,
        client_uuid: str | None = None,
    ) -> Task:
        """Create new Task entity."""
        task = Task(
            title=title.strip(),
            due_date=due_date,
            assigned_to_id=assigned_to_id,
            created_by_id=created_by_id,
            description=description.strip() if description else None,
            priority=priority.upper(),
            status="PENDING",
            customer_type=customer_type.upper() if customer_type else None,
            customer_id=customer_id,
            client_uuid=client_uuid,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(task)
        self.db.flush()
        return task

    def add_comment(self, task_id: int, user_id: int, message: str) -> TaskComment:
        """Add a comment/chat entry to a task."""
        comment = TaskComment(
            task_id=task_id,
            user_id=user_id,
            message=message.strip(),
            created_at=datetime.utcnow(),
        )
        self.db.add(comment)
        self.db.flush()
        return comment

    def list_comments(self, task_id: int) -> list[TaskComment]:
        """Fetch comments for a task ordered chronologically."""
        return (
            self.db.query(TaskComment)
            .options(joinedload(TaskComment.user))
            .filter(TaskComment.task_id == task_id)
            .order_by(TaskComment.created_at.asc())
            .all()
        )

    def get_summary(self, accessible_user_ids: list[int] | None = None) -> dict[str, int]:
        """Get counts for badges and dashboard."""
        now_date = date.today()
        base_query = self.db.query(Task)
        if accessible_user_ids is not None:
            base_query = base_query.filter(
                or_(
                    Task.assigned_to_id.in_(accessible_user_ids),
                    Task.created_by_id.in_(accessible_user_ids),
                )
            )

        today_count = base_query.filter(
            Task.due_date == now_date, Task.status != "COMPLETED"
        ).count()
        upcoming_count = base_query.filter(
            Task.due_date > now_date, Task.status != "COMPLETED"
        ).count()
        overdue_count = base_query.filter(
            Task.due_date < now_date, Task.status != "COMPLETED"
        ).count()
        completed_count = base_query.filter(Task.status == "COMPLETED").count()

        return {
            "today_count": today_count,
            "upcoming_count": upcoming_count,
            "overdue_count": overdue_count,
            "completed_count": completed_count,
            "total_active": today_count + upcoming_count + overdue_count,
        }

    def delete(self, task: Task) -> None:
        """Delete task entity."""
        self.db.delete(task)
        self.db.flush()
