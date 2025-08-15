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
from app.models import User, UserOrgRole, RefreshToken, Organization
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
    UserInfo,
    RegisterRequest,
    RegisterResponse,
)
from app.schemas.sso import (
    SSOLoginRequest,
    SSOLoginResponse,
    SSOCallbackRequest,
    SSOTokenResponse,
    SSOLogoutRequest,
    SSOLogoutResponse,
    SSOStatusResponse,
)
from app.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.services.azure_sso import azure_sso
from app.config import settings

router = APIRouter()


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    session: AsyncSession = Depends(get_async_session),
) -> RegisterResponse:
    """Register a new user - DISABLED when SSO is mandatory."""
    if settings.SSO_MANDATORY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is disabled. Please use SSO to authenticate.",
        )
    
    # Check if user already exists
    query = select(User).where(User.email == request.email)
    result = await session.execute(query)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )
    
    # Get or create default organization
    org_query = select(Organization).where(Organization.name == "Default Organization")
    org_result = await session.execute(org_query)
    organization = org_result.scalar_one_or_none()
    
    if not organization:
        organization = Organization(
            name="Default Organization",
            timezone="Europe/Paris",
        )
        session.add(organization)
        await session.flush()
    
    # Create new user
    hashed_password = get_password_hash(request.password)
    new_user = User(
        email=request.email,
        password_hash=hashed_password,
        full_name=f"{request.first_name} {request.last_name}",
        org_id=organization.id,
        is_active=True,
    )
    
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    
    return RegisterResponse(
        id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_async_session),
) -> LoginResponse:
    """Login with email and password - DISABLED when SSO is mandatory."""
    if settings.SSO_MANDATORY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Direct login is disabled. Please use SSO to authenticate.",
        )
    
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


# SSO Endpoints
@router.get("/sso/status", response_model=SSOStatusResponse)
async def get_sso_status() -> SSOStatusResponse:
    """Get SSO configuration status."""
    return SSOStatusResponse(
        enabled=settings.FEATURE_SSO,
        configured=settings.azure_ad_configured,
        provider="Azure AD",
        login_url="/api/v1/auth/sso/login" if settings.azure_ad_configured else None,
        mandatory=settings.SSO_MANDATORY,  # Add mandatory flag to response
    )


@router.post("/sso/login", response_model=SSOLoginResponse)
async def sso_login(
    request: SSOLoginRequest = SSOLoginRequest(),
) -> SSOLoginResponse:
    """Initiate SSO login flow."""
    if not settings.FEATURE_SSO:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SSO is not enabled",
        )
    
    if not settings.azure_ad_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Azure AD is not configured",
        )
    
    # Get authorization URL
    auth_url = azure_sso.get_auth_url(state=request.state)
    
    return SSOLoginResponse(
        auth_url=auth_url,
        state=request.state,
    )


@router.post("/sso/token-exchange", response_model=SSOTokenResponse)
async def sso_token_exchange(
    request: dict,  # Will contain azureToken, idToken, userInfo
    session: AsyncSession = Depends(get_async_session),
) -> SSOTokenResponse:
    """Exchange Azure AD tokens from frontend for backend tokens."""
    import logging
    import time
    logger = logging.getLogger(__name__)
    
    if not settings.FEATURE_SSO or not settings.azure_ad_configured:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SSO is not available",
        )
    
    try:
        # Extract data from frontend request
        user_info = request.get("userInfo", {})
        email = user_info.get("email")
        name = user_info.get("name", "")
        azure_id = user_info.get("id")
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not found in user info"
            )
        
        logger.info(f"SSO token exchange for user: {email}")
        
        # Create user info dict for get_or_create_user
        azure_user_info = {
            "oid": azure_id,
            "preferred_username": email,
            "name": name,
            "email": email,
        }
        
        # Get or create user
        user = await azure_sso.get_or_create_user(azure_user_info, session)
        
        # Create application tokens
        tokens = azure_sso.create_app_tokens(user)
        
        # Clean up old refresh tokens for this user to prevent duplicates
        token_hash = hashlib.sha256(tokens["refresh_token"].encode()).hexdigest()
        
        # Try up to 3 times with a small delay to handle race conditions
        for attempt in range(3):
            try:
                # First, try to delete any existing token with the same hash
                delete_result = await session.execute(
                    select(RefreshToken).where(RefreshToken.token_hash == token_hash)
                )
                existing_token = delete_result.scalar_one_or_none()
                
                if existing_token:
                    logger.warning(f"Found existing token with same hash (attempt {attempt + 1}), replacing it for user {user.email}")
                    await session.delete(existing_token)
                    await session.flush()  # Important: flush the deletion before adding new token
                
                # Also clean up old tokens for this user (keep only last 5)
                old_tokens_query = (
                    select(RefreshToken)
                    .where(RefreshToken.user_id == user.id)
                    .where(RefreshToken.revoked_at.is_(None))
                    .order_by(RefreshToken.created_at.desc())
                    .offset(4)  # Keep last 4, will add 1 new = 5 total
                )
                old_tokens_result = await session.execute(old_tokens_query)
                for old_token in old_tokens_result.scalars():
                    old_token.revoked_at = datetime.utcnow()
                
                # Store new refresh token
                refresh_token = RefreshToken(
                    user_id=user.id,
                    org_id=user.org_id,
                    token_hash=token_hash,
                    expires_at=datetime.utcnow() + timedelta(days=30),
                    device_info={
                        "user_agent": "SSO Client",
                        "provider": "Azure AD",
                    },
                )
                session.add(refresh_token)
                await session.commit()
                logger.info(f"SSO login successful for user: {user.email}")
                break  # Success, exit the retry loop
                
            except Exception as token_error:
                if "duplicate key value" in str(token_error) and attempt < 2:
                    logger.warning(f"Token duplicate error on attempt {attempt + 1}, retrying...")
                    await session.rollback()
                    time.sleep(0.1 * (attempt + 1))  # Small delay before retry
                    # Generate a new token to avoid duplicates
                    tokens = azure_sso.create_app_tokens(user)
                    token_hash = hashlib.sha256(tokens["refresh_token"].encode()).hexdigest()
                else:
                    raise token_error
        
        # Load user relationships for response
        await session.refresh(user, attribute_names=["roles", "person", "organization"])
        
        # Prepare user info
        user_info = {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "org_id": str(user.org_id),
            "roles": [role.role for role in user.roles],
            "person_id": str(user.person_id) if user.person_id else None,
        }
        
        return SSOTokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            user=user_info,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SSO callback error: {str(e)}", exc_info=True)
        # Check if it's an Azure AD error
        if "AADSTS" in str(e):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Le code d'autorisation a déjà été utilisé ou est expiré. Veuillez réessayer."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SSO authentication failed: {str(e)}"
        )


@router.post("/sso/logout", response_model=SSOLogoutResponse)
async def sso_logout(
    request: SSOLogoutRequest = SSOLogoutRequest(),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> SSOLogoutResponse:
    """Get SSO logout URL and revoke tokens."""
    # Revoke all refresh tokens for the user
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == current_user.id)
        .where(RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.utcnow())
    )
    await session.commit()
    
    # Get logout URL
    post_logout_uri = str(request.post_logout_redirect_uri) if request.post_logout_redirect_uri else None
    logout_url = azure_sso.get_logout_url(post_logout_redirect_uri=post_logout_uri)
    
    return SSOLogoutResponse(logout_url=logout_url)