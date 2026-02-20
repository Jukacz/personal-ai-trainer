"""Repository for exercise completion and user opinion feedback data."""

import logging
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from database.mongodb import get_client, get_database

logger = logging.getLogger(__name__)

EXERCISE_OPINION_COLLECTION = "exercise_opinion"
EXERCISE_OPINION_EVENTS_COLLECTION = "exercise_opinion_events"
EXERCISE_COMPLETION_COLLECTION = "exercise_completion"
EXERCISE_NOT_COMPLETED_EVENTS_COLLECTION = "exercise_not_completed_events"


class ExerciseFeedbackRepository:
    """Data access layer for completions and exercise opinions."""

    def _get_collections(self):
        client = get_client()
        db = get_database(client)
        return (
            client,
            db[EXERCISE_OPINION_COLLECTION],
            db[EXERCISE_OPINION_EVENTS_COLLECTION],
            db[EXERCISE_COMPLETION_COLLECTION],
            db[EXERCISE_NOT_COMPLETED_EVENTS_COLLECTION],
        )

    def set_exercise_status(
        self,
        user_id: str,
        training_id: str,
        day: str,
        exercise_index: int,
        exercise_id: int,
        status: str,
        reason_code: str | None = None,
        reason_text: str | None = None,
    ) -> dict[str, Any] | None:
        """Persist one-way final status for a training exercise."""
        client, _, _, completion, _ = self._get_collections()
        try:
            now = datetime.now(timezone.utc)
            document = {
                "user_id": user_id,
                "training_id": training_id,
                "day": day,
                "exercise_index": exercise_index,
                "exercise_id": exercise_id,
                "status": status,
                "reason_code": reason_code,
                "reason_text": (reason_text or "").strip(),
                "updated_at": now,
            }
            if status == "completed":
                document["completed_at"] = now
            try:
                completion.insert_one(document)
            except DuplicateKeyError:
                return None
            return document
        finally:
            client.close()

    def complete_exercise(
        self,
        user_id: str,
        training_id: str,
        day: str,
        exercise_index: int,
        exercise_id: int,
    ) -> dict[str, Any] | None:
        """Persist backwards-compatible completed status for a training exercise."""
        return self.set_exercise_status(
            user_id=user_id,
            training_id=training_id,
            day=day,
            exercise_index=exercise_index,
            exercise_id=exercise_id,
            status="completed",
        )

    def get_status_snapshot_for_day(
        self,
        user_id: str,
        training_id: str,
        day: str,
    ) -> dict[int, dict[str, Any]]:
        """Return final status snapshot for selected day keyed by exercise_index."""
        client, _, _, completion, _ = self._get_collections()
        try:
            cursor = completion.find(
                {
                    "user_id": user_id,
                    "training_id": training_id,
                    "day": day,
                },
                {
                    "_id": 0,
                    "exercise_index": 1,
                    "exercise_id": 1,
                    "status": 1,
                    "reason_code": 1,
                    "reason_text": 1,
                    "updated_at": 1,
                    "completed_at": 1,
                },
            )
            snapshot: dict[int, dict[str, Any]] = {}
            for doc in cursor:
                exercise_index = doc.get("exercise_index")
                if not isinstance(exercise_index, int):
                    continue
                doc_status = doc.get("status")
                # Backward compatibility: old docs without status mean completed.
                normalized_status = doc_status if isinstance(doc_status, str) else "completed"
                snapshot[exercise_index] = {
                    "exercise_index": exercise_index,
                    "exercise_id": doc.get("exercise_id"),
                    "status": normalized_status,
                    "reason_code": doc.get("reason_code"),
                    "reason_text": doc.get("reason_text", ""),
                    "updated_at": doc.get("updated_at") or doc.get("completed_at"),
                }
            return snapshot
        finally:
            client.close()

    def get_completed_exercise_indices(
        self,
        user_id: str,
        training_id: str,
        day: str,
    ) -> list[int]:
        """Return sorted completed exercise indices for selected day."""
        snapshot = self.get_status_snapshot_for_day(
            user_id=user_id,
            training_id=training_id,
            day=day,
        )
        return sorted(
            index
            for index, item in snapshot.items()
            if item.get("status") == "completed"
        )

    def get_not_completed_snapshot_for_day(
        self,
        user_id: str,
        training_id: str,
        day: str,
    ) -> dict[int, dict[str, str]]:
        """Return not-completed reason map keyed by exercise_index."""
        snapshot = self.get_status_snapshot_for_day(
            user_id=user_id,
            training_id=training_id,
            day=day,
        )
        result: dict[int, dict[str, str]] = {}
        for index, item in snapshot.items():
            if item.get("status") != "not_completed":
                continue
            reason_code = item.get("reason_code")
            if not isinstance(reason_code, str):
                continue
            result[index] = {
                "reason_code": reason_code,
                "reason_text": str(item.get("reason_text") or ""),
            }
        return result

    def get_exercise_opinion(
        self,
        user_id: str,
        exercise_id: int,
    ) -> dict[str, Any] | None:
        """Get latest snapshot opinion for one exercise."""
        client, opinion, _, _, _ = self._get_collections()
        try:
            doc = opinion.find_one(
                {"user_id": user_id, "exercise_id": exercise_id},
                {
                    "_id": 0,
                    "exercise_id": 1,
                    "rating": 1,
                    "opinion": 1,
                    "created_at": 1,
                    "updated_at": 1,
                },
            )
            return doc
        finally:
            client.close()

    def get_exercise_opinions_bulk(
        self,
        user_id: str,
        exercise_ids: list[int],
    ) -> dict[int, dict[str, Any]]:
        """Get snapshot opinions for multiple exercises keyed by exercise_id."""
        if not exercise_ids:
            return {}

        client, opinion, _, _, _ = self._get_collections()
        try:
            cursor = opinion.find(
                {
                    "user_id": user_id,
                    "exercise_id": {"$in": exercise_ids},
                },
                {
                    "_id": 0,
                    "exercise_id": 1,
                    "rating": 1,
                    "opinion": 1,
                    "created_at": 1,
                    "updated_at": 1,
                },
            )
            return {
                int(doc["exercise_id"]): doc
                for doc in cursor
                if isinstance(doc.get("exercise_id"), int)
            }
        finally:
            client.close()

    def upsert_exercise_opinion(
        self,
        user_id: str,
        exercise_id: int,
        rating: int,
        opinion_text: str,
    ) -> dict[str, Any]:
        """Upsert user opinion snapshot for exercise."""
        client, opinion, _, _, _ = self._get_collections()
        try:
            now = datetime.now(timezone.utc)
            opinion.update_one(
                {"user_id": user_id, "exercise_id": exercise_id},
                {
                    "$set": {
                        "rating": rating,
                        "opinion": opinion_text,
                        "updated_at": now,
                    },
                    "$setOnInsert": {
                        "created_at": now,
                    },
                },
                upsert=True,
            )

            updated = opinion.find_one(
                {"user_id": user_id, "exercise_id": exercise_id},
                {
                    "_id": 0,
                    "exercise_id": 1,
                    "rating": 1,
                    "opinion": 1,
                    "created_at": 1,
                    "updated_at": 1,
                },
            )
            if not updated:
                raise RuntimeError("Failed to upsert exercise opinion")
            return updated
        finally:
            client.close()

    def append_exercise_opinion_event(
        self,
        user_id: str,
        exercise_id: int,
        rating: int,
        opinion_text: str,
    ) -> None:
        """Append immutable opinion event for historical scoring."""
        client, _, opinion_events, _, _ = self._get_collections()
        try:
            opinion_events.insert_one(
                {
                    "user_id": user_id,
                    "exercise_id": exercise_id,
                    "rating": rating,
                    "opinion": opinion_text,
                    "created_at": datetime.now(timezone.utc),
                }
            )
        finally:
            client.close()

    def get_user_opinion_events(
        self,
        user_id: str,
        limit: int = 5000,
    ) -> list[dict[str, Any]]:
        """Return recent opinion events for user, sorted by created_at desc."""
        client, _, opinion_events, _, _ = self._get_collections()
        try:
            cursor = opinion_events.find(
                {"user_id": user_id},
                {
                    "_id": 0,
                    "exercise_id": 1,
                    "rating": 1,
                    "opinion": 1,
                    "created_at": 1,
                },
            ).sort("created_at", -1).limit(limit)
            return list(cursor)
        finally:
            client.close()

    def append_not_completed_event(
        self,
        user_id: str,
        exercise_id: int,
        reason_code: str,
        reason_text: str,
    ) -> None:
        """Append immutable not-completed event for historical scoring."""
        client, _, _, _, not_completed_events = self._get_collections()
        try:
            not_completed_events.insert_one(
                {
                    "user_id": user_id,
                    "exercise_id": exercise_id,
                    "reason_code": reason_code,
                    "reason_text": reason_text,
                    "created_at": datetime.now(timezone.utc),
                }
            )
        finally:
            client.close()

    def get_user_not_completed_events(
        self,
        user_id: str,
        limit: int = 5000,
    ) -> list[dict[str, Any]]:
        """Return recent not-completed events for user, sorted by created_at desc."""
        client, _, _, _, not_completed_events = self._get_collections()
        try:
            cursor = not_completed_events.find(
                {"user_id": user_id},
                {
                    "_id": 0,
                    "exercise_id": 1,
                    "reason_code": 1,
                    "reason_text": 1,
                    "created_at": 1,
                },
            ).sort("created_at", -1).limit(limit)
            return list(cursor)
        finally:
            client.close()

    def get_training_day_exercise_id(
        self,
        training_id: str,
        day: str,
        exercise_index: int,
        user_id: str,
    ) -> int | None:
        """Resolve exercise_id from selected plan day and index."""
        client = get_client()
        try:
            db = get_database(client)
            training_days = db["training_days"]

            try:
                plan_object_id = ObjectId(training_id)
            except Exception:
                logger.warning("Invalid training ObjectId in completion lookup: %s", training_id)
                return None

            day_doc = training_days.find_one(
                {
                    "plan_id": plan_object_id,
                    "day": day,
                    "user_id": user_id,
                },
                {"_id": 0, "exercises": 1},
            )
            if not day_doc:
                return None

            exercises = day_doc.get("exercises", [])
            if exercise_index < 0 or exercise_index >= len(exercises):
                return None

            value = exercises[exercise_index].get("exercise_id")
            if not isinstance(value, int):
                return None
            return value
        finally:
            client.close()


_repository_instance: ExerciseFeedbackRepository | None = None


def get_exercise_feedback_repository() -> ExerciseFeedbackRepository:
    """Get singleton instance of exercise feedback repository."""
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = ExerciseFeedbackRepository()
    return _repository_instance
