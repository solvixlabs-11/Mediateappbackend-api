"""Authentication and session database repository."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.modules.auth.models import RefreshToken
from app.modules.common.models import AuditLog
from app.modules.users.models import Role, User


class AuthRepository:
    """Encapsulates all database operations for authentication and user sessions."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_user_by_email(self, email: str) -> User | None:
        """Find active/non-deleted user by case-insensitive email."""
        return (
            self.db.query(User)
            .filter(
                User.email.ilike(email.strip()),
                User.is_deleted == False,  # noqa: E712
            )
            .first()
        )

    def get_user_by_id(self, user_id: int) -> User | None:
        """Find active/non-deleted user by primary ID."""
        return (
            self.db.query(User)
            .filter(
                User.id == user_id,
                User.is_deleted == False,  # noqa: E712
            )
            .first()
        )

    def get_role_by_code(self, code: str) -> Role | None:
        """Find role by its code."""
        return self.db.query(Role).filter(Role.code == code).first()

    def get_active_roles(self) -> list[Role]:
        """Fetch all active, non-deleted system roles."""
        return (
            self.db.query(Role)
            .filter(Role.is_active == True, Role.is_deleted == False)  # noqa: E712
            .order_by(Role.id)
            .all()
        )

    def create_user(self, user: User) -> User:
        """Persist a new user entity."""
        self.db.add(user)
        self.db.flush()
        return user

    def update_user_login_success(self, user: User) -> None:
        """Reset failed attempts and record last login timestamp."""
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.now(UTC)
        self.db.flush()

    def update_user_failed_attempt(
        self,
        user: User,
        attempts: int,
        locked_until: datetime | None = None,
    ) -> None:
        """Increment failed counter and conditionally lock account."""
        user.failed_login_attempts = attempts
        user.locked_until = locked_until
        self.db.flush()

    def save_refresh_token(
        self,
        user_id: int,
        token_hash: str,
        family_id: str,
        expires_at: datetime,
    ) -> RefreshToken:
        """Store newly generated hashed refresh token with family tracking."""
        token_entry = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            family_id=family_id,
            is_revoked=False,
            expires_at=expires_at,
        )
        self.db.add(token_entry)
        self.db.flush()
        return token_entry

    def get_refresh_token_by_hash(self, token_hash: str) -> RefreshToken | None:
        """Look up refresh token record by its sha256 hash."""
        return (
            self.db.query(RefreshToken)
            .filter(
                RefreshToken.token_hash == token_hash,
                RefreshToken.is_deleted == False,  # noqa: E712
            )
            .first()
        )

    def revoke_refresh_token(
        self,
        token: RefreshToken,
        replaced_by_id: int | None = None,
    ) -> None:
        """Revoke a single refresh token during rotation or logout."""
        token.is_revoked = True
        if replaced_by_id:
            token.replaced_by_token_id = replaced_by_id
        self.db.flush()

    def revoke_token_family(self, family_id: str) -> int:
        """Revoke every token belonging to a family (triggered upon token reuse)."""
        count = (
            self.db.query(RefreshToken)
            .filter(
                RefreshToken.family_id == family_id,
                RefreshToken.is_revoked == False,  # noqa: E712
            )
            .update({"is_revoked": True})
        )
        self.db.flush()
        return count

    def revoke_all_user_tokens(self, user_id: int) -> int:
        """Revoke all active refresh tokens for the given user (logout from all devices)."""
        count = (
            self.db.query(RefreshToken)
            .filter(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False,  # noqa: E712
            )
            .update({"is_revoked": True})
        )
        self.db.flush()
        return count

    def create_audit_log(
        self,
        action: str,
        user_id: int | None = None,
        entity_type: str | None = "auth",
        entity_id: str | None = None,
        details: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Persist an audit trail record for compliance and security events."""
        log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(log)
        self.db.flush()
        return log
