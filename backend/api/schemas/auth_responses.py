"""Authentication response schemas.

Contains Pydantic models for authentication-related API responses.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserProfileResponse(BaseModel):
    """User profile information in API responses.

    Attributes:
        age: User's age in years
        weight: Current weight in kg
        target_weight: Target weight in kg
    """

    age: Optional[int] = None
    weight: Optional[float] = None
    target_weight: Optional[float] = None


class UserResponse(BaseModel):
    """User information in API responses.

    Attributes:
        id: Unique user identifier
        email: User's email address
        name: User's display name
        profile: User's fitness profile
        created_at: Account creation timestamp
    """

    id: str
    email: str
    name: str
    profile: UserProfileResponse
    created_at: datetime


class AuthResponse(BaseModel):
    """Response for successful authentication (login/register).

    Attributes:
        access_token: JWT access token for API authorization
        token_type: Token type (always "bearer")
        user: Authenticated user information
    """

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshResponse(BaseModel):
    """Response for successful token refresh.

    Attributes:
        access_token: New JWT access token
        token_type: Token type (always "bearer")
    """

    access_token: str
    token_type: str = "bearer"
