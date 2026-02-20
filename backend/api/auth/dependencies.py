"""FastAPI dependencies for authentication.

Provides dependency injection functions for protecting routes.
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.auth.jwt import verify_token
from api.repositories.user_repository import get_user_repository

# HTTP Bearer security scheme
# auto_error=False allows optional authentication
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """Get the current authenticated user.

    Use this dependency for routes that require authentication.

    Args:
        credentials: HTTP Bearer credentials from Authorization header

    Returns:
        User document from database

    Raises:
        HTTPException: If not authenticated or token is invalid
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = verify_token(credentials.credentials, "access")
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_repository().get_by_id(token_data.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """Get the current user if authenticated, otherwise return None.

    Use this dependency for routes that work with or without authentication
    but may provide additional features for authenticated users.

    Args:
        credentials: HTTP Bearer credentials from Authorization header

    Returns:
        User document from database if authenticated, None otherwise
    """
    if not credentials:
        return None

    token_data = verify_token(credentials.credentials, "access")
    if not token_data:
        return None

    return get_user_repository().get_by_id(token_data.user_id)
