"""Authentication endpoints."""

import hashlib
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_async_session
from app.dependencies import get_current_active_user
from app.models import User, UserOrgRole, RefreshToken
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
    UserInfo,
)
from app.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
)

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_async_session),
) -> LoginResponse:
    """Login with email and password."""
    # Find user by email
    query = (
        select(User)
        .options(
            selectinload(User.roles),
            selectinload(User.person),
            selectinload(User.organization),
        )
        .where(User.email == request.email)
        .where(User.is_active == True)
    )
    
    result = await session.execute(query)
    user = result.scalar_one_or_none()
    
    # Check if user exists and password is correct
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token = create_access_token(
        subject=str(user.id),
        additional_claims={"org_id": str(user.org_id)},
    )
    refresh_token_str = create_refresh_token(
        subject=str(user.id),
        additional_claims={"org_id": str(user.org_id)},
    )
    
    # Store refresh token in database
    refresh_token = RefreshToken(
        user_id=user.id,
        org_id=user.org_id,
        token_hash=hashlib.sha256(refresh_token_str.encode()).hexdigest(),
        expires_at=datetime.utcnow() + timedelta(days=30),
        device_info={
            "user_agent": "API Client",  # In real app, get from request headers
        },
    )
    session.add(refresh_token)
    
    # Update last login
    await session.execute(
        update(User)
        .where(User.id == user.id)
        .values(last_login_at=datetime.utcnow())
    )
    
    await session.commit()
    
    # Prepare user info
    user_info = UserInfo(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        org_id=user.org_id,
        roles=[role.role for role in user.roles],
        person_id=user.person_id,
    )
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
        token_type="bearer",
        user=user_info,
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    request: RefreshRequest,
    session: AsyncSession = Depends(get_async_session),
) -> RefreshResponse:
    """Refresh access token using refresh token."""
    # Verify refresh token
    payload = verify_token(request.refresh_token, token_type="refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    # Check if refresh token exists in database
    token_hash = hashlib.sha256(request.refresh_token.encode()).hexdigest()
    query = (
        select(RefreshToken)
        .where(RefreshToken.user_id == user_id)
        .where(RefreshToken.token_hash == token_hash)
        .where(RefreshToken.revoked_at.is_(None))
    )
    
    result = await session.execute(query)
    db_token = result.scalar_one_or_none()
    
    if not db_token or not db_token.is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    
    # Get user
    query = select(User).where(User.id == user_id).where(User.is_active == True)
    result = await session.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    # Revoke old refresh token
    db_token.revoked_at = datetime.utcnow()
    
    # Create new tokens
    new_access_token = create_access_token(
        subject=str(user.id),
        additional_claims={"org_id": str(user.org_id)},
    )
    new_refresh_token = create_refresh_token(
        subject=str(user.id),
        additional_claims={"org_id": str(user.org_id)},
    )
    
    # Store new refresh token
    new_db_token = RefreshToken(
        user_id=user.id,
        org_id=user.org_id,
        token_hash=hashlib.sha256(new_refresh_token.encode()).hexdigest(),
        expires_at=datetime.utcnow() + timedelta(days=30),
        device_info=db_token.device_info,
    )
    session.add(new_db_token)
    
    await session.commit()
    
    return RefreshResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    refresh_token: RefreshRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """Logout and revoke refresh token."""
    # Hash the refresh token
    token_hash = hashlib.sha256(refresh_token.refresh_token.encode()).hexdigest()
    
    # Revoke the refresh token
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == current_user.id)
        .where(RefreshToken.token_hash == token_hash)
        .values(revoked_at=datetime.utcnow())
    )
    
    await session.commit()


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    request: ForgotPasswordRequest,
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, str]:
    """Request password reset."""
    # Always return success to prevent email enumeration
    # In a real application, send an email with reset link
    
    # Check if user exists (but don't reveal this to the client)
    query = select(User).where(User.email == request.email)
    result = await session.execute(query)
    user = result.scalar_one_or_none()
    
    if user:
        # In production, generate reset token and send email
        # For now, just log the request
        pass
    
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    request: ResetPasswordRequest,
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """Reset password with token."""
    # In production, verify the reset token
    # For now, this is a placeholder
    
    # Verify token (simplified for demo)
    # In production, use a proper token storage/verification system
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset not implemented in demo",
    )


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """Change password for current user."""
    # Verify current password
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )
    
    # Update password
    await session.execute(
        update(User)
        .where(User.id == current_user.id)
        .values(password_hash=get_password_hash(request.new_password))
    )
    
    # Revoke all refresh tokens for security
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == current_user.id)
        .where(RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.utcnow())
    )
    
    await session.commit()


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
) -> UserInfo:
    """Get current user information."""
    return UserInfo(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        org_id=current_user.org_id,
        roles=[role.role for role in current_user.roles],
        person_id=current_user.person_id,
    )