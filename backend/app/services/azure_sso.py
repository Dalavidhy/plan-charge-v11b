"""Azure AD SSO service for authentication."""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

import msal
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Organization, User
from app.utils.security import create_access_token, create_refresh_token

logger = logging.getLogger(__name__)


class AzureSSO:
    """Service for Azure AD SSO authentication."""

    def __init__(self):
        """Initialize Azure SSO service."""
        self.tenant_id = settings.AZURE_AD_TENANT_ID
        self.client_id = settings.AZURE_AD_CLIENT_ID
        self.client_secret = settings.AZURE_AD_CLIENT_SECRET
        self.redirect_uri = settings.AZURE_AD_REDIRECT_URI
        self.authority = settings.azure_ad_authority_url
        self.scopes = settings.AZURE_AD_SCOPES

        # Create MSAL confidential client application
        self.msal_app = None
        if settings.azure_ad_configured:
            self.msal_app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=self.authority,
            )

    def get_auth_url(self, state: Optional[str] = None) -> str:
        """Get the authorization URL for Azure AD login.

        Args:
            state: Optional state parameter for CSRF protection

        Returns:
            Authorization URL
        """
        if not self.msal_app:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Azure AD is not configured",
            )

        auth_url = self.msal_app.get_authorization_request_url(
            scopes=self.scopes,
            state=state,
            redirect_uri=self.redirect_uri,
        )

        return auth_url

    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code from Azure AD

        Returns:
            Token response from Azure AD
        """
        if not self.msal_app:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Azure AD is not configured",
            )

        try:
            logger.info(f"Exchanging authorization code for token")
            logger.info(f"Redirect URI: {self.redirect_uri}")
            logger.info(f"Scopes: {self.scopes}")

            result = self.msal_app.acquire_token_by_authorization_code(
                code=code,
                scopes=self.scopes,
                redirect_uri=self.redirect_uri,
            )

            if "error" in result:
                error_msg = result.get("error_description", "Authentication failed")
                error_code = result.get("error", "unknown_error")
                logger.error(
                    f"Azure AD token exchange error - Code: {error_code}, Description: {error_msg}"
                )
                logger.error(f"Full error response: {result}")

                # Provide more specific error messages
                if "AADSTS700" in error_msg:
                    detail = (
                        "Configuration error: Check your redirect URI in Azure Portal"
                    )
                elif "AADSTS50011" in error_msg:
                    detail = f"Redirect URI mismatch. Expected: {self.redirect_uri}. Check Azure Portal configuration."
                elif "AADSTS70000" in error_msg:
                    detail = "Invalid authorization code. Please try logging in again."
                elif "invalid_client" in error_code:
                    detail = (
                        "Invalid client credentials. Check your Client ID and Secret."
                    )
                else:
                    detail = error_msg

                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail=detail
                )

            logger.info("Successfully exchanged code for token")
            return result

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error exchanging code for token: {e}", exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to authenticate with Azure AD: {str(e)}",
            )

    async def get_or_create_user(
        self, azure_user_info: Dict[str, Any], session: AsyncSession
    ) -> User:
        """Get existing user or create new one from Azure AD info.

        Args:
            azure_user_info: User information from Azure AD token
            session: Database session

        Returns:
            User object
        """
        # Extract user information
        azure_id = azure_user_info.get("oid") or azure_user_info.get("sub")
        email = azure_user_info.get("preferred_username") or azure_user_info.get(
            "email"
        )
        full_name = azure_user_info.get("name", "")

        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not found in Azure AD response",
            )

        # Validate email domain if allowed domains are configured
        if settings.SSO_ALLOWED_DOMAINS:
            email_domain = email.split("@")[-1].lower()
            allowed_domains = [d.lower() for d in settings.SSO_ALLOWED_DOMAINS]

            if email_domain not in allowed_domains:
                logger.warning(f"Unauthorized login attempt from email: {email}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Only users from authorized domains ({', '.join(allowed_domains)}) are allowed.",
                )

        # Check if user exists by Azure ID
        if azure_id:
            query = select(User).where(User.azure_id == azure_id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()
            if user:
                # Update user info from Azure AD
                user.email = email
                user.full_name = full_name
                user.last_login_at = datetime.utcnow()
                await session.commit()
                return user

        # Check if user exists by email
        query = select(User).where(User.email == email)
        result = await session.execute(query)
        user = result.scalar_one_or_none()

        if user:
            # Update existing user with Azure ID
            user.azure_id = azure_id
            user.full_name = full_name or user.full_name
            user.last_login_at = datetime.utcnow()
            await session.commit()
            return user

        # Create new user
        # Get or create default organization
        org_query = select(Organization).where(Organization.name == "NDA Partners")
        org_result = await session.execute(org_query)
        organization = org_result.scalar_one_or_none()

        if not organization:
            organization = Organization(
                name="NDA Partners",
                timezone="Europe/Paris",
            )
            session.add(organization)
            await session.flush()

        # Create new user without password (SSO only)
        new_user = User(
            email=email,
            azure_id=azure_id,
            full_name=full_name,
            org_id=organization.id,
            is_active=True,
            last_login_at=datetime.utcnow(),
        )

        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        logger.info(f"Created new user from Azure AD: {email}")
        return new_user

    def create_app_tokens(self, user: User) -> Dict[str, str]:
        """Create application JWT tokens for the user.

        Args:
            user: User object

        Returns:
            Dictionary with access_token and refresh_token
        """
        access_token = create_access_token(
            subject=str(user.id),
            additional_claims={"org_id": str(user.org_id)},
        )
        refresh_token_str = create_refresh_token(
            subject=str(user.id),
            additional_claims={"org_id": str(user.org_id)},
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token_str,
            "token_type": "bearer",
        }

    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate an Azure AD token.

        Args:
            token: Access token from Azure AD

        Returns:
            Token claims if valid, None otherwise
        """
        if not self.msal_app:
            return None

        # In production, you would validate the token signature
        # For now, we'll trust the token if it comes from our flow
        # MSAL handles token validation internally during acquire_token_* calls

        # You can implement additional validation here if needed
        # For example, checking token expiration, audience, etc.

        return None  # Simplified for now

    def get_logout_url(self, post_logout_redirect_uri: Optional[str] = None) -> str:
        """Get the Azure AD logout URL.

        Args:
            post_logout_redirect_uri: URL to redirect after logout

        Returns:
            Logout URL
        """
        logout_url = f"{self.authority}/oauth2/v2.0/logout"

        if post_logout_redirect_uri:
            logout_url += f"?post_logout_redirect_uri={post_logout_redirect_uri}"

        return logout_url


# Create singleton instance
azure_sso = AzureSSO()
