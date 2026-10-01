"""Authentication domain business logic and session security."""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.modules.auth.constants import (
    AUTH_LOCKOUT,
    AUTH_LOGIN_FAILED,
    AUTH_LOGIN_SUCCESS,
    AUTH_LOGOUT,
    AUTH_LOGOUT_ALL,
    AUTH_PASSWORD_CHANGED,
    AUTH_REGISTER,
    AUTH_TOKEN_REFRESH,
    AUTH_TOKEN_REUSE_DETECTED,
    LOCKOUT_DURATION_MINUTES,
    MAX_FAILED_LOGIN_ATTEMPTS,
)
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import (
    AuthConfigResponse,
    ChangePasswordRequest,
    DemoAccount,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserSummary,
)
from app.modules.users.models import User

logger = logging.getLogger(__name__)
settings = get_settings()


def ensure_utc(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware in UTC."""
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


class AuthService:
    """Authentication and session management service implementing security policies."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = AuthRepository(db)

    def _extract_permissions(self, user: User) -> list[str]:
        """Extract flat permission codes for a user, granting all if ADMIN."""
        if not user.role:
            return []
        if user.role.code == "ADMIN":
            from app.modules.users.models import Permission

            all_perms = self.db.query(Permission).all()
            return [p.code for p in all_perms]
        return [p.code for p in user.role.permissions]

    def _build_user_summary(self, user: User) -> UserSummary:
        """Construct UserSummary with permissions."""
        role_code = user.role.code if user.role else "MR"
        perms = self._extract_permissions(user)
        return UserSummary(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            role=role_code,
            force_password_change=user.force_password_change,
            permissions=perms,
        )

    def login(
        self,
        request: LoginRequest,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> TokenResponse:
        """Authenticate user credentials, enforce rate limits, and issue tokens."""
        now = datetime.now(UTC)
        user = self.repo.get_user_by_email(request.email)

        # Unknown user
        if not user:
            self.repo.create_audit_log(
                action=AUTH_LOGIN_FAILED,
                entity_id=request.email,
                details="Login failed: user not found",
                ip_address=ip_address,
                user_agent=user_agent,
            )
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Deactivated or soft-deleted user
        if not user.is_active or user.is_deleted:
            self.repo.create_audit_log(
                action=AUTH_LOGIN_FAILED,
                user_id=user.id,
                details="Login rejected: account deactivated",
                ip_address=ip_address,
                user_agent=user_agent,
            )
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated. Contact your administrator.",
            )

        # Lockout check
        if user.locked_until and ensure_utc(user.locked_until) > now:
            locked_until_utc = ensure_utc(user.locked_until)
            remaining_mins = max(1, int((locked_until_utc - now).total_seconds() // 60))
            self.repo.create_audit_log(
                action=AUTH_LOGIN_FAILED,
                user_id=user.id,
                details=f"Login attempt on locked account (remaining: {remaining_mins}m)",
                ip_address=ip_address,
                user_agent=user_agent,
            )
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is temporarily locked. Try again in {remaining_mins} minute(s).",
            )

        # Password check
        if not verify_password(request.password, user.hashed_password):
            attempts = user.failed_login_attempts + 1
            if attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
                lock_time = now + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                self.repo.update_user_failed_attempt(
                    user, attempts=attempts, locked_until=lock_time
                )
                self.repo.create_audit_log(
                    action=AUTH_LOCKOUT,
                    user_id=user.id,
                    details=f"Account locked after {attempts} failed attempts",
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
                self.db.commit()
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=(
                        f"Too many failed login attempts. "
                        f"Account locked for {LOCKOUT_DURATION_MINUTES} minutes."
                    ),
                )

            self.repo.update_user_failed_attempt(user, attempts=attempts)
            self.repo.create_audit_log(
                action=AUTH_LOGIN_FAILED,
                user_id=user.id,
                details=(
                    f"Login failed: bad password (attempt {attempts}/{MAX_FAILED_LOGIN_ATTEMPTS})"
                ),
                ip_address=ip_address,
                user_agent=user_agent,
            )
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Authentication succeeded: reset counters and record last login
        self.repo.update_user_login_success(user)

        # Issue access token and rotating refresh token
        user_summary = self._build_user_summary(user)
        access_token, expire_at = create_access_token(
            subject=user.id,
            role=user_summary.role,
            permissions=user_summary.permissions,
        )
        raw_refresh, token_hash, family_id, refresh_expire = create_refresh_token()
        self.repo.save_refresh_token(
            user_id=user.id,
            token_hash=token_hash,
            family_id=family_id,
            expires_at=refresh_expire,
        )

        self.repo.create_audit_log(
            action=AUTH_LOGIN_SUCCESS,
            user_id=user.id,
            details=f"Login successful for role {user_summary.role}",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.commit()

        expires_in = int((expire_at - now).total_seconds())
        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh,
            token_type="Bearer",
            expires_in=expires_in,
            user=user_summary,
        )

    def refresh(
        self,
        refresh_token_raw: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> TokenResponse:
        """Rotate refresh token: revoke existing, issue new pair, detect reuse."""
        now = datetime.now(UTC)
        token_hash = hash_token(refresh_token_raw)
        token_record = self.repo.get_refresh_token_by_hash(token_hash)

        if not token_record:
            self.repo.create_audit_log(
                action=AUTH_TOKEN_REFRESH,
                details="Refresh failed: token not found",
                ip_address=ip_address,
                user_agent=user_agent,
            )
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        # Reuse detection (Architecture 6.3)
        if token_record.is_revoked:
            revoked_count = self.repo.revoke_token_family(token_record.family_id)
            self.repo.create_audit_log(
                action=AUTH_TOKEN_REUSE_DETECTED,
                user_id=token_record.user_id,
                details=(
                    f"Token reuse detected! Revoked {revoked_count} "
                    f"tokens in family {token_record.family_id}"
                ),
                ip_address=ip_address,
                user_agent=user_agent,
            )
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=(
                    "Security alert: Token reuse detected. All active sessions have been revoked."
                ),
            )

        # Expiry check
        if ensure_utc(token_record.expires_at) < now:
            self.repo.revoke_refresh_token(token_record)
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired. Please log in again.",
            )

        # Check that user is still active and valid
        user = token_record.user
        if not user or not user.is_active or user.is_deleted:
            self.repo.revoke_refresh_token(token_record)
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated.",
            )

        # Issue new rotated refresh token in the SAME family
        new_raw_refresh, new_token_hash, _, new_refresh_expire = create_refresh_token(
            family_id=token_record.family_id
        )
        new_token_record = self.repo.save_refresh_token(
            user_id=user.id,
            token_hash=new_token_hash,
            family_id=token_record.family_id,
            expires_at=new_refresh_expire,
        )

        # Revoke the consumed token and link to successor
        self.repo.revoke_refresh_token(token_record, replaced_by_id=new_token_record.id)

        user_summary = self._build_user_summary(user)
        access_token, expire_at = create_access_token(
            subject=user.id,
            role=user_summary.role,
            permissions=user_summary.permissions,
        )

        self.repo.create_audit_log(
            action=AUTH_TOKEN_REFRESH,
            user_id=user.id,
            details=f"Token rotated successfully in family {token_record.family_id}",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.commit()

        expires_in = int((expire_at - now).total_seconds())
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_raw_refresh,
            token_type="Bearer",
            expires_in=expires_in,
            user=user_summary,
        )

    def logout(
        self,
        user: User,
        refresh_token_raw: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Revoke current refresh token and log audit event."""
        if refresh_token_raw:
            token_hash = hash_token(refresh_token_raw)
            token_record = self.repo.get_refresh_token_by_hash(token_hash)
            if token_record and token_record.user_id == user.id:
                self.repo.revoke_refresh_token(token_record)

        self.repo.create_audit_log(
            action=AUTH_LOGOUT,
            user_id=user.id,
            details="User logged out",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.commit()

    def logout_all(
        self,
        user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> int:
        """Revoke all active refresh tokens for the user across all devices."""
        count = self.repo.revoke_all_user_tokens(user.id)
        self.repo.create_audit_log(
            action=AUTH_LOGOUT_ALL,
            user_id=user.id,
            details=f"User logged out of all devices (revoked {count} tokens)",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.commit()
        return count

    def change_password(
        self,
        user: User,
        request: ChangePasswordRequest,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Verify old password, update to new hashed password, and revoke sessions."""
        if not verify_password(request.old_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password does not match",
            )

        if request.old_password == request.new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password",
            )

        user.hashed_password = hash_password(request.new_password)
        user.force_password_change = False
        self.repo.revoke_all_user_tokens(user.id)

        self.repo.create_audit_log(
            action=AUTH_PASSWORD_CHANGED,
            user_id=user.id,
            details="Password changed successfully; all existing sessions revoked",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.commit()

    def get_me(self, user: User) -> UserSummary:
        """Retrieve current authenticated user profile and permissions."""
        return self._build_user_summary(user)

    def register(
        self,
        request: RegisterRequest,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> UserSummary:
        """Register a new user account."""
        existing = self.repo.get_user_by_email(request.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email address already exists",
            )

        role = self.repo.get_role_by_code(request.role_code.upper())
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role '{request.role_code}' does not exist",
            )

        new_user = User(
            email=request.email.strip().lower(),
            full_name=request.full_name.strip(),
            phone=request.phone.strip() if request.phone else None,
            hashed_password=hash_password(request.password),
            role_id=role.id,
            is_active=True,
            force_password_change=False,
        )
        self.repo.create_user(new_user)
        self.repo.create_audit_log(
            action=AUTH_REGISTER,
            user_id=new_user.id,
            details=f"User registered with role {role.code}",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.commit()
        return self._build_user_summary(new_user)

    def get_auth_config(self) -> AuthConfigResponse:
        """Return public auth configuration, available roles, and dev demo accounts."""
        active_roles = self.repo.get_active_roles()
        role_codes = [r.code for r in active_roles]

        demo_accounts: list[DemoAccount] = []
        if settings.ENVIRONMENT == "development":
            demo_accounts = [
                DemoAccount(
                    role="MR",
                    email="mr@mediatehealthcare.com",
                    password="Mr@123",
                    label="Medical Representative",
                    description="Field force visits, DCR reporting, and chemist orders",
                ),
                DemoAccount(
                    role="MANAGER",
                    email="manager@mediatehealthcare.com",
                    password="Manager@123",
                    label="Regional Manager",
                    description="Team supervision, visit tracking, and approvals",
                ),
                DemoAccount(
                    role="ADMIN",
                    email="admin@mediatehealthcare.com",
                    password="Admin@123",
                    label="System Administrator",
                    description="Full administrative access and system configuration",
                ),
            ]

        return AuthConfigResponse(
            project_name=settings.PROJECT_NAME,
            version=settings.VERSION,
            environment=settings.ENVIRONMENT,
            roles=role_codes,
            demo_accounts=demo_accounts,
        )
