"""Repository layer for training data access."""

import logging
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo import MongoClient
from pymongo.collection import Collection

from database.mongodb import (
    get_all_trainings as db_get_all_trainings,
    get_client,
    get_database,
    save_training_plan as db_save_training_plan,
    EXERCISE_COMPLETION_COLLECTION,
    get_training_days_collection,
    get_training_plans_collection,
)

logger = logging.getLogger(__name__)

TASKS_COLLECTION = "training_tasks"


class TrainingRepository:
    """Repository for training plan and task data operations."""

    def _get_tasks_collection(self, client: MongoClient) -> Collection:
        db = get_database(client)
        return db[TASKS_COLLECTION]

    def create_training_plan(
        self,
        plan_meta: dict[str, Any],
        days: list[dict[str, Any]],
        user_id: str | None = None,
    ) -> str:
        """Create training plan metadata and day records in v2 schema."""
        client = get_client()
        try:
            plans = get_training_plans_collection(client)
            training_days = get_training_days_collection(client)

            now = datetime.now(timezone.utc)
            plan_document = {
                "user_id": user_id,
                "difficulty": plan_meta.get("difficulty"),
                "created_at": now,
                "updated_at": now,
                "source_version": 2,
            }
            result = plans.insert_one(plan_document)
            plan_id = result.inserted_id

            if days:
                day_docs: list[dict[str, Any]] = []
                for day in days:
                    day_docs.append(
                        {
                            "plan_id": plan_id,
                            "user_id": user_id,
                            "day": day.get("day"),
                            "name": day.get("name"),
                            "time_required": day.get("timeRequired"),
                            "body_parts": day.get("bodyParts", []),
                            "exercises": day.get("exercises", []),
                            "created_at": now,
                            "updated_at": now,
                        }
                    )
                training_days.insert_many(day_docs)

            return str(plan_id)
        finally:
            client.close()

    def save_training_plan(
        self,
        plan_data: dict[str, Any],
        user_id: str | None = None,
    ) -> str:
        """Compatibility wrapper for existing controller flow."""
        return db_save_training_plan(plan_data, user_id=user_id)

    def get_training_plan(self, training_id: str, user_id: str | None = None) -> dict[str, Any] | None:
        """Get one full training plan by joining plan metadata with day documents."""
        client = get_client()
        try:
            plans = get_training_plans_collection(client)
            training_days = get_training_days_collection(client)

            try:
                object_id = ObjectId(training_id)
            except Exception:
                logger.warning(f"Invalid ObjectId format: {training_id}")
                return None

            query: dict[str, Any] = {"_id": object_id}
            if user_id:
                query["user_id"] = user_id

            plan = plans.find_one(query)
            if not plan:
                return None

            days_cursor = training_days.find(
                {"plan_id": object_id, **({"user_id": user_id} if user_id else {})},
                {
                    "_id": 0,
                    "day": 1,
                    "name": 1,
                    "time_required": 1,
                    "body_parts": 1,
                    "exercises": 1,
                },
            ).sort("day", 1)

            trainings = [
                {
                    "day": day.get("day"),
                    "name": day.get("name"),
                    "timeRequired": day.get("time_required"),
                    "bodyParts": day.get("body_parts", []),
                    "exercises": day.get("exercises", []),
                }
                for day in days_cursor
            ]

            return {
                "_id": str(plan["_id"]),
                "created_at": plan.get("created_at"),
                "difficulty": plan.get("difficulty"),
                "trainings": trainings,
            }
        finally:
            client.close()

    def get_training_by_id(self, training_id: str, user_id: str | None = None) -> dict[str, Any] | None:
        """Compatibility wrapper."""
        return self.get_training_plan(training_id, user_id=user_id)

    def list_training_plans(
        self,
        limit: int = 10,
        offset: int = 0,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """List training plans with aggregated training dates and day count."""
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
                    plan_id = str(day_doc["plan_id"])
                    grouped_days.setdefault(plan_id, []).append(day_doc.get("day"))

            trainings = []
            for plan_doc in plan_docs:
                plan_id = str(plan_doc["_id"])
                dates = sorted([date for date in grouped_days.get(plan_id, []) if date])
                trainings.append(
                    {
                        "id": plan_id,
                        "created_at": plan_doc.get("created_at"),
                        "difficulty": plan_doc.get("difficulty"),
                        "training_dates": dates,
                        "trainings_count": len(dates),
                    }
                )

            return {"total": total, "trainings": trainings}
        finally:
            client.close()

    def get_trainings_list(
        self,
        limit: int = 10,
        offset: int = 0,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Compatibility wrapper."""
        return db_get_all_trainings(limit=limit, offset=offset, user_id=user_id)

    def get_conflicts_for_dates(
        self,
        dates: list[str],
        user_id: str | None = None,
    ) -> list[dict[str, str]]:
        """Find conflicts by matching day dates in training_days."""
        if not dates:
            return []

        client = get_client()
        try:
            training_days = get_training_days_collection(client)

            query: dict[str, Any] = {"day": {"$in": dates}}
            if user_id:
                query["user_id"] = user_id

            cursor = training_days.find(query, {"_id": 1, "plan_id": 1, "day": 1, "name": 1, "trainings": 1})
            conflicts: list[dict[str, str]] = []
            for day_doc in cursor:
                # Compatibility path for legacy documents storing a `trainings` array.
                if isinstance(day_doc.get("trainings"), list):
                    for training in day_doc["trainings"]:
                        day = training.get("day")
                        if day not in dates:
                            continue
                        conflicts.append(
                            {
                                "date": day,
                                "existing_training_id": str(day_doc.get("_id")),
                                "existing_training_name": training.get("name", "Plan treningowy"),
                            }
                        )
                    continue

                conflicts.append(
                    {
                        "date": day_doc.get("day"),
                        "existing_training_id": str(day_doc.get("plan_id")),
                        "existing_training_name": day_doc.get("name", "Plan treningowy"),
                    }
                )
            return conflicts
        finally:
            client.close()

    def remove_conflicting_days(
        self,
        dates: list[str],
        user_id: str | None = None,
    ) -> int:
        """Remove conflicting day records and delete empty plans."""
        if not dates:
            return 0

        client = get_client()
        try:
            training_days = get_training_days_collection(client)
            plans = get_training_plans_collection(client)

            query: dict[str, Any] = {"day": {"$in": dates}}
            if user_id:
                query["user_id"] = user_id

            matched_docs = list(training_days.find(query, {"_id": 1, "plan_id": 1, "trainings": 1}))
            if matched_docs and any(isinstance(doc.get("trainings"), list) for doc in matched_docs):
                affected = 0
                for doc in matched_docs:
                    if not isinstance(doc.get("trainings"), list):
                        continue

                    remaining_trainings = [
                        training
                        for training in doc["trainings"]
                        if training.get("day") not in dates
                    ]
                    affected += 1

                    doc_query: dict[str, Any] = {"_id": doc["_id"]}
                    if user_id:
                        doc_query["user_id"] = user_id

                    if remaining_trainings:
                        training_days.update_one(doc_query, {"$set": {"trainings": remaining_trainings}})
                    else:
                        training_days.delete_one(doc_query)

                return affected

            affected_plan_ids = {str(doc.get("plan_id")) for doc in matched_docs if doc.get("plan_id")}
            if not affected_plan_ids:
                return 0

            training_days.delete_many(query)

            # Delete plans that no longer have any day records.
            for plan_id_str in affected_plan_ids:
                plan_id = ObjectId(plan_id_str)
                day_query: dict[str, Any] = {"plan_id": plan_id}
                if user_id:
                    day_query["user_id"] = user_id

                if training_days.count_documents(day_query) == 0:
                    plan_query: dict[str, Any] = {"_id": plan_id}
                    if user_id:
                        plan_query["user_id"] = user_id
                    plans.delete_one(plan_query)

            return len(affected_plan_ids)
        finally:
            client.close()

    def get_training_calendar_days(
        self,
        user_id: str | None = None,
    ) -> tuple[list[dict[str, str]], list[str]]:
        """Return calendar day entries deduplicated by date.

        If multiple records exist for a single date, first encountered entry is kept.
        """
        client = get_client()
        try:
            training_days = get_training_days_collection(client)

            query: dict[str, Any] = {}
            if user_id:
                query["user_id"] = user_id

            cursor = training_days.find(
                query,
                {"_id": 0, "day": 1, "plan_id": 1, "name": 1},
            ).sort("day", 1)

            days_by_date: dict[str, dict[str, str]] = {}
            counts_by_date: dict[str, int] = {}
            for day_doc in cursor:
                day = day_doc.get("day")
                if not day:
                    continue

                counts_by_date[day] = counts_by_date.get(day, 0) + 1
                if day not in days_by_date:
                    days_by_date[day] = {
                        "date": day,
                        "training_id": str(day_doc.get("plan_id")),
                        "training_name": day_doc.get("name", "Plan treningowy"),
                    }

            duplicate_dates = sorted([date for date, count in counts_by_date.items() if count > 1])
            days = [days_by_date[day] for day in sorted(days_by_date.keys())]
            return days, duplicate_dates
        finally:
            client.close()

    def get_recent_training_history(
        self,
        user_id: str,
        from_date: str,
        to_date: str,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """Return recent training day history in selected date window."""
        client = get_client()
        try:
            training_days = get_training_days_collection(client)
            cursor = (
                training_days.find(
                    {
                        "user_id": user_id,
                        "day": {"$gte": from_date, "$lte": to_date},
                    },
                    {
                        "_id": 0,
                        "plan_id": 1,
                        "day": 1,
                        "body_parts": 1,
                        "exercises": 1,
                    },
                )
                .sort("day", -1)
                .limit(limit)
            )
            history: list[dict[str, Any]] = []
            for item in cursor:
                exercises = item.get("exercises", []) or []
                history.append(
                    {
                        "plan_id": str(item.get("plan_id")),
                        "day": item.get("day"),
                        "body_parts": item.get("body_parts", []) or [],
                        "exercises_count": len(exercises),
                    }
                )
            return history
        finally:
            client.close()

    def get_training_days_for_window(
        self,
        *,
        user_id: str,
        from_date: str,
        to_date: str,
    ) -> list[dict[str, Any]]:
        """Return all training days in selected date window with exercise counts."""
        client = get_client()
        try:
            training_days = get_training_days_collection(client)
            cursor = training_days.find(
                {
                    "user_id": user_id,
                    "day": {"$gte": from_date, "$lte": to_date},
                },
                {
                    "_id": 0,
                    "plan_id": 1,
                    "day": 1,
                    "exercises": 1,
                },
            ).sort("day", 1)

            items: list[dict[str, Any]] = []
            for doc in cursor:
                exercises = doc.get("exercises", []) or []
                items.append(
                    {
                        "training_id": str(doc.get("plan_id")),
                        "day": str(doc.get("day")),
                        "exercises_count": len(exercises),
                    }
                )
            return items
        finally:
            client.close()

    def get_completion_summary_for_window(
        self,
        *,
        user_id: str,
        from_date: str,
        to_date: str,
    ) -> dict[str, dict[str, int]]:
        """Return completion stats keyed by '<training_id>|<day>' in selected date window."""
        client = get_client()
        try:
            db = get_database(client)
            completion = db[EXERCISE_COMPLETION_COLLECTION]
            cursor = completion.find(
                {
                    "user_id": user_id,
                    "day": {"$gte": from_date, "$lte": to_date},
                },
                {
                    "_id": 0,
                    "training_id": 1,
                    "day": 1,
                    "status": 1,
                },
            )

            summary: dict[str, dict[str, int]] = {}
            for doc in cursor:
                training_id = doc.get("training_id")
                day = doc.get("day")
                if not isinstance(training_id, str) or not isinstance(day, str):
                    continue

                key = f"{training_id}|{day}"
                if key not in summary:
                    summary[key] = {"completed": 0, "not_completed": 0}

                status = doc.get("status")
                if status == "not_completed":
                    summary[key]["not_completed"] += 1
                else:
                    # Backward compatibility: old records without status are treated as completed.
                    summary[key]["completed"] += 1
            return summary
        finally:
            client.close()

    def create_task(
        self,
        status: str = "pending",
        message: str = "Zadanie oczekuje na przetworzenie",
        user_id: str | None = None,
    ) -> str:
        """Create a new task record in MongoDB."""
        client = get_client()
        try:
            collection = self._get_tasks_collection(client)
            document = {
                "status": status,
                "message": message,
                "result": None,
                "error": None,
                "created_at": datetime.now(timezone.utc),
                "completed_at": None,
            }
            if user_id:
                document["user_id"] = user_id

            result = collection.insert_one(document)
            return str(result.inserted_id)
        finally:
            client.close()

    def update_task_status(
        self,
        task_id: str,
        status: str,
        message: str,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> bool:
        """Update the status of an existing task."""
        client = get_client()
        try:
            collection = self._get_tasks_collection(client)
            try:
                object_id = ObjectId(task_id)
            except Exception:
                logger.warning(f"Invalid task ID format: {task_id}")
                return False

            update_data: dict[str, Any] = {"status": status, "message": message}
            if result is not None:
                update_data["result"] = result
            if error is not None:
                update_data["error"] = error
            if status in ("completed", "failed"):
                update_data["completed_at"] = datetime.now(timezone.utc)

            update_result = collection.update_one({"_id": object_id}, {"$set": update_data})
            return update_result.modified_count > 0
        finally:
            client.close()

    def get_task(self, task_id: str, user_id: str | None = None) -> dict[str, Any] | None:
        """Retrieve a task by its ID."""
        client = get_client()
        try:
            collection = self._get_tasks_collection(client)
            try:
                object_id = ObjectId(task_id)
            except Exception:
                logger.warning(f"Invalid task ID format: {task_id}")
                return None

            query: dict[str, Any] = {"_id": object_id}
            if user_id:
                query["user_id"] = user_id

            doc = collection.find_one(query)
            if not doc:
                return None

            doc["_id"] = str(doc["_id"])
            return doc
        finally:
            client.close()

    def get_training_day(
        self,
        training_id: str,
        day: str,
        user_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Get one training day with related plan metadata."""
        client = get_client()
        try:
            plans = get_training_plans_collection(client)
            training_days = get_training_days_collection(client)

            try:
                object_id = ObjectId(training_id)
            except Exception:
                logger.warning(f"Invalid ObjectId format: {training_id}")
                return None

            plan_query: dict[str, Any] = {"_id": object_id}
            if user_id:
                plan_query["user_id"] = user_id

            plan = plans.find_one(plan_query, {"_id": 1, "difficulty": 1})
            if not plan:
                return None

            day_query: dict[str, Any] = {"plan_id": object_id, "day": day}
            if user_id:
                day_query["user_id"] = user_id

            day_doc = training_days.find_one(
                day_query,
                {
                    "_id": 0,
                    "day": 1,
                    "name": 1,
                    "time_required": 1,
                    "body_parts": 1,
                    "exercises": 1,
                },
            )
            if not day_doc:
                return None

            return {
                "training_id": training_id,
                "difficulty": plan.get("difficulty", "Intermediate"),
                "day": day_doc.get("day"),
                "name": day_doc.get("name"),
                "time_required": day_doc.get("time_required", 0),
                "body_parts": day_doc.get("body_parts", []),
                "exercises": day_doc.get("exercises", []),
            }
        finally:
            client.close()

    def replace_training_day_exercise(
        self,
        training_id: str,
        day: str,
        exercise_index: int,
        exercise: dict[str, Any],
        time_required: int,
        user_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Replace one exercise in training day and return update metadata."""
        client = get_client()
        try:
            training_days = get_training_days_collection(client)

            try:
                object_id = ObjectId(training_id)
            except Exception:
                logger.warning(f"Invalid ObjectId format: {training_id}")
                return None

            query: dict[str, Any] = {"plan_id": object_id, "day": day}
            if user_id:
                query["user_id"] = user_id

            day_doc = training_days.find_one(query, {"_id": 0, "exercises": 1})
            if not day_doc:
                return None

            exercises = list(day_doc.get("exercises", []))
            if exercise_index < 0 or exercise_index >= len(exercises):
                return None

            exercises[exercise_index] = exercise
            updated_at = datetime.now(timezone.utc)
            training_days.update_one(
                query,
                {
                    "$set": {
                        "exercises": exercises,
                        "time_required": time_required,
                        "updated_at": updated_at,
                    }
                },
            )

            return {
                "updated_at": updated_at,
                "time_required": time_required,
                "exercise": exercise,
            }
        finally:
            client.close()


_repository_instance: TrainingRepository | None = None


def get_training_repository() -> TrainingRepository:
    """Get the training repository singleton."""
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = TrainingRepository()
    return _repository_instance
