"""Authentication endpoints and session management router."""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.modules.auth.schemas import (
    AuthConfigResponse,
    ChangePasswordRequest,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserSummary,
)
from app.modules.auth.service import AuthService
from app.modules.users.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _get_client_ip(request: Request) -> str | None:
    """Extract client IP from request headers or client socket."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def _get_user_agent(request: Request) -> str | None:
    """Extract User-Agent string from request headers."""
    return request.headers.get("user-agent")


@router.get(
    "/config",
    response_model=AuthConfigResponse,
    summary="Get authentication metadata and configuration",
    description=(
        "Returns dynamic system metadata, active roles, and dev demo accounts if in dev mode."
    ),
)
def get_auth_config(
    db: Session = Depends(get_db),
) -> AuthConfigResponse:
    service = AuthService(db)
    return service.get_auth_config()


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login with email and password",
    description=(
        "Authenticates credentials, issues a short-lived JWT access token "
        "and rotating refresh token."
    ),
)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    service = AuthService(db)
    return service.login(
        request=payload,
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotate refresh token for new access/refresh pair",
    description=(
        "Rotates the refresh token. If an already revoked token is submitted, "
        "invalidates the whole session family."
    ),
)
def refresh(
    payload: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    service = AuthService(db)
    return service.refresh(
        refresh_token_raw=payload.refresh_token,
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout current session",
    description="Revokes the specified refresh token and closes the session.",
)
def logout(
    request: Request,
    payload: LogoutRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    service = AuthService(db)
    raw_token = payload.refresh_token if payload else None
    service.logout(
        user=current_user,
        refresh_token_raw=raw_token,
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
    )
    return MessageResponse(message="Successfully logged out")


@router.post(
    "/logout-all",
    response_model=MessageResponse,
    summary="Logout from all devices",
    description="Revokes all active refresh tokens for the authenticated user.",
)
def logout_all(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    service = AuthService(db)
    count = service.logout_all(
        user=current_user,
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
    )
    return MessageResponse(message=f"Logged out from all devices ({count} session(s) revoked)")


@router.get(
    "/me",
    response_model=UserSummary,
    summary="Get current user profile and permissions",
    description="Returns authenticated user details along with permitted actions.",
)
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserSummary:
    service = AuthService(db)
    return service.get_me(current_user)


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change user password",
    description=(
        "Validates current password, applies new password, and revokes all active sessions."
    ),
)
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    service = AuthService(db)
    service.change_password(
        user=current_user,
        request=payload,
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
    )
    return MessageResponse(
        message="Password changed successfully. Please log in again with your new password."
    )


@router.post(
    "/register",
    response_model=UserSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description="Creates a new account with specified role.",
)
def register(
    payload: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> UserSummary:
    service = AuthService(db)
    return service.register(
        request=payload,
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
    )
