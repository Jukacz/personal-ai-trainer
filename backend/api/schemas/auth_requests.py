"""Authentication request schemas.

Contains Pydantic models for authentication-related API requests.
"""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Request body for user registration.

    Attributes:
        email: Valid email address
        password: Password with minimum 8 characters
        name: User's display name (1-100 characters)
    """

    email: EmailStr = Field(description="User's email address")
    password: str = Field(
        min_length=8, description="Password (minimum 8 characters)"
    )
    name: str = Field(
        min_length=1, max_length=100, description="User's display name"
    )


class LoginRequest(BaseModel):
    """Request body for user login.

    Attributes:
        email: User's email address
        password: User's password
    """

    email: EmailStr = Field(description="User's email address")
    password: str = Field(description="User's password")


class GoogleAuthRequest(BaseModel):
    """Request body for Google OAuth authentication.

    Attributes:
        code: Authorization code from Google OAuth flow
        redirect_uri: The redirect URI used in the OAuth flow
    """

    code: str = Field(description="Google OAuth authorization code")
    redirect_uri: str = Field(
        description="Redirect URI used in the OAuth flow"
    )


class UpdateProfileRequest(BaseModel):
    """Request body for updating user profile.

    All fields are optional - only provided fields will be updated.

    Attributes:
        name: New display name
        age: User's age in years (16-100)
        weight: Current weight in kg (30-300)
        target_weight: Target weight in kg (30-300)
    """

    name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="User's display name"
    )
    age: Optional[int] = Field(
        None, ge=16, le=100, description="User's age in years"
    )
    weight: Optional[float] = Field(
        None, gt=30, le=300, description="Current weight in kg"
    )
    target_weight: Optional[float] = Field(
        None, gt=30, le=300, description="Target weight in kg"
    )
