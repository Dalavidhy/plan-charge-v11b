"""Pydantic schemas for SSO authentication."""

from typing import Optional
from pydantic import BaseModel, HttpUrl


class SSOLoginRequest(BaseModel):
    """Request for initiating SSO login."""
    state: Optional[str] = None
    redirect_uri: Optional[str] = None


class SSOLoginResponse(BaseModel):
    """Response with SSO login URL."""
    auth_url: str
    state: Optional[str] = None


class SSOCallbackRequest(BaseModel):
    """Request from SSO callback."""
    code: str
    state: Optional[str] = None
    session_state: Optional[str] = None


class SSOTokenResponse(BaseModel):
    """Response with application tokens after SSO."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict  # User information


class SSOLogoutRequest(BaseModel):
    """Request for SSO logout."""
    post_logout_redirect_uri: Optional[HttpUrl] = None


class SSOLogoutResponse(BaseModel):
    """Response with SSO logout URL."""
    logout_url: str


class SSOStatusResponse(BaseModel):
    """Response with SSO configuration status."""
    enabled: bool
    configured: bool
    provider: str = "Azure AD"
    login_url: Optional[str] = None
    mandatory: bool = False  # Is SSO mandatory for authentication