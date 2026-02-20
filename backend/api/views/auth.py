"""Authentication routes - API endpoints for user authentication.

Provides REST endpoints for user registration, login, token refresh,
logout, and profile management.
"""

import os

from fastapi import APIRouter, Cookie, Depends, Response, status

from api.auth.dependencies import get_current_user
from api.controllers.auth_controller import AuthController, get_auth_controller
from api.schemas.auth_requests import (
    GoogleAuthRequest,
    LoginRequest,
    RegisterRequest,
    UpdateProfileRequest,
)
from api.schemas.auth_responses import AuthResponse, RefreshResponse, UserResponse
from api.schemas.responses import ErrorResponse

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

# Cookie settings
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
COOKIE_SAMESITE = "lax"
COOKIE_MAX_AGE = 7 * 24 * 60 * 60  # 7 days in seconds
COOKIE_PATH = "/api/v1/auth"


def _set_refresh_token_cookie(response: Response, refresh_token: str) -> None:
    """Set the refresh token as an HTTP-only cookie.

    Args:
        response: FastAPI response object
        refresh_token: The refresh token to set
    """
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=COOKIE_MAX_AGE,
        path=COOKIE_PATH,
    )


def _clear_refresh_token_cookie(response: Response) -> None:
    """Clear the refresh token cookie.

    Args:
        response: FastAPI response object
    """
    response.delete_cookie(
        key="refresh_token",
        path=COOKIE_PATH,
    )


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="""
Create a new user account with email and password.

**Request body:**
- `email`: Valid email address (must be unique)
- `password`: Password with minimum 8 characters
- `name`: User's display name

**Response:**
- Access token in response body
- Refresh token in HTTP-only cookie

**Errors:**
- `409 Conflict`: Email already registered
- `422 Unprocessable Entity`: Invalid input data
    """,
    responses={
        201: {"description": "User registered successfully", "model": AuthResponse},
        409: {"description": "Email already registered", "model": ErrorResponse},
        422: {"description": "Invalid input data", "model": ErrorResponse},
    },
)
async def register(
    request: RegisterRequest,
    response: Response,
    controller: AuthController = Depends(get_auth_controller),
) -> AuthResponse:
    """Register a new user.

    Args:
        request: Registration data
        response: FastAPI response for setting cookies
        controller: Auth controller instance

    Returns:
        Authentication response with access token and user info
    """
    auth_response, refresh_token = controller.register(request)
    _set_refresh_token_cookie(response, refresh_token)
    return auth_response


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login with email and password",
    description="""
Authenticate with email and password.

**Request body:**
- `email`: User's email address
- `password`: User's password

**Response:**
- Access token in response body
- Refresh token in HTTP-only cookie

**Errors:**
- `401 Unauthorized`: Invalid email or password
    """,
    responses={
        200: {"description": "Login successful", "model": AuthResponse},
        401: {"description": "Invalid credentials", "model": ErrorResponse},
    },
)
async def login(
    request: LoginRequest,
    response: Response,
    controller: AuthController = Depends(get_auth_controller),
) -> AuthResponse:
    """Login with email and password.

    Args:
        request: Login credentials
        response: FastAPI response for setting cookies
        controller: Auth controller instance

    Returns:
        Authentication response with access token and user info
    """
    auth_response, refresh_token = controller.login(request)
    _set_refresh_token_cookie(response, refresh_token)
    return auth_response


@router.post(
    "/google",
    response_model=AuthResponse,
    summary="Authenticate with Google OAuth",
    description="""
Authenticate or register using Google OAuth.

**Request body:**
- `code`: Authorization code from Google OAuth flow
- `redirect_uri`: Redirect URI used in the OAuth flow

**Behavior:**
- If user exists with this Google ID: Login
- If user exists with same email: Link Google ID and login
- Otherwise: Create new account

**Response:**
- Access token in response body
- Refresh token in HTTP-only cookie
    """,
    responses={
        200: {"description": "Google authentication successful", "model": AuthResponse},
        400: {"description": "Failed to authenticate with Google", "model": ErrorResponse},
    },
)
async def google_auth(
    request: GoogleAuthRequest,
    response: Response,
    controller: AuthController = Depends(get_auth_controller),
) -> AuthResponse:
    """Authenticate with Google OAuth.

    Args:
        request: Google OAuth data
        response: FastAPI response for setting cookies
        controller: Auth controller instance

    Returns:
        Authentication response with access token and user info
    """
    auth_response, refresh_token = await controller.google_auth(request)
    _set_refresh_token_cookie(response, refresh_token)
    return auth_response


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    summary="Refresh access token",
    description="""
Get a new access token using the refresh token from cookies.

The refresh token is automatically read from the HTTP-only cookie
set during login or registration.

**Response:**
- New access token in response body

**Errors:**
- `401 Unauthorized`: Invalid or expired refresh token
    """,
    responses={
        200: {"description": "Token refreshed successfully", "model": RefreshResponse},
        401: {"description": "Invalid or expired refresh token", "model": ErrorResponse},
    },
)
async def refresh_token(
    refresh_token: str = Cookie(None, alias="refresh_token"),
    controller: AuthController = Depends(get_auth_controller),
) -> RefreshResponse:
    """Refresh the access token.

    Args:
        refresh_token: Refresh token from cookie
        controller: Auth controller instance

    Returns:
        New access token
    """
    from fastapi import HTTPException

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
        )

    return controller.refresh(refresh_token)


@router.post(
    "/logout",
    summary="Logout user",
    description="""
Logout the current user by clearing the refresh token cookie.

Note: This only clears the cookie on the client side.
The access token will remain valid until it expires.
    """,
    responses={
        200: {"description": "Logged out successfully"},
    },
)
async def logout(response: Response) -> dict:
    """Logout the current user.

    Args:
        response: FastAPI response for clearing cookies

    Returns:
        Success message
    """
    _clear_refresh_token_cookie(response)
    return {"message": "Logged out successfully"}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="""
Get the profile of the currently authenticated user.

**Authorization:**
Requires Bearer token in Authorization header.
    """,
    responses={
        200: {"description": "User profile", "model": UserResponse},
        401: {"description": "Not authenticated", "model": ErrorResponse},
    },
)
async def get_me(
    user: dict = Depends(get_current_user),
    controller: AuthController = Depends(get_auth_controller),
) -> UserResponse:
    """Get the current user's profile.

    Args:
        user: Current authenticated user
        controller: Auth controller instance

    Returns:
        User profile information
    """
    return controller.get_me(user["_id"])


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
    description="""
Update the profile of the currently authenticated user.

All fields are optional - only provided fields will be updated.

**Request body:**
- `name`: New display name (optional)
- `age`: Age in years, 16-100 (optional)
- `weight`: Current weight in kg, 30-300 (optional)
- `target_weight`: Target weight in kg, 30-300 (optional)

**Authorization:**
Requires Bearer token in Authorization header.
    """,
    responses={
        200: {"description": "Profile updated", "model": UserResponse},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        422: {"description": "Invalid input data", "model": ErrorResponse},
    },
)
async def update_me(
    request: UpdateProfileRequest,
    user: dict = Depends(get_current_user),
    controller: AuthController = Depends(get_auth_controller),
) -> UserResponse:
    """Update the current user's profile.

    Args:
        request: Profile update data
        user: Current authenticated user
        controller: Auth controller instance

    Returns:
        Updated user profile
    """
    return controller.update_profile(user["_id"], request)
