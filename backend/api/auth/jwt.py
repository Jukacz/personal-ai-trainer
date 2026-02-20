"""JWT token management for authentication.

Provides functions for creating and verifying access and refresh tokens.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from pydantic import BaseModel

# JWT Configuration from environment variables
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


class TokenData(BaseModel):
    """Data extracted from a verified JWT token.

    Attributes:
        user_id: The user's unique identifier
        email: The user's email address
        type: Token type ('access' or 'refresh')
    """

    user_id: str
    email: str
    type: str


def create_access_token(user_id: str, email: str) -> str:
    """Create a new access token for a user.

    Args:
        user_id: The user's unique identifier
        email: The user's email address

    Returns:
        Encoded JWT access token string
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "email": email,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str, email: str) -> str:
    """Create a new refresh token for a user.

    Args:
        user_id: The user's unique identifier
        email: The user's email address

    Returns:
        Encoded JWT refresh token string
    """
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "email": email,
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_token(token: str, expected_type: str) -> Optional[TokenData]:
    """Verify a JWT token and extract its data.

    Args:
        token: The JWT token string to verify
        expected_type: Expected token type ('access' or 'refresh')

    Returns:
        TokenData if token is valid and matches expected type, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        token_type: str = payload.get("type")

        if user_id is None or email is None or token_type is None:
            return None

        if token_type != expected_type:
            return None

        return TokenData(user_id=user_id, email=email, type=token_type)

    except JWTError:
        return None
