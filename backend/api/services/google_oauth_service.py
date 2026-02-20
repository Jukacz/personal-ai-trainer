"""Google OAuth service for authentication.

Handles the exchange of Google OAuth authorization codes for user information.
"""

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


class GoogleOAuthService:
    """Service for Google OAuth authentication.

    Handles exchanging authorization codes for access tokens and
    retrieving user information from Google.
    """

    def __init__(self):
        """Initialize the service with Google OAuth credentials.

        Credentials are loaded from environment variables:
        - GOOGLE_CLIENT_ID: Google OAuth client ID
        - GOOGLE_CLIENT_SECRET: Google OAuth client secret
        """
        self.client_id = os.getenv("GOOGLE_CLIENT_ID", "")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")

    async def exchange_code(self, code: str, redirect_uri: str) -> dict:
        """Exchange an authorization code for user information.

        Args:
            code: Authorization code from Google OAuth flow
            redirect_uri: The redirect URI used in the OAuth flow

        Returns:
            Dictionary containing Google user information:
            - sub: Google user ID
            - email: User's email address
            - name: User's display name
            - picture: URL to profile picture (optional)

        Raises:
            ValueError: If the exchange fails or user info cannot be retrieved
        """
        if not self.client_id or not self.client_secret:
            logger.error(
                "[GoogleOAuth] Missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET"
            )
            raise ValueError(
                "Google OAuth is not configured. "
                "Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."
            )

        async with httpx.AsyncClient() as client:
            # Exchange authorization code for access token
            logger.debug("[GoogleOAuth] Exchanging authorization code for token")

            token_response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )

            if token_response.status_code != 200:
                logger.error(
                    f"[GoogleOAuth] Token exchange failed: "
                    f"{token_response.status_code} - {token_response.text}"
                )
                raise ValueError("Failed to exchange Google authorization code")

            tokens = token_response.json()
            access_token = tokens.get("access_token")

            if not access_token:
                logger.error("[GoogleOAuth] No access token in response")
                raise ValueError("Failed to get access token from Google")

            # Get user information
            logger.debug("[GoogleOAuth] Fetching user information")

            userinfo_response = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if userinfo_response.status_code != 200:
                logger.error(
                    f"[GoogleOAuth] User info fetch failed: "
                    f"{userinfo_response.status_code} - {userinfo_response.text}"
                )
                raise ValueError("Failed to get user information from Google")

            user_info = userinfo_response.json()
            logger.info(
                f"[GoogleOAuth] Successfully retrieved user info for: "
                f"{user_info.get('email')}"
            )

            return user_info


# Singleton instance for dependency injection
_service_instance: Optional[GoogleOAuthService] = None


def get_google_oauth_service() -> GoogleOAuthService:
    """Get the Google OAuth service singleton.

    Returns:
        GoogleOAuthService instance
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = GoogleOAuthService()
    return _service_instance
