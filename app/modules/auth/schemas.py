"""Pydantic schemas for Authentication and Session requests/responses."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    """User credentials for standard email/password authentication."""

    email: EmailStr
    password: str = Field(..., min_length=6, description="Plaintext login password")


class UserSummary(BaseModel):
    """Safe user profile overview without sensitive credentials."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    phone: str | None = None
    role: str
    force_password_change: bool = False
    permissions: list[str] = []


class TokenResponse(BaseModel):
    """JWT access token and rotating refresh token response."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = Field(..., description="Access token expiration in seconds")
    user: UserSummary


class RefreshTokenRequest(BaseModel):
    """Refresh token payload used to rotate tokens."""

    refresh_token: str = Field(..., description="The opaque refresh token string")


class LogoutRequest(BaseModel):
    """Optional payload to explicitly specify the refresh token to revoke."""

    refresh_token: str | None = None


class ChangePasswordRequest(BaseModel):
    """Request payload for updating password."""

    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, description="Minimum 8 characters")


class RegisterRequest(BaseModel):
    """Self-registration request for new personnel."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: str | None = None
    role_code: str = Field(default="MR", description="Requested role: MR, MANAGER, or ADMIN")


class MessageResponse(BaseModel):
    """Generic status response."""

    message: str
    success: bool = True


class DemoAccount(BaseModel):
    """Development/preview demo credentials."""

    role: str
    email: str
    password: str
    label: str
    description: str | None = None


class AuthConfigResponse(BaseModel):
    """Dynamic auth configuration and available roles provided by backend."""

    project_name: str
    version: str
    environment: str
    roles: list[str]
    demo_accounts: list[DemoAccount] = []
