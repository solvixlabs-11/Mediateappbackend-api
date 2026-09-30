"""Authentication and permission FastAPI dependencies."""

from collections.abc import Callable
from datetime import UTC, datetime

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.modules.users.models import User

security_bearer = HTTPBearer(auto_error=True)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Extract and validate current authenticated user from Bearer access token."""
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(user_id_str)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject format",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()  # noqa: E712
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or has been deleted",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated. Contact administrator.",
        )

    if user.locked_until:
        locked_utc = (
            user.locked_until if user.locked_until.tzinfo else user.locked_until.replace(tzinfo=UTC)
        )
        if locked_utc > datetime.now(UTC):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is temporarily locked until {locked_utc.isoformat()}",
            )

    return user


def require_permission(permission_code: str) -> Callable[[User], User]:
    """Dependency factory checking that the current user's role has permission_code."""

    def _dependency(current_user: User = Depends(get_current_user)) -> User:
        # ADMIN role has superuser override on all permissions
        if current_user.role and current_user.role.code == "ADMIN":
            return current_user

        user_permissions = (
            {p.code for p in current_user.role.permissions} if current_user.role else set()
        )
        if permission_code not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: missing required permission '{permission_code}'",
            )
        return current_user

    return _dependency
