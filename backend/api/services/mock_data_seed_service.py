"""Service for seeding mock training and tracking data."""

from __future__ import annotations

import logging
import os
import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

from bson import ObjectId

from database.mongodb import get_client, get_database

logger = logging.getLogger(__name__)

USERS_COLLECTION = "users"
EXERCISES_COLLECTION = "exercises"
TRAINING_PLANS_COLLECTION = "training_plans"
TRAINING_DAYS_COLLECTION = "training_days"
EXERCISE_COMPLETION_COLLECTION = "exercise_completion"
EXERCISE_OPINION_COLLECTION = "exercise_opinion"
EXERCISE_OPINION_EVENTS_COLLECTION = "exercise_opinion_events"
EXERCISE_NOT_COMPLETED_EVENTS_COLLECTION = "exercise_not_completed_events"

DIFFICULTY_LEVELS = ["Novice", "Intermediate", "Advanced"]
NOT_COMPLETED_REASONS = [
    "brak_czasu",
    "zbyt_trudne",
    "bol_dyskomfort",
    "brak_sprzetu",
    "brak_motywacji",
    "inne",
]
BODY_PARTS_TEMPLATES = [
    ["Chest", "Triceps"],
    ["Back", "Biceps"],
    ["Quadriceps", "Hamstrings", "Glutes"],
    ["Deltoids", "Core"],
    ["Chest", "Back"],
    ["Glutes", "Core"],
]
TRAINING_NAMES = [
    "Klatka i Triceps",
    "Plecy i Biceps",
    "Nogi i Posladki",
    "Barki i Core",
    "Push Pull",
    "Mobilnosc i Core",
]


@dataclass
class MockSeedConfig:
    """Configuration for mock data generation."""

    plans_per_user: int = 4
    min_days_per_plan: int = 3
    max_days_per_plan: int = 4
    exercises_per_day: int = 4
    not_completed_rate: float = 0.2
    opinion_rate: float = 0.55
    start_days_ago: int = 45
    base_seed: int = 20260220

    @classmethod
    def from_env(cls) -> "MockSeedConfig":
        return cls(
            plans_per_user=int(os.getenv("AUTO_SEED_MOCK_PLANS_PER_USER", "4")),
            min_days_per_plan=int(os.getenv("AUTO_SEED_MOCK_MIN_DAYS_PER_PLAN", "3")),
            max_days_per_plan=int(os.getenv("AUTO_SEED_MOCK_MAX_DAYS_PER_PLAN", "4")),
            exercises_per_day=int(os.getenv("AUTO_SEED_MOCK_EXERCISES_PER_DAY", "4")),
            not_completed_rate=float(os.getenv("AUTO_SEED_MOCK_NOT_COMPLETED_RATE", "0.2")),
            opinion_rate=float(os.getenv("AUTO_SEED_MOCK_OPINION_RATE", "0.55")),
            start_days_ago=int(os.getenv("AUTO_SEED_MOCK_START_DAYS_AGO", "45")),
            base_seed=int(os.getenv("AUTO_SEED_MOCK_BASE_SEED", "20260220")),
        )


class MockDataSeedService:
    """Seed mock plans and tracking history for users."""

    def __init__(self, config: MockSeedConfig | None = None):
        self.config = config or MockSeedConfig.from_env()

    def is_auto_seed_enabled(self) -> bool:
        """Return whether automatic seeding is enabled for new users."""
        return os.getenv("AUTO_SEED_MOCK_DATA_ON_USER_CREATE", "false").lower() == "true"

    def seed_for_user(
        self,
        user_id: str,
        execute: bool = True,
        config: MockSeedConfig | None = None,
    ) -> dict[str, Any]:
        """Seed mock data for one user."""
        return self.seed_for_users(
            user_ids=[user_id],
            execute=execute,
            config=config,
        )

    def seed_for_all_users(
        self,
        execute: bool = True,
        config: MockSeedConfig | None = None,
    ) -> dict[str, Any]:
        """Seed mock data for all users."""
        return self.seed_for_users(
            user_ids=None,
            execute=execute,
            config=config,
        )

    def seed_for_users(
        self,
        user_ids: list[str] | None,
        execute: bool = True,
        config: MockSeedConfig | None = None,
    ) -> dict[str, Any]:
        """Seed mock data for selected users."""
        seed_config = config or self.config

        client = get_client()
        try:
            db = get_database(client)
            users = db[USERS_COLLECTION]

            user_docs = self._resolve_users(users, user_ids=user_ids)
            if not user_docs:
                return {
                    "execute": execute,
                    "users_total": 0,
                    "users_seeded": 0,
                    "plans_created": 0,
                    "days_created": 0,
                    "completion_created": 0,
                    "not_completed_events_created": 0,
                    "opinion_upserts": 0,
                    "opinion_events_created": 0,
                    "users": [],
                }

            exercises_pool = list(
                db[EXERCISES_COLLECTION].find(
                    {"id": {"$exists": True}},
                    {
                        "_id": 0,
                        "id": 1,
                        "name": 1,
                        "primary_muscles": 1,
                        "difficulty": 1,
                        "category": 1,
                        "videos": 1,
                        "steps": 1,
                    },
                )
            )
            if len(exercises_pool) < seed_config.exercises_per_day:
                raise RuntimeError(
                    f"Not enough exercises in database ({len(exercises_pool)}), "
                    f"need at least {seed_config.exercises_per_day}"
                )

            plans_col = db[TRAINING_PLANS_COLLECTION]
            days_col = db[TRAINING_DAYS_COLLECTION]
            completion_col = db[EXERCISE_COMPLETION_COLLECTION]
            not_completed_col = db[EXERCISE_NOT_COMPLETED_EVENTS_COLLECTION]
            opinion_col = db[EXERCISE_OPINION_COLLECTION]
            opinion_events_col = db[EXERCISE_OPINION_EVENTS_COLLECTION]

            summary: dict[str, Any] = {
                "execute": execute,
                "users_total": len(user_docs),
                "users_seeded": 0,
                "plans_created": 0,
                "days_created": 0,
                "completion_created": 0,
                "not_completed_events_created": 0,
                "opinion_upserts": 0,
                "opinion_events_created": 0,
                "users": [],
            }

            for user in user_docs:
                user_id = str(user["_id"])
                rng = random.Random(f"{seed_config.base_seed}-{user_id}")
                user_stats = self._seed_one_user(
                    user_id=user_id,
                    user_email=user.get("email"),
                    rng=rng,
                    exercises_pool=exercises_pool,
                    plans_col=plans_col,
                    days_col=days_col,
                    completion_col=completion_col,
                    not_completed_col=not_completed_col,
                    opinion_col=opinion_col,
                    opinion_events_col=opinion_events_col,
                    execute=execute,
                    config=seed_config,
                )
                summary["users_seeded"] += 1
                summary["users"].append(user_stats)
                for key in [
                    "plans_created",
                    "days_created",
                    "completion_created",
                    "not_completed_events_created",
                    "opinion_upserts",
                    "opinion_events_created",
                ]:
                    summary[key] += user_stats[key]

            return summary
        finally:
            client.close()

    def _resolve_users(self, users_collection: Any, user_ids: list[str] | None) -> list[dict[str, Any]]:
        if not user_ids:
            return list(users_collection.find({}, {"_id": 1, "email": 1}))

        resolved: list[dict[str, Any]] = []
        for user_id in user_ids:
            try:
                object_id = ObjectId(user_id)
            except Exception:
                logger.warning("Skipping invalid user_id for seed: %s", user_id)
                continue
            user = users_collection.find_one({"_id": object_id}, {"_id": 1, "email": 1})
            if user:
                resolved.append(user)
        return resolved

    def _seed_one_user(
        self,
        *,
        user_id: str,
        user_email: str | None,
        rng: random.Random,
        exercises_pool: list[dict[str, Any]],
        plans_col: Any,
        days_col: Any,
        completion_col: Any,
        not_completed_col: Any,
        opinion_col: Any,
        opinion_events_col: Any,
        execute: bool,
        config: MockSeedConfig,
    ) -> dict[str, Any]:
        today = date.today()
        start_date = today - timedelta(days=config.start_days_ago)
        now = datetime.now(timezone.utc)

        user_stats = {
            "user_id": user_id,
            "email": user_email,
            "plans_created": 0,
            "days_created": 0,
            "completion_created": 0,
            "not_completed_events_created": 0,
            "opinion_upserts": 0,
            "opinion_events_created": 0,
        }

        for plan_idx in range(config.plans_per_user):
            created_at = now - timedelta(days=max(0, config.start_days_ago - plan_idx * 3))
            plan_doc = {
                "user_id": user_id,
                "difficulty": rng.choice(DIFFICULTY_LEVELS),
                "created_at": created_at,
                "updated_at": now,
                "source_version": 2,
            }
            plan_id = plans_col.insert_one(plan_doc).inserted_id if execute else ObjectId()

            user_stats["plans_created"] += 1

            days_in_plan = rng.randint(config.min_days_per_plan, config.max_days_per_plan)
            for day_idx in range(days_in_plan):
                day_date = start_date + timedelta(days=plan_idx * 7 + day_idx * 2)
                repetitions = rng.choice(["3 x 12", "4 x 10", "5 x 8"])
                picked = rng.sample(exercises_pool, config.exercises_per_day)
                exercises = [self._build_exercise_payload(doc, repetitions) for doc in picked]

                day_doc = {
                    "plan_id": plan_id,
                    "user_id": user_id,
                    "day": day_date.isoformat(),
                    "name": TRAINING_NAMES[(plan_idx + day_idx) % len(TRAINING_NAMES)],
                    "time_required": rng.randint(45, 80),
                    "body_parts": BODY_PARTS_TEMPLATES[(plan_idx + day_idx) % len(BODY_PARTS_TEMPLATES)],
                    "exercises": exercises,
                    "created_at": created_at,
                    "updated_at": now,
                }
                if execute:
                    days_col.insert_one(day_doc)
                user_stats["days_created"] += 1

                for exercise_index, exercise in enumerate(exercises):
                    exercise_id = int(exercise["exercise_id"])
                    event_at = now - timedelta(days=rng.randint(1, max(2, config.start_days_ago)))
                    is_not_completed = rng.random() < config.not_completed_rate

                    completion_doc = {
                        "user_id": user_id,
                        "training_id": str(plan_id),
                        "day": day_date.isoformat(),
                        "exercise_index": exercise_index,
                        "exercise_id": exercise_id,
                        "status": "not_completed" if is_not_completed else "completed",
                        "reason_code": None,
                        "reason_text": "",
                        "updated_at": event_at,
                    }
                    if is_not_completed:
                        completion_doc["reason_code"] = rng.choice(NOT_COMPLETED_REASONS)
                        completion_doc["reason_text"] = "Mock seed: skipped exercise"
                    else:
                        completion_doc["completed_at"] = event_at

                    if execute:
                        completion_col.insert_one(completion_doc)
                    user_stats["completion_created"] += 1

                    if is_not_completed:
                        not_completed_doc = {
                            "user_id": user_id,
                            "exercise_id": exercise_id,
                            "reason_code": completion_doc["reason_code"],
                            "reason_text": completion_doc["reason_text"],
                            "created_at": event_at,
                        }
                        if execute:
                            not_completed_col.insert_one(not_completed_doc)
                        user_stats["not_completed_events_created"] += 1

                    if rng.random() < config.opinion_rate:
                        rating = rng.randint(2, 5)
                        opinion_text = rng.choice(
                            [
                                "Dobre cwiczenie, zostawiam.",
                                "Bylo ciezko, ale dalem rade.",
                                "Raczej ok, chce kontynuowac.",
                                "Wymaga poprawy techniki.",
                            ]
                        )
                        if execute:
                            opinion_col.update_one(
                                {"user_id": user_id, "exercise_id": exercise_id},
                                {
                                    "$set": {
                                        "rating": rating,
                                        "opinion": opinion_text,
                                        "updated_at": event_at,
                                    },
                                    "$setOnInsert": {
                                        "created_at": event_at,
                                    },
                                },
                                upsert=True,
                            )
                            opinion_events_col.insert_one(
                                {
                                    "user_id": user_id,
                                    "exercise_id": exercise_id,
                                    "rating": rating,
                                    "opinion": opinion_text,
                                    "created_at": event_at,
                                }
                            )
                        user_stats["opinion_upserts"] += 1
                        user_stats["opinion_events_created"] += 1

        return user_stats

    def _build_exercise_payload(self, exercise_doc: dict[str, Any], repetitions: str) -> dict[str, Any]:
        exercise_id = int(exercise_doc.get("id", 0))
        name = exercise_doc.get("name")
        return {
            "name": name if isinstance(name, str) and name else f"Exercise {exercise_id}",
            "exercise_id": exercise_id,
            "primary_muscles": exercise_doc.get("primary_muscles", []) or [],
            "difficulty": exercise_doc.get("difficulty"),
            "category": exercise_doc.get("category"),
            "videos": self._normalize_videos(exercise_doc.get("videos")),
            "repetitions": repetitions,
            "steps": exercise_doc.get("steps", []) or ["Kontroluj ruch", "Oddychaj regularnie"],
        }

    def _normalize_videos(self, videos: list[dict[str, Any]] | None) -> list[dict[str, str | None]]:
        normalized: list[dict[str, str | None]] = []
        for video in videos or []:
            if not isinstance(video, dict):
                continue
            url = video.get("url")
            if not isinstance(url, str) or not url:
                continue
            angle = video.get("angle")
            normalized.append(
                {
                    "url": url,
                    "angle": angle if isinstance(angle, str) else None,
                }
            )
        return normalized


_mock_seed_service_instance: MockDataSeedService | None = None


def get_mock_data_seed_service() -> MockDataSeedService:
    """Return singleton mock data seed service."""
    global _mock_seed_service_instance
    if _mock_seed_service_instance is None:
        _mock_seed_service_instance = MockDataSeedService()
    return _mock_seed_service_instance
