"""User domain models for the AI Personal Trainer API.

Contains Pydantic models for user data and profiles.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserProfile(BaseModel):
    """User profile with fitness-related information.

    Attributes:
        age: User's age in years (16-100)
        weight: Current weight in kg (30-300)
        target_weight: Target weight in kg (30-300)
    """

    age: Optional[int] = Field(None, ge=16, le=100, description="User's age in years")
    weight: Optional[float] = Field(None, gt=30, le=300, description="Current weight in kg")
    target_weight: Optional[float] = Field(
        None, gt=30, le=300, description="Target weight in kg"
    )


class User(BaseModel):
    """User domain model.

    Attributes:
        id: Unique user identifier
        email: User's email address
        name: User's display name
        profile: User's fitness profile
        created_at: Account creation timestamp
        updated_at: Last update timestamp
    """

    id: str
    email: EmailStr
    name: str
    profile: UserProfile
    created_at: datetime
    updated_at: datetime
