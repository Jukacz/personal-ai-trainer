"""Repository layer for user data access.

Provides methods for CRUD operations on user documents in MongoDB.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from bson import ObjectId

from database.mongodb import get_client, get_database

logger = logging.getLogger(__name__)

USERS_COLLECTION = "users"


class UserRepository:
    """Repository for user data operations.

    Provides methods for creating, retrieving, and updating user documents
    in MongoDB.
    """

    def __init__(self):
        """Initialize repository without a persistent connection.

        Connections are created per-operation to ensure thread safety
        with FastAPI's async nature.
        """
        pass

    def create(
        self,
        email: str,
        password_hash: str,
        name: str,
        google_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create a new user in the database.

        Args:
            email: User's email address
            password_hash: Hashed password
            name: User's display name
            google_id: Optional Google OAuth ID

        Returns:
            Created user document with _id as string
        """
        client = get_client()

        try:
            db = get_database(client)
            collection = db[USERS_COLLECTION]

            now = datetime.now(timezone.utc)
            document = {
                "email": email.lower(),
                "password_hash": password_hash,
                "name": name,
                "google_id": google_id,
                "profile": {
                    "age": None,
                    "weight": None,
                    "target_weight": None,
                },
                "created_at": now,
                "updated_at": now,
            }

            result = collection.insert_one(document)
            document["_id"] = str(result.inserted_id)

            logger.info(f"[UserRepository] Created user: {document['_id']}")
            return document

        finally:
            client.close()

    def get_by_id(self, user_id: str) -> Optional[dict[str, Any]]:
        """Retrieve a user by their ID.

        Args:
            user_id: The MongoDB ObjectId as string

        Returns:
            User document or None if not found
        """
        client = get_client()

        try:
            db = get_database(client)
            collection = db[USERS_COLLECTION]

            try:
                object_id = ObjectId(user_id)
            except Exception:
                logger.warning(f"[UserRepository] Invalid ObjectId format: {user_id}")
                return None

            doc = collection.find_one({"_id": object_id})

            if doc:
                doc["_id"] = str(doc["_id"])
                logger.debug(f"[UserRepository] Retrieved user: {user_id}")
                return doc

            logger.debug(f"[UserRepository] User not found: {user_id}")
            return None

        finally:
            client.close()

    def get_by_email(self, email: str) -> Optional[dict[str, Any]]:
        """Retrieve a user by their email address.

        Args:
            email: User's email address

        Returns:
            User document or None if not found
        """
        client = get_client()

        try:
            db = get_database(client)
            collection = db[USERS_COLLECTION]

            doc = collection.find_one({"email": email.lower()})

            if doc:
                doc["_id"] = str(doc["_id"])
                logger.debug(f"[UserRepository] Found user by email: {email}")
                return doc

            logger.debug(f"[UserRepository] User not found by email: {email}")
            return None

        finally:
            client.close()

    def get_by_google_id(self, google_id: str) -> Optional[dict[str, Any]]:
        """Retrieve a user by their Google OAuth ID.

        Args:
            google_id: Google OAuth user ID

        Returns:
            User document or None if not found
        """
        client = get_client()

        try:
            db = get_database(client)
            collection = db[USERS_COLLECTION]

            doc = collection.find_one({"google_id": google_id})

            if doc:
                doc["_id"] = str(doc["_id"])
                logger.debug(f"[UserRepository] Found user by google_id: {google_id}")
                return doc

            logger.debug(f"[UserRepository] User not found by google_id: {google_id}")
            return None

        finally:
            client.close()

    def update(
        self, user_id: str, data: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """Update a user's data.

        Args:
            user_id: The user's ID
            data: Dictionary of fields to update

        Returns:
            Updated user document or None if not found
        """
        client = get_client()

        try:
            db = get_database(client)
            collection = db[USERS_COLLECTION]

            try:
                object_id = ObjectId(user_id)
            except Exception:
                logger.warning(f"[UserRepository] Invalid ObjectId format: {user_id}")
                return None

            # Add updated_at timestamp
            data["updated_at"] = datetime.now(timezone.utc)

            result = collection.find_one_and_update(
                {"_id": object_id},
                {"$set": data},
                return_document=True,
            )

            if result:
                result["_id"] = str(result["_id"])
                logger.info(f"[UserRepository] Updated user: {user_id}")
                return result

            logger.warning(f"[UserRepository] User not found for update: {user_id}")
            return None

        finally:
            client.close()

    def link_google(self, user_id: str, google_id: str) -> bool:
        """Link a Google OAuth ID to an existing user.

        Args:
            user_id: The user's ID
            google_id: Google OAuth user ID to link

        Returns:
            True if update was successful, False otherwise
        """
        client = get_client()

        try:
            db = get_database(client)
            collection = db[USERS_COLLECTION]

            try:
                object_id = ObjectId(user_id)
            except Exception:
                logger.warning(f"[UserRepository] Invalid ObjectId format: {user_id}")
                return False

            result = collection.update_one(
                {"_id": object_id},
                {
                    "$set": {
                        "google_id": google_id,
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )

            success = result.modified_count > 0
            if success:
                logger.info(
                    f"[UserRepository] Linked Google ID to user: {user_id}"
                )
            else:
                logger.warning(
                    f"[UserRepository] Failed to link Google ID to user: {user_id}"
                )

            return success

        finally:
            client.close()


# Singleton instance for dependency injection
_repository_instance: Optional[UserRepository] = None


def get_user_repository() -> UserRepository:
    """Get the user repository singleton.

    Returns:
        UserRepository instance
    """
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = UserRepository()
    return _repository_instance
