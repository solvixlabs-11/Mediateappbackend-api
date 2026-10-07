"""Target database repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.targets.models import Target
from app.modules.users.models import User


class TargetRepository:
    """SQLAlchemy queries for Target records."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_user_and_period(self, user_id: int, year: int, month: int) -> Target | None:
        stmt = select(Target).where(
            Target.user_id == user_id,
            Target.year == year,
            Target.month == month,
            Target.is_deleted.is_(False),
        )
        return self.db.scalars(stmt).first()

    def list_targets(
        self,
        year: int,
        month: int,
        user_ids: list[int] | None = None,
    ) -> list[tuple[Target, str]]:
        """Return list of (Target, user_name) for specified year and month."""
        stmt = (
            select(Target, User.full_name)
            .join(User, Target.user_id == User.id)
            .where(
                Target.year == year,
                Target.month == month,
                Target.is_deleted.is_(False),
            )
        )
        if user_ids is not None:
            stmt = stmt.where(Target.user_id.in_(user_ids))

        return list(self.db.execute(stmt).all())

    def upsert_target(
        self,
        user_id: int,
        year: int,
        month: int,
        visit_target: int,
        doctor_call_target: int = 0,
        chemist_call_target: int = 0,
        primary_sales_target: float = 0.0,
        secondary_sales_target: float = 0.0,
        creator_id: int | None = None,
    ) -> Target:
        target = self.get_by_user_and_period(user_id, year, month)
        if target:
            target.visit_target = visit_target
            target.doctor_call_target = doctor_call_target
            target.chemist_call_target = chemist_call_target
            target.primary_sales_target = primary_sales_target
            target.secondary_sales_target = secondary_sales_target
            target.updated_by = creator_id
        else:
            target = Target(
                user_id=user_id,
                year=year,
                month=month,
                visit_target=visit_target,
                doctor_call_target=doctor_call_target,
                chemist_call_target=chemist_call_target,
                primary_sales_target=primary_sales_target,
                secondary_sales_target=secondary_sales_target,
                created_by=creator_id,
                updated_by=creator_id,
            )
            self.db.add(target)

        self.db.commit()
        self.db.refresh(target)
        return target
