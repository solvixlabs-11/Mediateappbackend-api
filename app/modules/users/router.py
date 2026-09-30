"""Users and Team HTTP endpoints."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_permission
from app.db.session import get_db
from app.modules.users.models import User
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
from app.modules.users.service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/roles",
    response_model=list[RoleResponse],
    summary="Get all system roles",
)
def get_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RoleResponse]:
    """List available system roles."""
    service = UserService(db)
    return service.get_all_roles()


@router.get(
    "/managers",
    response_model=list[ManagerSummary],
    summary="List active managers for assignment",
)
def list_managers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ManagerSummary]:
    """List eligible managers and administrators for MR assignment."""
    service = UserService(db)
    return service.get_managers_list()


@router.get(
    "/my-team",
    response_model=list[UserResponse],
    summary="Get manager's active team members",
)
def get_my_team(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users:read")),
) -> list[UserResponse]:
    """List active MRs assigned to current logged-in manager."""
    service = UserService(db)
    return service.get_my_team(current_user)


@router.get(
    "/me/profile",
    response_model=UserResponse,
    summary="Get current user profile with manager info",
)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Get full profile details for logged-in user including manager and avatar."""
    service = UserService(db)
    return service.to_user_response(current_user)


@router.put(
    "/me/profile",
    response_model=UserResponse,
    summary="Update current user profile",
)
def update_my_profile(
    payload: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Self-service profile update (name, phone, avatar)."""
    service = UserService(db)
    return service.update_profile(current_user, payload)


@router.get(
    "",
    response_model=UserListResponse,
    summary="List users with data scoping and filters",
)
def list_users(
    role: str | None = Query(default=None, description="Filter by role code (ADMIN, MANAGER, MR)"),
    search: str | None = Query(default=None, description="Search by name, email, or phone"),
    is_active: bool | None = Query(default=None, description="Filter active/inactive"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users:read")),
) -> UserListResponse:
    """Fetch paginated, role-scoped list of user accounts."""
    service = UserService(db)
    return service.list_users(
        current_user=current_user,
        role_code=role,
        search=search,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user account (Admin only)",
)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users:write")),
) -> UserResponse:
    """Create a new user account with role and optional manager assignment."""
    service = UserService(db)
    return service.create_user(payload, current_user)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user details by ID",
)
def get_user_details(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users:read")),
) -> UserResponse:
    """Get user details by ID respecting team scope."""
    service = UserService(db)
    return service.get_user_by_id(user_id, current_user)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user account",
)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users:write")),
) -> UserResponse:
    """Update user account attributes."""
    service = UserService(db)
    return service.update_user(user_id, payload, current_user)


@router.patch(
    "/{user_id}/status",
    response_model=UserResponse,
    summary="Activate or deactivate user account (BR-14)",
)
def update_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users:write")),
) -> UserResponse:
    """Activate or deactivate user. Deactivating revokes all active tokens immediately."""
    service = UserService(db)
    return service.update_status(user_id, payload, current_user)


@router.post(
    "/{user_id}/assign-manager",
    response_model=ManagerMRAssignmentResponse,
    summary="Assign MR to a Manager with history",
)
def assign_manager(
    user_id: int,
    payload: AssignManagerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users:manage_roles")),
) -> ManagerMRAssignmentResponse:
    """Assign an MR to a manager. Replaces active assignment while preserving history."""
    service = UserService(db)
    return service.assign_manager(user_id, payload, current_user)


@router.get(
    "/{user_id}/assignments",
    response_model=list[ManagerMRAssignmentResponse],
    summary="Get manager assignment history for MR",
)
def get_assignment_history(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users:read")),
) -> list[ManagerMRAssignmentResponse]:
    """Retrieve full manager assignment audit history for an MR."""
    service = UserService(db)
    return service.get_assignment_history(user_id)
