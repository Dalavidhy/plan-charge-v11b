"""Authentication schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    """Register request schema."""

    email: EmailStr
    password: str
    first_name: str
    last_name: str


class RegisterResponse(BaseModel):
    """Register response schema."""

    id: UUID
    email: EmailStr
    full_name: str
    message: str = "User registered successfully"


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserInfo(BaseModel):
    """User info in auth response."""

    id: UUID
    email: EmailStr
    full_name: str
    org_id: UUID
    roles: list[str]
    person_id: Optional[UUID] = None

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Login response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserInfo


class RefreshRequest(BaseModel):
    """Refresh token request."""

    refresh_token: str


class RefreshResponse(BaseModel):
    """Refresh token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    """Forgot password request."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password request."""

    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    """Change password request."""

    current_password: str
    new_password: str
