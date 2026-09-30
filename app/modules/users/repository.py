"""User database repository."""

from collections.abc import Sequence

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.db.mixins import utc_now
from app.modules.auth.models import RefreshToken
from app.modules.users.models import ManagerMRAssignment, Role, User


class UserRepository:
    """Database repository for User, Role, and Manager assignments."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        """Fetch user by primary key ID."""
        return (
            self.db.query(User)
            .options(joinedload(User.role))
            .filter(User.id == user_id, User.is_deleted == False)  # noqa: E712
            .first()
        )

    def get_by_email(self, email: str) -> User | None:
        """Fetch user by unique email."""
        return (
            self.db.query(User)
            .options(joinedload(User.role))
            .filter(User.email == email.strip().lower(), User.is_deleted == False)  # noqa: E712
            .first()
        )

    def get_role_by_code(self, code: str) -> Role | None:
        """Fetch role by code (e.g. 'ADMIN', 'MANAGER', 'MR')."""
        return (
            self.db.query(Role)
            .filter(Role.code == code.upper(), Role.is_deleted == False)  # noqa: E712
            .first()
        )

    def get_all_roles(self) -> list[Role]:
        """Fetch all active system roles."""
        return (
            self.db.query(Role)
            .filter(Role.is_deleted == False)  # noqa: E712
            .order_by(Role.id.asc())
            .all()
        )

    def list_users(
        self,
        accessible_user_ids: Sequence[int] | None = None,
        role_code: str | None = None,
        search: str | None = None,
        is_active: bool | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[User]:
        """Fetch filtered and paginated user list."""
        query = (
            self.db.query(User)
            .join(User.role)
            .options(joinedload(User.role))
            .filter(User.is_deleted == False)  # noqa: E712
        )

        if accessible_user_ids is not None:
            query = query.filter(User.id.in_(accessible_user_ids))

        if role_code:
            query = query.filter(Role.code == role_code.upper())

        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    User.full_name.ilike(pattern),
                    User.email.ilike(pattern),
                    User.phone.ilike(pattern),
                )
            )

        return query.order_by(User.id.desc()).offset(skip).limit(limit).all()

    def count_users(
        self,
        accessible_user_ids: Sequence[int] | None = None,
        role_code: str | None = None,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> int:
        """Count total matching users for pagination."""
        query = (
            self.db.query(User)
            .join(User.role)
            .filter(User.is_deleted == False)  # noqa: E712
        )

        if accessible_user_ids is not None:
            query = query.filter(User.id.in_(accessible_user_ids))

        if role_code:
            query = query.filter(Role.code == role_code.upper())

        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        if search:
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    User.full_name.ilike(pattern),
                    User.email.ilike(pattern),
                    User.phone.ilike(pattern),
                )
            )

        return query.count()

    def create_user(
        self,
        email: str,
        full_name: str,
        phone: str | None,
        role_id: int,
        hashed_password: str,
        force_password_change: bool = False,
        created_by_user_id: int | None = None,
    ) -> User:
        """Insert new user account."""
        user = User(
            email=email.strip().lower(),
            full_name=full_name.strip(),
            phone=phone.strip() if phone else None,
            role_id=role_id,
            hashed_password=hashed_password,
            is_active=True,
            force_password_change=force_password_change,
            created_by=created_by_user_id,
        )
        self.db.add(user)
        self.db.flush()
        return user

    def get_users_by_role(self, role_code: str) -> list[User]:
        """Get all active users belonging to a specific role code."""
        return (
            self.db.query(User)
            .join(User.role)
            .options(joinedload(User.role))
            .filter(
                Role.code == role_code.upper(),
                User.is_active == True,  # noqa: E712
                User.is_deleted == False,  # noqa: E712
            )
            .order_by(User.full_name.asc())
            .all()
        )

    # Manager Assignment Queries
    def get_active_assignment_for_mr(self, mr_id: int) -> ManagerMRAssignment | None:
        """Find active manager assignment for an MR."""
        return (
            self.db.query(ManagerMRAssignment)
            .filter(
                ManagerMRAssignment.mr_id == mr_id,
                ManagerMRAssignment.unassigned_at.is_(None),
                ManagerMRAssignment.is_deleted == False,  # noqa: E712
            )
            .first()
        )

    def get_active_assignments_for_manager(self, manager_id: int) -> list[ManagerMRAssignment]:
        """Find all active MR assignments under a manager."""
        return (
            self.db.query(ManagerMRAssignment)
            .filter(
                ManagerMRAssignment.manager_id == manager_id,
                ManagerMRAssignment.unassigned_at.is_(None),
                ManagerMRAssignment.is_deleted == False,  # noqa: E712
            )
            .all()
        )

    def close_active_assignment(self, mr_id: int, updated_by_user_id: int | None = None) -> None:
        """Close current active assignment for an MR."""
        current = self.get_active_assignment_for_mr(mr_id)
        if current:
            current.unassigned_at = utc_now()
            current.updated_by = updated_by_user_id
            self.db.flush()

    def create_assignment(
        self,
        manager_id: int,
        mr_id: int,
        assigned_by_user_id: int | None = None,
    ) -> ManagerMRAssignment:
        """Record new active manager-to-MR assignment."""
        assignment = ManagerMRAssignment(
            manager_id=manager_id,
            mr_id=mr_id,
            assigned_at=utc_now(),
            unassigned_at=None,
            created_by=assigned_by_user_id,
        )
        self.db.add(assignment)
        self.db.flush()
        return assignment

    def get_assignment_history(self, mr_id: int) -> list[ManagerMRAssignment]:
        """Get chronological manager assignment history for an MR."""
        return (
            self.db.query(ManagerMRAssignment)
            .filter(
                ManagerMRAssignment.mr_id == mr_id,
                ManagerMRAssignment.is_deleted == False,  # noqa: E712
            )
            .order_by(ManagerMRAssignment.assigned_at.desc())
            .all()
        )

    def revoke_all_user_tokens(self, user_id: int) -> int:
        """Revoke all active refresh tokens for user (BR-14 compliance)."""
        now = utc_now()
        tokens = (
            self.db.query(RefreshToken)
            .filter(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False,  # noqa: E712
            )
            .all()
        )
        for token in tokens:
            token.is_revoked = True
            token.updated_at = now
        self.db.flush()
        return len(tokens)
