"""MongoDB database operations for training plans."""

import logging
import os
from datetime import datetime, timezone
from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

logger = logging.getLogger(__name__)

DATABASE_NAME = "personal_trainer"
LEGACY_TRAININGS_COLLECTION = "trainings"
TRAINING_PLANS_COLLECTION = "training_plans"
TRAINING_DAYS_COLLECTION = "training_days"
EXERCISES_COLLECTION = "exercises"
EXERCISE_OPINION_COLLECTION = "exercise_opinion"
EXERCISE_OPINION_EVENTS_COLLECTION = "exercise_opinion_events"
EXERCISE_COMPLETION_COLLECTION = "exercise_completion"
EXERCISE_NOT_COMPLETED_EVENTS_COLLECTION = "exercise_not_completed_events"


def get_client() -> MongoClient:
    """Create and return a MongoDB client.

    Returns:
        MongoClient instance connected to the database.
    """
    uri = os.getenv(
        "MONGODB_URI",
        "mongodb://admin:password123@localhost:27017/?authSource=admin",
    )
    logger.debug(f"[MongoDB] Connecting to: {uri[:30]}...")
    return MongoClient(uri)


def get_database(client: MongoClient) -> Database:
    """Get the personal_trainer database.

    Args:
        client: MongoClient instance

    Returns:
        Database instance
    """
    return client[DATABASE_NAME]


def get_legacy_trainings_collection(client: MongoClient) -> Collection:
    """Get the legacy trainings collection.

    Args:
        client: MongoClient instance

    Returns:
        Collection instance
    """
    db = get_database(client)
    return db[LEGACY_TRAININGS_COLLECTION]


def get_training_plans_collection(client: MongoClient) -> Collection:
    """Get the training_plans collection."""
    db = get_database(client)
    return db[TRAINING_PLANS_COLLECTION]


def get_training_days_collection(client: MongoClient) -> Collection:
    """Get the training_days collection."""
    db = get_database(client)
    return db[TRAINING_DAYS_COLLECTION]


def get_exercises_collection(client: MongoClient) -> Collection:
    """Get the exercises collection.

    Args:
        client: MongoClient instance

    Returns:
        Collection instance
    """
    db = get_database(client)
    return db[EXERCISES_COLLECTION]


def ensure_training_indexes() -> None:
    """Ensure indexes for v2 training collections."""
    client = get_client()
    try:
        plans = get_training_plans_collection(client)
        days = get_training_days_collection(client)
        tasks = get_database(client)["training_tasks"]
        exercise_opinion = get_database(client)[EXERCISE_OPINION_COLLECTION]
        exercise_opinion_events = get_database(client)[EXERCISE_OPINION_EVENTS_COLLECTION]
        exercise_completion = get_database(client)[EXERCISE_COMPLETION_COLLECTION]
        exercise_not_completed_events = get_database(client)[EXERCISE_NOT_COMPLETED_EVENTS_COLLECTION]

        plans.create_index([("user_id", 1), ("created_at", -1)])
        plans.create_index([("created_at", -1)])
        plans.create_index([("legacy_training_id", 1)], sparse=True)

        days.create_index([("plan_id", 1), ("day", 1)])
        days.create_index([("user_id", 1), ("day", 1)])
        days.create_index([("user_id", 1), ("plan_id", 1)])

        tasks.create_index([("user_id", 1), ("created_at", -1)])
        tasks.create_index([("result.training_id", 1)])
        exercise_opinion.create_index([("user_id", 1), ("exercise_id", 1)], unique=True)
        exercise_opinion.create_index([("user_id", 1), ("updated_at", -1)])
        exercise_opinion_events.create_index([("user_id", 1), ("exercise_id", 1), ("created_at", -1)])
        exercise_completion.create_index(
            [("user_id", 1), ("training_id", 1), ("day", 1), ("exercise_index", 1)],
            unique=True,
        )
        exercise_completion.create_index([("user_id", 1), ("day", 1)])
        exercise_not_completed_events.create_index(
            [("user_id", 1), ("exercise_id", 1), ("created_at", -1)]
        )
    finally:
        client.close()


def save_training_plan(
    plan_data: dict[str, Any],
    user_id: str | None = None,
) -> str:
    """Backward-compatible helper to save a full training plan."""
    client = get_client()
    try:
        plans = get_training_plans_collection(client)
        training_days = get_training_days_collection(client)
        now = datetime.now(timezone.utc)

        plan_doc = {
            "user_id": user_id,
            "difficulty": plan_data.get("difficulty"),
            "created_at": now,
            "updated_at": now,
            "source_version": 2,
        }
        plan_id = plans.insert_one(plan_doc).inserted_id

        day_docs = []
        for training_day in plan_data.get("trainings", []):
            day_docs.append(
                {
                    "plan_id": plan_id,
                    "user_id": user_id,
                    "day": training_day.get("day"),
                    "name": training_day.get("name"),
                    "time_required": training_day.get("timeRequired"),
                    "body_parts": training_day.get("bodyParts", []),
                    "exercises": training_day.get("exercises", []),
                    "created_at": now,
                    "updated_at": now,
                }
            )

        if day_docs:
            training_days.insert_many(day_docs)

        return str(plan_id)
    finally:
        client.close()


def get_all_trainings(
    limit: int = 10,
    offset: int = 0,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Backward-compatible helper returning paginated plan summaries."""
    client = get_client()
    try:
        plans = get_training_plans_collection(client)
        training_days = get_training_days_collection(client)

        query: dict[str, Any] = {}
        if user_id:
            query["user_id"] = user_id

        total = plans.count_documents(query)
        plan_docs = list(
            plans.find(query, {"_id": 1, "created_at": 1, "difficulty": 1})
            .sort("created_at", -1)
            .skip(offset)
            .limit(limit)
        )

        plan_ids = [doc["_id"] for doc in plan_docs]
        grouped_days: dict[str, list[str]] = {}
        if plan_ids:
            day_cursor = training_days.find(
                {"plan_id": {"$in": plan_ids}, **({"user_id": user_id} if user_id else {})},
                {"_id": 0, "plan_id": 1, "day": 1},
            )
            for day_doc in day_cursor:
                grouped_days.setdefault(str(day_doc["plan_id"]), []).append(day_doc.get("day"))

        items = []
        for doc in plan_docs:
            dates = sorted([d for d in grouped_days.get(str(doc["_id"]), []) if d])
            items.append(
                {
                    "id": str(doc["_id"]),
                    "created_at": doc.get("created_at"),
                    "difficulty": doc.get("difficulty"),
                    "training_dates": dates,
                    "trainings_count": len(dates),
                }
            )

        return {"total": total, "trainings": items}
    finally:
        client.close()


# --- Exercise functions for local database ---


def get_exercise(exercise_id: int) -> dict[str, Any] | None:
    """Retrieve exercise from local database.

    Args:
        exercise_id: MuscleWiki API exercise ID

    Returns:
        Dict with exercise data or None if not found.
    """
    client = get_client()

    try:
        collection = get_exercises_collection(client)
        doc = collection.find_one({"exerciseId": exercise_id})

        if doc:
            doc["_id"] = str(doc["_id"])
            logger.info(f"[DB] Found exercise {exercise_id} in local database")
            return doc

        return None

    finally:
        client.close()


def save_exercise(exercise_id: int, data: dict[str, Any]) -> str:
    """Save exercise to local database.

    Uses upsert to update if exists or insert if not.

    Args:
        exercise_id: MuscleWiki API exercise ID
        data: Exercise data from API response

    Returns:
        String ID of the saved document.
    """
    client = get_client()

    try:
        collection = get_exercises_collection(client)

        document = {
            "exerciseId": exercise_id,
            **data,
            "savedAt": datetime.now(timezone.utc),
        }

        result = collection.update_one(
            {"exerciseId": exercise_id},
            {"$set": document},
            upsert=True,
        )

        logger.info(f"[DB] Saved exercise {exercise_id} to local database")
        return str(result.upserted_id or exercise_id)

    finally:
        client.close()
