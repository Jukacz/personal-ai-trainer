"""Controller layer for authentication endpoints.

Coordinates between views and repositories for user authentication operations.
"""

import logging
from typing import Optional, Tuple

from fastapi import HTTPException, status

from api.auth.jwt import create_access_token, create_refresh_token, verify_token
from api.auth.password import hash_password, verify_password
from api.repositories.user_repository import UserRepository, get_user_repository
from api.schemas.auth_requests import (
    GoogleAuthRequest,
    LoginRequest,
    RegisterRequest,
    UpdateProfileRequest,
)
from api.schemas.auth_responses import (
    AuthResponse,
    RefreshResponse,
    UserProfileResponse,
    UserResponse,
)
from api.services.google_oauth_service import (
    GoogleOAuthService,
    get_google_oauth_service,
)
from api.services.mock_data_seed_service import (
    MockDataSeedService,
    get_mock_data_seed_service,
)

logger = logging.getLogger(__name__)


class AuthController:
    """Controller for authentication operations.

    Handles user registration, login, token refresh, and profile management.
    """

    def __init__(
        self,
        repository: Optional[UserRepository] = None,
        google_service: Optional[GoogleOAuthService] = None,
        mock_seed_service: Optional[MockDataSeedService] = None,
    ):
        """Initialize the controller with dependencies.

        Args:
            repository: User repository instance (optional)
            google_service: Google OAuth service instance (optional)
            mock_seed_service: Mock seed service for onboarding data (optional)
        """
        self.repository = repository or get_user_repository()
        self.google_service = google_service or get_google_oauth_service()
        self.mock_seed_service = mock_seed_service or get_mock_data_seed_service()

    def register(self, request: RegisterRequest) -> Tuple[AuthResponse, str]:
        """Register a new user.

        Args:
            request: Registration request data

        Returns:
            Tuple of (AuthResponse, refresh_token)

        Raises:
            HTTPException: If email is already registered
        """
        logger.info(f"[AuthController] Registering user: {request.email}")

        # Check if email already exists
        existing_user = self.repository.get_by_email(request.email)
        if existing_user:
            logger.warning(
                f"[AuthController] Registration failed - email exists: {request.email}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email address is already registered",
            )

        # Create user
        password_hash = hash_password(request.password)
        user = self.repository.create(
            email=request.email,
            password_hash=password_hash,
            name=request.name,
        )
        self._seed_mock_data_for_new_user(user["_id"])

        # Generate tokens
        user_id = user["_id"]
        access_token = create_access_token(user_id, user["email"])
        refresh_token = create_refresh_token(user_id, user["email"])

        logger.info(f"[AuthController] User registered successfully: {user_id}")

        return (
            AuthResponse(
                access_token=access_token,
                user=self._user_to_response(user),
            ),
            refresh_token,
        )

    def login(self, request: LoginRequest) -> Tuple[AuthResponse, str]:
        """Authenticate a user with email and password.

        Args:
            request: Login request data

        Returns:
            Tuple of (AuthResponse, refresh_token)

        Raises:
            HTTPException: If credentials are invalid
        """
        logger.info(f"[AuthController] Login attempt: {request.email}")

        # Find user
        user = self.repository.get_by_email(request.email)
        if not user:
            logger.warning(
                f"[AuthController] Login failed - user not found: {request.email}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Verify password
        if not verify_password(request.password, user["password_hash"]):
            logger.warning(
                f"[AuthController] Login failed - invalid password: {request.email}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Generate tokens
        user_id = user["_id"]
        access_token = create_access_token(user_id, user["email"])
        refresh_token = create_refresh_token(user_id, user["email"])

        logger.info(f"[AuthController] User logged in successfully: {user_id}")

        return (
            AuthResponse(
                access_token=access_token,
                user=self._user_to_response(user),
            ),
            refresh_token,
        )

    def refresh(self, refresh_token: str) -> RefreshResponse:
        """Refresh an access token using a refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            RefreshResponse with new access token

        Raises:
            HTTPException: If refresh token is invalid or expired
        """
        logger.debug("[AuthController] Token refresh attempt")

        token_data = verify_token(refresh_token, "refresh")
        if not token_data:
            logger.warning("[AuthController] Token refresh failed - invalid token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        # Verify user still exists
        user = self.repository.get_by_id(token_data.user_id)
        if not user:
            logger.warning(
                f"[AuthController] Token refresh failed - user not found: "
                f"{token_data.user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        # Generate new access token
        access_token = create_access_token(token_data.user_id, token_data.email)

        logger.debug(f"[AuthController] Token refreshed for user: {token_data.user_id}")

        return RefreshResponse(access_token=access_token)

    def get_me(self, user_id: str) -> UserResponse:
        """Get the current user's profile.

        Args:
            user_id: The authenticated user's ID

        Returns:
            User profile information

        Raises:
            HTTPException: If user is not found
        """
        user = self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return self._user_to_response(user)

    def update_profile(
        self, user_id: str, request: UpdateProfileRequest
    ) -> UserResponse:
        """Update the current user's profile.

        Args:
            user_id: The authenticated user's ID
            request: Profile update data

        Returns:
            Updated user profile

        Raises:
            HTTPException: If user is not found
        """
        logger.info(f"[AuthController] Updating profile for user: {user_id}")

        # Build update data
        update_data = {}

        if request.name is not None:
            update_data["name"] = request.name

        # Profile fields
        profile_updates = {}
        if request.age is not None:
            profile_updates["profile.age"] = request.age
        if request.weight is not None:
            profile_updates["profile.weight"] = request.weight
        if request.target_weight is not None:
            profile_updates["profile.target_weight"] = request.target_weight

        update_data.update(profile_updates)

        if not update_data:
            # No fields to update, just return current user
            return self.get_me(user_id)

        user = self.repository.update(user_id, update_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        logger.info(f"[AuthController] Profile updated for user: {user_id}")

        return self._user_to_response(user)

    async def google_auth(
        self, request: GoogleAuthRequest
    ) -> Tuple[AuthResponse, str]:
        """Authenticate or register a user via Google OAuth.

        Args:
            request: Google OAuth request data

        Returns:
            Tuple of (AuthResponse, refresh_token)

        Raises:
            HTTPException: If Google authentication fails
        """
        logger.info("[AuthController] Google OAuth authentication attempt")

        try:
            # Exchange code for user info
            google_user = await self.google_service.exchange_code(
                request.code, request.redirect_uri
            )
        except ValueError as e:
            logger.error(f"[AuthController] Google OAuth failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

        google_id = google_user.get("sub")
        email = google_user.get("email")
        name = google_user.get("name", email.split("@")[0] if email else "User")

        if not google_id or not email:
            logger.error("[AuthController] Google OAuth - missing user info")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user information from Google",
            )

        # Try to find user by Google ID
        user = self.repository.get_by_google_id(google_id)

        if not user:
            # Try to find by email
            user = self.repository.get_by_email(email)

            if user:
                # Link Google ID to existing account
                self.repository.link_google(user["_id"], google_id)
                logger.info(
                    f"[AuthController] Linked Google ID to existing user: {user['_id']}"
                )
            else:
                # Create new user
                user = self.repository.create(
                    email=email,
                    password_hash="",  # No password for Google-only users
                    name=name,
                    google_id=google_id,
                )
                self._seed_mock_data_for_new_user(user["_id"])
                logger.info(
                    f"[AuthController] Created new user via Google: {user['_id']}"
                )

        # Generate tokens
        user_id = user["_id"]
        access_token = create_access_token(user_id, user["email"])
        refresh_token = create_refresh_token(user_id, user["email"])

        logger.info(
            f"[AuthController] Google OAuth successful for user: {user_id}"
        )

        return (
            AuthResponse(
                access_token=access_token,
                user=self._user_to_response(user),
            ),
            refresh_token,
        )

    def _user_to_response(self, user: dict) -> UserResponse:
        """Convert a user document to a response model.

        Args:
            user: User document from database

        Returns:
            UserResponse model
        """
        profile = user.get("profile", {})
        return UserResponse(
            id=user["_id"],
            email=user["email"],
            name=user["name"],
            profile=UserProfileResponse(
                age=profile.get("age"),
                weight=profile.get("weight"),
                target_weight=profile.get("target_weight"),
            ),
            created_at=user["created_at"],
        )

    def _seed_mock_data_for_new_user(self, user_id: str) -> None:
        """Seed onboarding mock data for newly created user when enabled."""
        if not self.mock_seed_service.is_auto_seed_enabled():
            return

        try:
            summary = self.mock_seed_service.seed_for_user(user_id=user_id, execute=True)
            logger.info(
                "[AuthController] Mock seed completed for user %s: plans=%s days=%s",
                user_id,
                summary.get("plans_created", 0),
                summary.get("days_created", 0),
            )
        except Exception:
            # Registration/login should not fail because of mock seed failure.
            logger.exception("[AuthController] Mock seed failed for user %s", user_id)


# Singleton instance for dependency injection
_controller_instance: Optional[AuthController] = None


def get_auth_controller() -> AuthController:
    """Get the auth controller singleton.

    Returns:
        AuthController instance
    """
    global _controller_instance
    if _controller_instance is None:
        _controller_instance = AuthController()
    return _controller_instance
