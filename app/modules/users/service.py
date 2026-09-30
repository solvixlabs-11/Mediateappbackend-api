"""User management and team hierarchy business service."""

import math

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.scope import ScopeContext, UserRole, get_accessible_user_ids
from app.core.security import hash_password
from app.modules.common.models import AuditLog
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import (
    AssignManagerRequest,
    ManagerMRAssignmentResponse,
    ManagerSummary,
    ProfileUpdateRequest,
    RoleResponse,
    UserCreate,
    UserListResponse,
    UserResponse,
    UserStatusUpdate,
    UserUpdate,
)

logger = get_logger(__name__)


class UserService:
    """Business logic for user administration, team hierarchy, and profile."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = UserRepository(db)
        self.settings = get_settings()

    def get_user_scope_context(self, current_user: User) -> ScopeContext:
        """Build ScopeContext with team member IDs for managers."""
        role_code = current_user.role.code.upper() if current_user.role else "MR"
        try:
            role_enum = UserRole(role_code)
        except ValueError:
            role_enum = UserRole.MR

        team_member_ids: list[int] = []
        if role_enum == UserRole.MANAGER:
            assignments = self.repo.get_active_assignments_for_manager(current_user.id)
            team_member_ids = [a.mr_id for a in assignments]

        return ScopeContext(
            user_id=current_user.id,
            role=role_enum,
            team_member_ids=team_member_ids,
        )

    def list_users(
        self,
        current_user: User,
        role_code: str | None = None,
        search: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> UserListResponse:
        """List users respecting data scoping rules."""
        context = self.get_user_scope_context(current_user)
        accessible_ids = get_accessible_user_ids(context)

        skip = (page - 1) * page_size
        total = self.repo.count_users(
            accessible_user_ids=accessible_ids,
            role_code=role_code,
            search=search,
            is_active=is_active,
        )
        users = self.repo.list_users(
            accessible_user_ids=accessible_ids,
            role_code=role_code,
            search=search,
            is_active=is_active,
            skip=skip,
            limit=page_size,
        )

        items = [self.to_user_response(u) for u in users]
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        return UserListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_user_by_id(self, user_id: int, current_user: User) -> UserResponse:
        """Fetch user by ID with scope validation."""
        context = self.get_user_scope_context(current_user)
        accessible_ids = get_accessible_user_ids(context)

        if accessible_ids is not None and user_id not in accessible_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: User is not within your accessible team scope",
            )

        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )
        return self.to_user_response(user)

    def create_user(self, payload: UserCreate, current_user: User) -> UserResponse:
        """Create new user account (Admin only)."""
        existing = self.repo.get_by_email(payload.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A user with email '{payload.email}' already exists",
            )

        role = self.repo.get_role_by_code(payload.role_code)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role code '{payload.role_code}'. Valid roles: ADMIN, MANAGER, MR",
            )

        # Validate manager if provided
        if payload.manager_id:
            manager = self.repo.get_by_id(payload.manager_id)
            is_valid_mgr = (
                manager is not None
                and manager.is_active
                and manager.role.code in ("MANAGER", "ADMIN")
            )
            if not is_valid_mgr:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Manager ID {payload.manager_id} is invalid or not an active manager",
                )

        hashed_pw = hash_password(payload.password)
        new_user = self.repo.create_user(
            email=payload.email,
            full_name=payload.full_name,
            phone=payload.phone,
            role_id=role.id,
            hashed_password=hashed_pw,
            force_password_change=payload.force_password_change,
            created_by_user_id=current_user.id,
        )
        self.db.flush()

        # If MR and manager specified, create initial assignment
        if role.code == "MR" and payload.manager_id:
            self.repo.create_assignment(
                manager_id=payload.manager_id,
                mr_id=new_user.id,
                assigned_by_user_id=current_user.id,
            )

        # Audit log
        self._log_audit(
            current_user.id,
            "USER_CREATED",
            "users",
            new_user.id,
            {"email": new_user.email, "role": role.code},
        )
        self.db.commit()
        self.db.refresh(new_user)

        return self.to_user_response(new_user)

    def update_user(self, user_id: int, payload: UserUpdate, current_user: User) -> UserResponse:
        """Update existing user record."""
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )

        changes: dict[str, str | None] = {}
        if payload.full_name is not None and payload.full_name.strip() != user.full_name:
            user.full_name = payload.full_name.strip()
            changes["full_name"] = user.full_name

        if payload.phone is not None and payload.phone.strip() != (user.phone or ""):
            user.phone = payload.phone.strip() if payload.phone else None
            changes["phone"] = user.phone

        if payload.role_code is not None:
            new_role = self.repo.get_role_by_code(payload.role_code)
            if not new_role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role code '{payload.role_code}'",
                )
            if new_role.id != user.role_id:
                user.role_id = new_role.id
                changes["role_code"] = new_role.code

        if payload.password is not None and payload.password.strip():
            user.hashed_password = hash_password(payload.password.strip())
            changes["password"] = "CHANGED"

        if payload.profile_picture_file_id is not None:
            user.profile_picture_file_id = payload.profile_picture_file_id
            changes["profile_picture_file_id"] = str(payload.profile_picture_file_id)

        user.updated_by = current_user.id
        self.db.flush()

        if changes:
            self._log_audit(
                current_user.id,
                "USER_UPDATED",
                "users",
                user.id,
                changes,
            )
            self.db.commit()
            self.db.refresh(user)

        return self.to_user_response(user)

    def update_status(
        self,
        user_id: int,
        payload: UserStatusUpdate,
        current_user: User,
    ) -> UserResponse:
        """Activate or deactivate user account with immediate token revocation (BR-14)."""
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )

        if user.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own account",
            )

        user.is_active = payload.is_active
        user.updated_by = current_user.id

        revoked_count = 0
        if not payload.is_active:
            # BR-14: Deactivated users lose access immediately (tokens revoked)
            revoked_count = self.repo.revoke_all_user_tokens(user.id)
            logger.info(
                "Deactivated user %s (id: %s) and revoked %s active refresh tokens",
                user.email,
                user.id,
                revoked_count,
            )

        self._log_audit(
            current_user.id,
            "USER_STATUS_CHANGED",
            "users",
            user.id,
            {
                "is_active": str(payload.is_active),
                "reason": payload.reason or "",
                "revoked_tokens": str(revoked_count),
            },
        )
        self.db.commit()
        self.db.refresh(user)

        return self.to_user_response(user)

    def assign_manager(
        self,
        mr_id: int,
        payload: AssignManagerRequest,
        current_user: User,
    ) -> ManagerMRAssignmentResponse:
        """Assign or reassign an MR to a manager with full history tracking."""
        mr = self.repo.get_by_id(mr_id)
        if not mr or mr.role.code != "MR":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User ID {mr_id} is not an MR",
            )

        manager = self.repo.get_by_id(payload.manager_id)
        if not manager or not manager.is_active or manager.role.code not in ("MANAGER", "ADMIN"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User ID {payload.manager_id} is not an active Manager",
            )

        # Close existing active assignment if any
        self.repo.close_active_assignment(mr_id, updated_by_user_id=current_user.id)

        # Create new assignment
        assignment = self.repo.create_assignment(
            manager_id=manager.id,
            mr_id=mr.id,
            assigned_by_user_id=current_user.id,
        )

        self._log_audit(
            current_user.id,
            "MANAGER_ASSIGNED",
            "manager_mr_assignments",
            assignment.id,
            {"manager_id": str(manager.id), "mr_id": str(mr.id)},
        )
        self.db.commit()
        self.db.refresh(assignment)

        return ManagerMRAssignmentResponse(
            id=assignment.id,
            manager_id=manager.id,
            manager_name=manager.full_name,
            mr_id=mr.id,
            mr_name=mr.full_name,
            assigned_at=assignment.assigned_at,
            unassigned_at=assignment.unassigned_at,
            is_active=assignment.unassigned_at is None,
        )

    def get_assignment_history(self, mr_id: int) -> list[ManagerMRAssignmentResponse]:
        """Get complete manager assignment history for an MR."""
        mr = self.repo.get_by_id(mr_id)
        if not mr:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {mr_id} not found",
            )

        records = self.repo.get_assignment_history(mr_id)
        results: list[ManagerMRAssignmentResponse] = []
        for r in records:
            mgr = self.repo.get_by_id(r.manager_id)
            mgr_name = mgr.full_name if mgr else f"Manager #{r.manager_id}"
            results.append(
                ManagerMRAssignmentResponse(
                    id=r.id,
                    manager_id=r.manager_id,
                    manager_name=mgr_name,
                    mr_id=mr.id,
                    mr_name=mr.full_name,
                    assigned_at=r.assigned_at,
                    unassigned_at=r.unassigned_at,
                    is_active=r.unassigned_at is None,
                )
            )
        return results

    def get_my_team(self, manager_user: User) -> list[UserResponse]:
        """Fetch active team members assigned to manager."""
        assignments = self.repo.get_active_assignments_for_manager(manager_user.id)
        team_mrs: list[UserResponse] = []
        for a in assignments:
            mr = self.repo.get_by_id(a.mr_id)
            if mr and mr.is_active:
                team_mrs.append(self.to_user_response(mr))
        return team_mrs

    def get_managers_list(self) -> list[ManagerSummary]:
        """Get list of active managers for dropdown selection."""
        managers = self.repo.get_users_by_role("MANAGER")
        admins = self.repo.get_users_by_role("ADMIN")
        all_eligible = managers + admins
        return [
            ManagerSummary(
                id=m.id,
                full_name=m.full_name,
                email=m.email,
                phone=m.phone,
            )
            for m in all_eligible
        ]

    def get_all_roles(self) -> list[RoleResponse]:
        """Get all available system roles."""
        roles = self.repo.get_all_roles()
        return [RoleResponse.model_validate(r) for r in roles]

    def update_profile(self, current_user: User, payload: ProfileUpdateRequest) -> UserResponse:
        """Update current logged-in user profile."""
        if payload.full_name is not None and payload.full_name.strip():
            current_user.full_name = payload.full_name.strip()

        if payload.phone is not None:
            current_user.phone = payload.phone.strip() if payload.phone.strip() else None

        if payload.profile_picture_file_id is not None:
            current_user.profile_picture_file_id = payload.profile_picture_file_id

        current_user.updated_by = current_user.id
        self.db.commit()
        self.db.refresh(current_user)
        return self.to_user_response(current_user)

    def to_user_response(self, user: User) -> UserResponse:
        """Convert User model to UserResponse including manager and photo URL."""
        manager_summary: ManagerSummary | None = None
        # If user is MR, lookup active manager
        if user.role and user.role.code == "MR":
            active_assignment = self.repo.get_active_assignment_for_mr(user.id)
            if active_assignment:
                mgr = self.repo.get_by_id(active_assignment.manager_id)
                if mgr:
                    manager_summary = ManagerSummary(
                        id=mgr.id,
                        full_name=mgr.full_name,
                        email=mgr.email,
                        phone=mgr.phone,
                    )

        photo_url: str | None = None
        if user.profile_picture_file_id:
            prefix = self.settings.API_V1_PREFIX
            photo_url = f"{prefix}/files/{user.profile_picture_file_id}/download"

        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            role_id=user.role_id,
            role=RoleResponse.model_validate(user.role),
            is_active=user.is_active,
            force_password_change=user.force_password_change,
            failed_login_attempts=user.failed_login_attempts,
            locked_until=user.locked_until,
            last_login_at=user.last_login_at,
            profile_picture_file_id=user.profile_picture_file_id,
            profile_picture_url=photo_url,
            current_manager=manager_summary,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    def _log_audit(
        self,
        actor_id: int,
        action: str,
        entity_name: str,
        entity_id: int,
        details: dict[str, str | None],
    ) -> None:
        """Create audit log entry."""
        log = AuditLog(
            user_id=actor_id,
            action=action,
            entity_type=entity_name,
            entity_id=str(entity_id),
            details=str(details),
        )
        self.db.add(log)
