"""Service layer for training plan generation.

Orchestrates the AI agents to generate complete training plans.
"""

import json
import logging
import os
import random
import re
from collections import defaultdict
from datetime import date, timedelta
from datetime import datetime, timezone
from math import exp, log
from typing import Any
from zoneinfo import ZoneInfo

from langchain_google_genai import ChatGoogleGenerativeAI

from agents.planner_agent import create_planner_agent
from agents.exercise_agent import create_exercise_agent
from agents.exercise_replace_agent import create_exercise_replace_agent
from api.exceptions.handlers import (
    ExerciseStatusAlreadyFinalizedError,
    ExerciseTrackingNotAllowedError,
    InvalidExerciseReplaceError,
    TrainingGenerationError,
    TrainingNotFoundError,
)
from api.repositories.exercise_feedback_repository import (
    ExerciseFeedbackRepository,
    get_exercise_feedback_repository,
)
from prompts.templates import create_quick_body_parts_prompt
from tools.musclewiki import fetch_exercise_details_by_id, fetch_exercises_list

logger = logging.getLogger(__name__)

DAY_ORDER = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}
WEEKDAY_ORDER = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
WEEKDAY_LABELS_PL = {
    "monday": "Pon",
    "tuesday": "Wt",
    "wednesday": "Śr",
    "thursday": "Czw",
    "friday": "Pt",
    "saturday": "Sob",
    "sunday": "Ndz",
}

WEEKDAY_BY_NAME = {name: index for name, index in DAY_ORDER.items()}
REPETITIONS_BY_DIFFICULTY = {
    "Novice": "3 x 12",
    "Intermediate": "4 x 10",
    "Advanced": "5 x 8",
}
NOT_COMPLETED_REASON_PENALTIES = {
    "brak_czasu": -0.35,
    "zbyt_trudne": -0.60,
    "bol_dyskomfort": -0.75,
    "brak_sprzetu": -0.40,
    "brak_motywacji": -0.45,
    "inne": -0.30,
}


class TrainingService:
    """Service for generating training plans using AI agents.

    Coordinates the planner and exercise agents to create
    complete weekly training plans with exercises.
    """

    def __init__(self, feedback_repository: ExerciseFeedbackRepository | None = None):
        """Initialize the training service."""
        self.feedback_repository = feedback_repository or get_exercise_feedback_repository()

    def is_trackable_today(self, day: str, tz_name: str = "Europe/Warsaw") -> bool:
        """Check if selected day equals today's date in configured timezone."""
        if os.getenv("ALLOW_TRACKING_ANY_DAY", "false").lower() == "true":
            return True
        today = datetime.now(ZoneInfo(tz_name)).date().isoformat()
        return day == today

    def get_dashboard_stats(
        self,
        *,
        user_id: str,
        window_days: int,
        training_repository: Any,
    ) -> dict[str, Any]:
        """Compute dashboard analytics for selected time window."""
        safe_window_days = max(1, window_days)
        end_day = date.today()
        start_day = end_day - timedelta(days=safe_window_days - 1)
        start_iso = start_day.isoformat()
        end_iso = end_day.isoformat()

        day_entries = training_repository.get_training_days_for_window(
            user_id=user_id,
            from_date=start_iso,
            to_date=end_iso,
        )
        completion_summary = training_repository.get_completion_summary_for_window(
            user_id=user_id,
            from_date=start_iso,
            to_date=end_iso,
        )

        trend_counts: dict[str, int] = defaultdict(int)
        weekday_counts: dict[str, int] = {weekday: 0 for weekday in WEEKDAY_ORDER}

        completed_total = 0
        not_completed_total = 0
        pending_total = 0

        for entry in day_entries:
            day_iso = entry.get("day")
            training_id = entry.get("training_id")
            exercises_count = int(entry.get("exercises_count", 0))
            if not isinstance(day_iso, str) or not isinstance(training_id, str):
                continue

            trend_counts[day_iso] += 1

            try:
                weekday_key = WEEKDAY_ORDER[datetime.fromisoformat(day_iso).weekday()]
                weekday_counts[weekday_key] += 1
            except ValueError:
                logger.warning("[Service] Invalid day format in dashboard stats: %s", day_iso)

            key = f"{training_id}|{day_iso}"
            summary = completion_summary.get(key, {"completed": 0, "not_completed": 0})
            completed = max(0, int(summary.get("completed", 0)))
            not_completed = max(0, int(summary.get("not_completed", 0)))

            if completed > exercises_count:
                completed = exercises_count
            remaining = max(0, exercises_count - completed)
            if not_completed > remaining:
                not_completed = remaining
            pending = max(0, exercises_count - completed - not_completed)

            completed_total += completed
            not_completed_total += not_completed
            pending_total += pending

        trend = []
        for i in range(safe_window_days):
            day_iso = (start_day + timedelta(days=i)).isoformat()
            trend.append({"date": day_iso, "count": trend_counts.get(day_iso, 0)})

        weekday_distribution = [
            {"weekday": WEEKDAY_LABELS_PL[weekday], "count": weekday_counts[weekday]}
            for weekday in WEEKDAY_ORDER
        ]

        total_exercises = completed_total + not_completed_total + pending_total
        completed_percent = round((completed_total / total_exercises) * 100) if total_exercises > 0 else 0

        most_active_weekday = "Brak danych"
        if day_entries:
            most_active_weekday = max(
                weekday_distribution,
                key=lambda item: item["count"],
                default={"weekday": "Brak danych", "count": 0},
            )["weekday"]
            if all(item["count"] == 0 for item in weekday_distribution):
                most_active_weekday = "Brak danych"

        return {
            "kpis": {
                "scheduled_trainings": len(day_entries),
                "completed_exercises_percent": completed_percent,
                "not_completed_exercises": not_completed_total,
                "most_active_weekday": most_active_weekday,
            },
            "training_trend": trend,
            "status_distribution": [
                {"status": "completed", "value": completed_total},
                {"status": "not_completed", "value": not_completed_total},
                {"status": "pending", "value": pending_total},
            ],
            "weekday_distribution": weekday_distribution,
        }

    def complete_exercise_for_day(
        self,
        *,
        training_id: str,
        day: str,
        exercise_index: int,
        user_id: str,
        training_repository: Any,
    ) -> dict[str, Any]:
        """Persist one-way exercise completion for selected day."""
        if not self.is_trackable_today(day):
            raise ExerciseTrackingNotAllowedError(
                "Exercise tracking is available only for today's training date"
            )

        training_day = training_repository.get_training_day(
            training_id=training_id,
            day=day,
            user_id=user_id,
        )
        if not training_day:
            raise TrainingNotFoundError(training_id)

        exercises = training_day.get("exercises", [])
        if exercise_index < 0 or exercise_index >= len(exercises):
            raise InvalidExerciseReplaceError("exercise_index is out of range for selected day")

        exercise_id = exercises[exercise_index].get("exercise_id")
        if not isinstance(exercise_id, int):
            raise InvalidExerciseReplaceError("Selected exercise does not contain numeric exercise_id")

        completion = self.feedback_repository.set_exercise_status(
            user_id=user_id,
            training_id=training_id,
            day=day,
            exercise_index=exercise_index,
            exercise_id=exercise_id,
            status="completed",
        )
        if not completion:
            raise ExerciseStatusAlreadyFinalizedError(
                "Exercise status has already been finalized for this exercise"
            )

        existing_opinion = self.feedback_repository.get_exercise_opinion(
            user_id=user_id,
            exercise_id=exercise_id,
        )
        return {
            "training_id": training_id,
            "day": day,
            "exercise_index": exercise_index,
            "exercise_id": exercise_id,
            "status": "completed",
            "reason_code": None,
            "reason_text": None,
            "updated_at": completion["updated_at"],
            "completed_at": completion["completed_at"],
            "existing_opinion": existing_opinion,
        }

    def mark_exercise_not_completed_for_day(
        self,
        *,
        training_id: str,
        day: str,
        exercise_index: int,
        reason_code: str,
        reason_text: str | None,
        user_id: str,
        training_repository: Any,
    ) -> dict[str, Any]:
        """Persist one-way exercise not-completed status for selected day."""
        if not self.is_trackable_today(day):
            raise ExerciseTrackingNotAllowedError(
                "Exercise tracking is available only for today's training date"
            )

        training_day = training_repository.get_training_day(
            training_id=training_id,
            day=day,
            user_id=user_id,
        )
        if not training_day:
            raise TrainingNotFoundError(training_id)

        exercises = training_day.get("exercises", [])
        if exercise_index < 0 or exercise_index >= len(exercises):
            raise InvalidExerciseReplaceError("exercise_index is out of range for selected day")

        exercise_id = exercises[exercise_index].get("exercise_id")
        if not isinstance(exercise_id, int):
            raise InvalidExerciseReplaceError("Selected exercise does not contain numeric exercise_id")

        normalized_reason_text = (reason_text or "").strip()
        completion = self.feedback_repository.set_exercise_status(
            user_id=user_id,
            training_id=training_id,
            day=day,
            exercise_index=exercise_index,
            exercise_id=exercise_id,
            status="not_completed",
            reason_code=reason_code,
            reason_text=normalized_reason_text,
        )
        if not completion:
            raise ExerciseStatusAlreadyFinalizedError(
                "Exercise status has already been finalized for this exercise"
            )

        self.feedback_repository.append_not_completed_event(
            user_id=user_id,
            exercise_id=exercise_id,
            reason_code=reason_code,
            reason_text=normalized_reason_text,
        )

        return {
            "training_id": training_id,
            "day": day,
            "exercise_index": exercise_index,
            "exercise_id": exercise_id,
            "status": "not_completed",
            "reason_code": reason_code,
            "reason_text": normalized_reason_text,
            "updated_at": completion["updated_at"],
            "completed_at": None,
            "existing_opinion": None,
        }

    def get_progress_for_day(
        self,
        *,
        training_id: str,
        day: str,
        user_id: str,
        training_repository: Any,
    ) -> dict[str, Any]:
        """Get progress state for selected day with opinion prefill map."""
        training_day = training_repository.get_training_day(
            training_id=training_id,
            day=day,
            user_id=user_id,
        )
        if not training_day:
            raise TrainingNotFoundError(training_id)

        status_snapshot = self.feedback_repository.get_status_snapshot_for_day(
            user_id=user_id,
            training_id=training_id,
            day=day,
        )
        completed_exercise_indices = sorted(
            index for index, item in status_snapshot.items() if item.get("status") == "completed"
        )
        not_completed_exercise_indices = sorted(
            index for index, item in status_snapshot.items() if item.get("status") == "not_completed"
        )
        not_completed_reasons_by_exercise_index = {
            str(index): {
                "reason_code": str(item.get("reason_code") or "inne"),
                "reason_text": str(item.get("reason_text") or ""),
            }
            for index, item in status_snapshot.items()
            if item.get("status") == "not_completed"
        }
        exercise_ids = [
            exercise.get("exercise_id")
            for exercise in training_day.get("exercises", [])
            if isinstance(exercise.get("exercise_id"), int)
        ]
        opinions = self.feedback_repository.get_exercise_opinions_bulk(
            user_id=user_id,
            exercise_ids=exercise_ids,
        )

        return {
            "day": day,
            "is_trackable_today": self.is_trackable_today(day),
            "completed_exercise_indices": completed_exercise_indices,
            "not_completed_exercise_indices": not_completed_exercise_indices,
            "not_completed_reasons_by_exercise_index": not_completed_reasons_by_exercise_index,
            "opinions_by_exercise_id": {
                str(exercise_id): opinion
                for exercise_id, opinion in opinions.items()
            },
        }

    def upsert_exercise_opinion(
        self,
        *,
        user_id: str,
        exercise_id: int,
        rating: int,
        opinion: str | None,
    ) -> dict[str, Any]:
        """Upsert opinion snapshot and append immutable event."""
        normalized_opinion = (opinion or "").strip()
        snapshot = self.feedback_repository.upsert_exercise_opinion(
            user_id=user_id,
            exercise_id=exercise_id,
            rating=rating,
            opinion_text=normalized_opinion,
        )
        self.feedback_repository.append_exercise_opinion_event(
            user_id=user_id,
            exercise_id=exercise_id,
            rating=rating,
            opinion_text=normalized_opinion,
        )
        return snapshot

    def get_exercise_opinion(
        self,
        *,
        user_id: str,
        exercise_id: int,
    ) -> dict[str, Any] | None:
        """Get snapshot opinion for selected exercise."""
        return self.feedback_repository.get_exercise_opinion(
            user_id=user_id,
            exercise_id=exercise_id,
        )

    def _decay_weight(
        self,
        *,
        days_old: float,
        half_life_days: float = 45.0,
    ) -> float:
        """Return exponential decay weight for given event age."""
        decay_lambda = log(2) / half_life_days
        return exp(-decay_lambda * max(0.0, days_old))

    def _event_days_old(self, created_at: datetime, now: datetime) -> float:
        """Return event age in days for decay calculation."""
        normalized_created_at = created_at
        if normalized_created_at.tzinfo is None:
            normalized_created_at = normalized_created_at.replace(tzinfo=timezone.utc)
        return max(0.0, (now - normalized_created_at).total_seconds() / 86400.0)

    def compute_rating_component(
        self,
        events: list[dict[str, Any]],
        half_life_days: float = 45.0,
    ) -> float:
        """Compute rating-based preference component with decay."""
        now = datetime.now(timezone.utc)
        score = 0.0

        for event in events:
            rating = event.get("rating")
            created_at = event.get("created_at")
            if not isinstance(rating, int) or not isinstance(created_at, datetime):
                continue
            days_old = self._event_days_old(created_at=created_at, now=now)
            rating_norm = (rating - 3) / 2
            weight = self._decay_weight(days_old=days_old, half_life_days=half_life_days)
            score += rating_norm * weight

        return score

    def compute_not_completed_penalty_component(
        self,
        events: list[dict[str, Any]],
        half_life_days: float = 45.0,
    ) -> float:
        """Compute not-completed penalty component with decay."""
        now = datetime.now(timezone.utc)
        score = 0.0
        for event in events:
            reason_code = event.get("reason_code")
            created_at = event.get("created_at")
            if not isinstance(reason_code, str) or not isinstance(created_at, datetime):
                continue
            penalty = NOT_COMPLETED_REASON_PENALTIES.get(reason_code, NOT_COMPLETED_REASON_PENALTIES["inne"])
            days_old = self._event_days_old(created_at=created_at, now=now)
            weight = self._decay_weight(days_old=days_old, half_life_days=half_life_days)
            score += penalty * weight
        return score

    def compute_preference_score(
        self,
        opinion_events: list[dict[str, Any]],
        not_completed_events: list[dict[str, Any]],
        half_life_days: float = 45.0,
    ) -> float:
        """Compute combined preference score from ratings and not-completed penalties."""
        return self.compute_rating_component(
            opinion_events,
            half_life_days=half_life_days,
        ) + self.compute_not_completed_penalty_component(
            not_completed_events,
            half_life_days=half_life_days,
        )

    def get_user_preference_scores(self, user_id: str | None) -> dict[int, float]:
        """Return decayed preference score map for user."""
        if not user_id:
            return {}

        opinion_events = self.feedback_repository.get_user_opinion_events(user_id=user_id)
        grouped_opinions: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for event in opinion_events:
            exercise_id = event.get("exercise_id")
            if isinstance(exercise_id, int):
                grouped_opinions[exercise_id].append(event)

        not_completed_events = self.feedback_repository.get_user_not_completed_events(user_id=user_id)
        grouped_not_completed: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for event in not_completed_events:
            exercise_id = event.get("exercise_id")
            if isinstance(exercise_id, int):
                grouped_not_completed[exercise_id].append(event)

        all_exercise_ids = set(grouped_opinions.keys()) | set(grouped_not_completed.keys())
        return {
            exercise_id: self.compute_preference_score(
                grouped_opinions.get(exercise_id, []),
                grouped_not_completed.get(exercise_id, []),
            )
            for exercise_id in all_exercise_ids
        }

    def _build_preference_context_block(self, user_id: str | None) -> str:
        """Build textual soft-preference block for plan generation prompt."""
        scores = self.get_user_preference_scores(user_id=user_id)
        if not scores:
            return "Preferencje uzytkownika: brak historii opinii. Dobieraj cwiczenia standardowo.\n"

        preferred = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        avoid = sorted(scores.items(), key=lambda item: item[1])
        preferred_ids = [str(item[0]) for item in preferred[:8] if item[1] > 0]
        avoid_ids = [str(item[0]) for item in avoid[:8] if item[1] < 0]
        strongly_penalized_ids = [str(item[0]) for item in avoid[:8] if item[1] <= -0.35]

        return (
            "KONTEKST PREFERENCJI (soft, nie twardy filtr):\n"
            f"- Preferred exercises (exercise_id): {', '.join(preferred_ids) if preferred_ids else 'brak'}\n"
            f"- Avoid if possible (exercise_id): {', '.join(avoid_ids) if avoid_ids else 'brak'}\n"
            f"- Often not completed (avoid if possible): {', '.join(strongly_penalized_ids) if strongly_penalized_ids else 'brak'}\n"
            "- Traktuj te preferencje jako wskazowki, nie bezwzgledne ograniczenia.\n"
        )

    def _normalize_selected_days(self, selected_days: list[str] | None) -> list[str]:
        """Normalize selected days to deterministic week order."""
        if not selected_days:
            selected_days = ["monday", "thursday", "saturday"]

        return sorted(selected_days, key=lambda day: DAY_ORDER[day])

    def get_default_planning_range(self) -> tuple[str, str]:
        """Return next full week range (next Monday to Sunday) in ISO format."""
        today = date.today()
        days_until_next_monday = (7 - today.weekday()) % 7
        if days_until_next_monday == 0:
            days_until_next_monday = 7
        next_monday = today + timedelta(days=days_until_next_monday)
        next_sunday = next_monday + timedelta(days=6)
        return next_monday.isoformat(), next_sunday.isoformat()

    def get_training_dates_in_range(
        self,
        *,
        start_date: str,
        end_date: str,
        selected_days: list[str] | None,
        trainings_per_week: int,
    ) -> list[str]:
        """Calculate planned training dates in selected range and weekday preferences."""
        normalized_selected_days = self._normalize_selected_days(selected_days)
        start_dt = date.fromisoformat(start_date)
        end_dt = date.fromisoformat(end_date)
        if start_dt > end_dt:
            return []

        dates_by_week: dict[tuple[int, int], list[str]] = defaultdict(list)
        current = start_dt
        allowed_weekdays = {WEEKDAY_BY_NAME[day] for day in normalized_selected_days}

        while current <= end_dt:
            if current.weekday() in allowed_weekdays:
                week_key = current.isocalendar()[:2]
                dates_by_week[week_key].append(current.isoformat())
            current += timedelta(days=1)

        selected_dates: list[str] = []
        for week_key in sorted(dates_by_week.keys()):
            week_dates = sorted(dates_by_week[week_key])
            selected_dates.extend(week_dates[:trainings_per_week])
        return selected_dates

    def get_quick_training_date(self, tz_name: str = "Europe/Warsaw") -> str:
        """Return today's date in configured timezone."""
        return datetime.now(ZoneInfo(tz_name)).date().isoformat()

    def get_upcoming_training_dates(self, selected_days: list[str] | None) -> list[str]:
        """Compatibility helper for legacy one-week conflict checks."""
        start_date, end_date = self.get_default_planning_range()
        return self.get_training_dates_in_range(
            start_date=start_date,
            end_date=end_date,
            selected_days=selected_days,
            trainings_per_week=len(self._normalize_selected_days(selected_days)),
        )

    def _get_difficulty_instruction(self, difficulty: str) -> str:
        """Get difficulty-specific instructions for exercise selection.

        Args:
            difficulty: Training difficulty level

        Returns:
            Polish language instructions for the exercise agent
        """
        instructions = {
            "Novice": (
                "Wybieraj prostsze cwiczenia, skupione na poprawnej technice. "
                "Unikaj zlozononych ruchow wielostawowych na poczatek."
            ),
            "Intermediate": (
                "Wybieraj zrownowazony zestaw cwiczen - zarowno podstawowe jak i bardziej zaawansowane. "
                "Mozesz uzywac cwiczen wielostawowych."
            ),
            "Advanced": (
                "Wybieraj intensywne cwiczenia, w tym zlozzone ruchy wielostawowe. "
                "Skup sie na cwiczeniach wymagajacych wiekszej sily i koordynacji."
            ),
        }
        return instructions.get(difficulty, instructions["Intermediate"])

    def _extract_json_from_response(self, response: str) -> dict[str, Any]:
        """Extract JSON from agent response.

        The exercise agent may wrap JSON in markdown code blocks.
        This method handles various response formats.

        Args:
            response: Raw response string from the agent

        Returns:
            Parsed JSON as dictionary

        Raises:
            TrainingGenerationError: If JSON cannot be extracted
        """
        # Try to find JSON in code block first
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response)

        if json_match:
            json_str = json_match.group(1).strip()
        else:
            # Try to find raw JSON object
            json_match = re.search(r'(\{[\s\S]*\})', response)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                logger.error(f"No JSON found in response: {response[:500]}")
                raise TrainingGenerationError(
                    "Failed to extract plan from agent response",
                    {"response_preview": response[:200]}
                )

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}, content: {json_str[:500]}")
            raise TrainingGenerationError(
                "Invalid JSON format in agent response",
                {"parse_error": str(e)}
            )

    def _build_suggestion_item(self, details: dict[str, Any]) -> dict[str, Any]:
        difficulty_label = details.get("difficulty") or "Intermediate"
        repetitions = REPETITIONS_BY_DIFFICULTY.get(difficulty_label, "4 x 10")
        videos = details.get("videos", []) or []
        normalized_videos = []
        for video in videos:
            url = video.get("url")
            if not url:
                continue
            normalized_videos.append(
                {
                    "url": url,
                    "angle": video.get("angle"),
                }
            )

        return {
            "exercise_id": int(details.get("id", 0)),
            "name": details.get("name", ""),
            "primary_muscles": details.get("primary_muscles", []) or [],
            "difficulty": details.get("difficulty"),
            "category": details.get("category"),
            "videos": normalized_videos,
            "repetitions": repetitions,
            "steps": details.get("steps", []) or [],
        }

    def _build_training_exercise(
        self,
        details: dict[str, Any],
        difficulty: str = "Intermediate",
    ) -> dict[str, Any]:
        videos = details.get("videos", []) or []
        normalized_videos = []
        for video in videos:
            url = video.get("url")
            if not url:
                continue
            normalized_videos.append(
                {
                    "url": url,
                    "angle": video.get("angle"),
                }
            )

        return {
            "name": details.get("name", ""),
            "exercise_id": int(details.get("id", 0)),
            "primary_muscles": details.get("primary_muscles", []) or [],
            "difficulty": details.get("difficulty"),
            "category": details.get("category"),
            "videos": normalized_videos,
            "repetitions": REPETITIONS_BY_DIFFICULTY.get(difficulty, "4 x 10"),
            "steps": details.get("steps", []) or [],
        }

    def _manual_candidates(
        self,
        muscles: list[str],
        query: str | None,
        limit: int,
        current_exercise_id: int | None,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        payload = fetch_exercises_list(
            muscles=muscles if muscles else None,
            search=query,
            limit=max(limit * 2, 20),
            offset=max(0, offset),
            gender="male",
        )
        results = payload.get("results", []) or []
        selected_ids: list[int] = []

        for item in results:
            exercise_id = item.get("id")
            if not isinstance(exercise_id, int):
                continue
            if current_exercise_id is not None and exercise_id == current_exercise_id:
                continue
            if exercise_id in selected_ids:
                continue
            selected_ids.append(exercise_id)
            if len(selected_ids) >= limit:
                break

        suggestions: list[dict[str, Any]] = []
        for exercise_id in selected_ids:
            details = fetch_exercise_details_by_id(exercise_id)
            suggestions.append(self._build_suggestion_item(details))
        return suggestions

    def suggest_exercise_replacements(
        self,
        current_exercise: dict[str, Any],
        body_parts: list[str] | None,
        mode: str,
        query: str | None,
        limit: int,
        refresh_seed: int | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Suggest replacement exercises for one selected exercise."""
        current_exercise_id = current_exercise.get("exercise_id")
        if not isinstance(current_exercise_id, int):
            current_exercise_id = None

        primary_muscles = current_exercise.get("primary_muscles")
        normalized_primary = primary_muscles if isinstance(primary_muscles, list) else []
        normalized_body_parts = body_parts if isinstance(body_parts, list) else []

        context_source = "exercise_primary_muscles"
        muscles = [m for m in normalized_primary if isinstance(m, str) and m]
        if not muscles:
            muscles = [m for m in normalized_body_parts if isinstance(m, str) and m]
            context_source = "training_day_body_parts"

        fallback_used = False
        suggestions: list[dict[str, Any]] = []
        if muscles:
            candidate_offset = (refresh_seed or 0) % 200
            try:
                suggestions = self._manual_candidates(
                    muscles=muscles,
                    query=query,
                    limit=limit,
                    current_exercise_id=current_exercise_id,
                    offset=candidate_offset,
                )
            except Exception:
                logger.exception("Manual candidate lookup failed, falling back to random_top")
                suggestions = []

        if not suggestions:
            context_source = "random_top"
            fallback_used = True
            random_offset = (
                (refresh_seed % 300) if refresh_seed is not None else random.randint(0, 200)
            )
            try:
                payload = fetch_exercises_list(
                    muscles=None,
                    search=query,
                    limit=max(limit * 2, 20),
                    offset=random_offset,
                    gender="male",
                )
            except Exception:
                logger.exception("Random fallback candidate lookup failed")
                payload = {"results": []}
            candidate_ids: list[int] = []
            for item in payload.get("results", []) or []:
                exercise_id = item.get("id")
                if not isinstance(exercise_id, int):
                    continue
                if current_exercise_id is not None and exercise_id == current_exercise_id:
                    continue
                if exercise_id in candidate_ids:
                    continue
                candidate_ids.append(exercise_id)
                if len(candidate_ids) >= limit:
                    break
            suggestions = [
                self._build_suggestion_item(fetch_exercise_details_by_id(exercise_id))
                for exercise_id in candidate_ids
            ]

        preference_scores = self.get_user_preference_scores(user_id=user_id)
        for suggestion in suggestions:
            exercise_id = suggestion.get("exercise_id")
            if not isinstance(exercise_id, int):
                suggestion["user_preference_score"] = 0.0
                continue
            suggestion["user_preference_score"] = preference_scores.get(exercise_id, 0.0)
        suggestions = sorted(
            suggestions,
            key=lambda item: float(item.get("user_preference_score", 0.0)),
            reverse=True,
        )

        if mode == "manual":
            return {
                "mode": "manual",
                "context_source": context_source,
                "fallback_used": fallback_used,
                "suggestions": suggestions[:limit],
            }

        ai_fallback_used = fallback_used
        ranked = suggestions[: max(limit, 10)]
        deterministic = ranked[:3]
        if ranked:
            try:
                run_agent = create_exercise_replace_agent()
                response_ids = run_agent(
                    {
                        "current_exercise": current_exercise,
                        "body_parts": normalized_body_parts,
                        "candidates": ranked,
                    }
                )
                allowed_ids = {item["exercise_id"] for item in ranked}
                picked: list[int] = []
                for exercise_id in response_ids:
                    if exercise_id not in allowed_ids:
                        continue
                    if exercise_id in picked:
                        continue
                    picked.append(exercise_id)
                    if len(picked) >= 3:
                        break

                if len(picked) == 3 or (len(ranked) < 3 and len(picked) == len(ranked)):
                    ranked_by_id = {item["exercise_id"]: item for item in ranked}
                    deterministic = [ranked_by_id[item_id] for item_id in picked]
                else:
                    ai_fallback_used = True
            except Exception:
                logger.exception("Exercise replacement AI failed, using deterministic fallback")
                ai_fallback_used = True

        return {
            "mode": "ai",
            "context_source": context_source,
            "fallback_used": ai_fallback_used,
            "suggestions": deterministic,
        }

    def build_replacement_exercise(
        self,
        replacement_exercise_id: int,
        difficulty: str,
    ) -> dict[str, Any]:
        """Build normalized exercise payload from MuscleWiki details."""
        details = fetch_exercise_details_by_id(replacement_exercise_id)
        return self._build_training_exercise(details, difficulty=difficulty)

    def _resolve_body_parts_by_weekday(
        self,
        *,
        age: int,
        weight: float,
        target_weight: float,
        difficulty: str,
        selected_days: list[str],
    ) -> dict[str, list[str]]:
        """Generate one-week body-part schedule and map it by weekday name."""
        try:
            planner = create_planner_agent(
                age=age,
                weight=weight,
                target_weight=target_weight,
                difficulty=difficulty,
                selected_days=selected_days,
            )
            week_plan = planner.invoke({})
        except Exception as exc:
            logger.exception("[Service] Planner agent failed")
            raise TrainingGenerationError(
                "Failed to generate weekly plan",
                {"step": "planner", "error": str(exc)},
            )

        mapping: dict[str, list[str]] = {}
        for training in week_plan.trainings:
            try:
                weekday_name = date.fromisoformat(training.day).strftime("%A").lower()
            except Exception:
                weekday_name = ""
            if weekday_name in WEEKDAY_BY_NAME:
                mapping[weekday_name] = list(training.bodyParts)

        # Fallback for missing weekdays from planner response.
        fallback_parts = [
            ["Chest", "Triceps"],
            ["Back", "Biceps"],
            ["Quadriceps", "Hamstrings"],
            ["Deltoids", "Core"],
            ["Glutes", "Core"],
            ["Chest", "Back"],
        ]
        for idx, weekday in enumerate(selected_days):
            mapping.setdefault(weekday, fallback_parts[idx % len(fallback_parts)])
        return mapping

    def _generate_training_day_with_exercises(
        self,
        *,
        day_iso: str,
        body_parts: list[str],
        difficulty: str,
        run_exercise_agent: Any,
        user_id: str | None,
    ) -> dict[str, Any]:
        """Generate one training day payload with exercises."""
        body_parts_str = ", ".join(body_parts)
        difficulty_instruction = self._get_difficulty_instruction(difficulty)
        prompt = (
            f"Wygeneruj plan treningowy na dzien {day_iso}.\n"
            f"Partie ciala do cwiczen: {body_parts_str}.\n"
            f"Poziom trudnosci: {difficulty}.\n"
            f"{difficulty_instruction}\n"
            f"{self._build_preference_context_block(user_id)}"
            f"Dla kazdej partii ciala wybierz 2 cwiczenia.\n"
            f"WAZNE: Przy wywolaniu get_exercises() uzyj parametru difficulty=\"{difficulty.lower()}\" "
            f"aby filtrowac cwiczenia po poziomie trudnosci.\n\n"
            f"Zwroc odpowiedz w formacie JSON:\n"
            f'{{"day": "{day_iso}", "name": "Nazwa treningu po polsku", '
            f'"timeRequired": <liczba_minut>, "exercises": [...]}}'
        )
        response = run_exercise_agent(prompt)
        day_plan = self._extract_json_from_response(response)
        day_plan["day"] = day_iso
        day_plan["bodyParts"] = body_parts
        return day_plan

    def _choose_quick_body_parts_with_ai(
        self,
        *,
        difficulty: str,
        history: list[dict[str, Any]],
        today_iso: str,
    ) -> list[str]:
        """Select body parts for quick training using AI and recent history context."""
        if not history:
            history_summary = "- Brak historii treningów użytkownika."
        else:
            lines = []
            for item in history[:30]:
                lines.append(
                    f"- {item.get('day')}: body_parts={item.get('body_parts', [])}, "
                    f"exercises_count={item.get('exercises_count', 0)}"
                )
            history_summary = "\n".join(lines)

        prompt = create_quick_body_parts_prompt(
            difficulty=difficulty,
            history_summary=history_summary,
            today_date=today_iso,
        )

        try:
            llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.4)
            message = llm.invoke(prompt.format_messages())
            payload = self._extract_json_from_response(str(message.content))
            body_parts = payload.get("body_parts", [])
            if isinstance(body_parts, list):
                normalized = [item for item in body_parts if isinstance(item, str) and item.strip()]
                if normalized:
                    return normalized[:3]
        except Exception:
            logger.exception("Quick body-parts AI selection failed, using fallback")

        return ["Chest", "Back", "Core"]

    def generate_training_plan(
        self,
        age: int = 19,
        weight: float = 102.0,
        target_weight: float = 80.0,
        difficulty: str = "Intermediate",
        selected_days: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        trainings_per_week: int | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Generate a complete training plan.

        Orchestrates the planner and exercise agents:
        1. Planner agent creates a weekly schedule with body parts
        2. Exercise agent fills in exercises for each training day
        3. Results are combined into a final plan

        Args:
            age: Client age
            weight: Current weight in kg
            target_weight: Target weight in kg
            difficulty: Training difficulty level (Novice, Intermediate, Advanced)
            selected_days: Selected days of week (monday-sunday)

        Returns:
            Complete training plan dictionary

        Raises:
            TrainingGenerationError: If plan generation fails
        """
        normalized_selected_days = self._normalize_selected_days(selected_days)
        effective_trainings_per_week = trainings_per_week or len(normalized_selected_days)
        if start_date is None or end_date is None:
            start_date, end_date = self.get_default_planning_range()

        target_dates = self.get_training_dates_in_range(
            start_date=start_date,
            end_date=end_date,
            selected_days=normalized_selected_days,
            trainings_per_week=effective_trainings_per_week,
        )
        if not target_dates:
            raise TrainingGenerationError(
                "No training dates matched selected range and weekday preferences",
                {
                    "start_date": start_date,
                    "end_date": end_date,
                    "selected_days": normalized_selected_days,
                    "trainings_per_week": effective_trainings_per_week,
                },
            )

        logger.info(
            f"[Service] Starting training plan generation: "
            f"age={age}, weight={weight}, target={target_weight}, "
            f"difficulty={difficulty}, selected_days={normalized_selected_days}, "
            f"range={start_date}:{end_date}, trainings_per_week={effective_trainings_per_week}"
        )

        body_parts_by_weekday = self._resolve_body_parts_by_weekday(
            age=age,
            weight=weight,
            target_weight=target_weight,
            difficulty=difficulty,
            selected_days=normalized_selected_days,
        )

        # Step 2: Create exercise agent
        try:
            logger.info("[Service] Creating exercise agent...")
            run_exercise_agent = create_exercise_agent()
        except Exception as e:
            logger.exception("[Service] Exercise agent creation failed")
            raise TrainingGenerationError(
                "Failed to create exercise agent",
                {"step": "exercise_agent_init", "error": str(e)}
            )

        # Step 3: Fill exercises for each training day
        training_days = []
        for idx, training_date in enumerate(target_dates):
            weekday_name = date.fromisoformat(training_date).strftime("%A").lower()
            body_parts = body_parts_by_weekday.get(weekday_name, ["Chest", "Back"])
            logger.info(
                f"[Service] Processing training {idx + 1}/{len(target_dates)}: "
                f"day={training_date}, bodyParts={body_parts}"
            )

            try:
                logger.info(f"[Service] Invoking exercise agent for day {training_date}...")
                day_plan = self._generate_training_day_with_exercises(
                    day_iso=training_date,
                    body_parts=body_parts,
                    difficulty=difficulty,
                    run_exercise_agent=run_exercise_agent,
                    user_id=user_id,
                )
                training_days.append(day_plan)

                logger.info(
                    f"[Service] Day {training_date} complete: "
                    f"{len(day_plan.get('exercises', []))} exercises"
                )

            except TrainingGenerationError:
                raise
            except Exception as e:
                logger.exception(f"[Service] Exercise agent failed for day {training_date}")
                raise TrainingGenerationError(
                    f"Failed to generate exercises for day {training_date}",
                    {"step": "exercise_agent", "day": training_date, "error": str(e)}
                )

        # Step 4: Combine into final plan
        final_plan = {
            "trainings": training_days,
            "difficulty": difficulty
        }

        logger.info(
            f"[Service] Training plan complete: "
            f"{len(training_days)} days generated, difficulty={difficulty}"
        )

        return final_plan

    def generate_quick_training_for_today(
        self,
        *,
        difficulty: str = "Intermediate",
        user_id: str,
        training_repository: Any,
    ) -> dict[str, Any]:
        """Generate one-day quick training for today's date."""
        today_iso = self.get_quick_training_date()
        history_from = (date.fromisoformat(today_iso) - timedelta(days=60)).isoformat()
        history = training_repository.get_recent_training_history(
            user_id=user_id,
            from_date=history_from,
            to_date=today_iso,
        )
        body_parts = self._choose_quick_body_parts_with_ai(
            difficulty=difficulty,
            history=history,
            today_iso=today_iso,
        )

        try:
            run_exercise_agent = create_exercise_agent()
            day_plan = self._generate_training_day_with_exercises(
                day_iso=today_iso,
                body_parts=body_parts,
                difficulty=difficulty,
                run_exercise_agent=run_exercise_agent,
                user_id=user_id,
            )
        except Exception as exc:
            logger.exception("[Service] Quick training generation failed")
            raise TrainingGenerationError(
                "Failed to generate quick training",
                {"step": "quick_training", "error": str(exc)},
            )

        return {
            "trainings": [day_plan],
            "difficulty": difficulty,
        }


# Singleton instance for dependency injection
_service_instance: TrainingService | None = None


def get_training_service() -> TrainingService:
    """Get the training service singleton.

    Returns:
        TrainingService instance
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = TrainingService()
    return _service_instance
