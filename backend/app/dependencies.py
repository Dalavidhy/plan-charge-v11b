"""Dependency injection for FastAPI."""

from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_async_session
from app.models import User, UserOrgRole
from app.utils.security import verify_token

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    """Get current authenticated user."""
    token = credentials.credentials

    # Verify token
    payload = verify_token(token, token_type="access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    query = (
        select(User)
        .options(
            selectinload(User.roles),
            selectinload(User.person),
            selectinload(User.organization),
        )
        .where(User.id == user_id)
        .where(User.is_active == True)
    )

    result = await session.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


def require_role(allowed_roles: list[str]):
    """Require specific roles for access."""

    async def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        """Check if user has required role."""
        user_roles = [role.role for role in current_user.roles]

        # Owner can access everything
        if "owner" in user_roles:
            return current_user

        # Check if user has any of the allowed roles
        if not any(role in allowed_roles for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return role_checker


# Role dependencies
require_owner = require_role(["owner"])
require_admin = require_role(["owner", "admin"])
require_manager = require_role(["owner", "admin", "manager"])
require_member = require_role(["owner", "admin", "manager", "member"])
require_viewer = require_role(["owner", "admin", "manager", "member", "viewer"])


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    session: AsyncSession = Depends(get_async_session),
) -> Optional[User]:
    """Get current user if authenticated, otherwise None."""
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, session)
    except HTTPException:
        return None
