"""Tests for exercise tracking statuses and preference penalties."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from api.exceptions.handlers import ExerciseStatusAlreadyFinalizedError
from api.services.training_service import TrainingService


class TestTrainingTrackingService:
    """Tests for completed/not_completed tracking flow."""

    def test_mark_exercise_not_completed_for_day_success(self):
        feedback_repo = MagicMock()
        service = TrainingService(feedback_repository=feedback_repo)
        service.is_trackable_today = MagicMock(return_value=True)
        training_repository = MagicMock()

        training_repository.get_training_day.return_value = {
            "exercises": [{"exercise_id": 123}, {"exercise_id": 456}],
        }
        feedback_repo.set_exercise_status.return_value = {
            "updated_at": datetime.now(timezone.utc),
        }

        payload = service.mark_exercise_not_completed_for_day(
            training_id="plan_1",
            day="2026-02-20",
            exercise_index=1,
            reason_code="brak_czasu",
            reason_text="Spotkania",
            user_id="user_1",
            training_repository=training_repository,
        )

        assert payload["status"] == "not_completed"
        assert payload["exercise_id"] == 456
        assert payload["reason_code"] == "brak_czasu"
        feedback_repo.append_not_completed_event.assert_called_once()

    def test_mark_exercise_not_completed_conflict_raises_409_error(self):
        feedback_repo = MagicMock()
        service = TrainingService(feedback_repository=feedback_repo)
        service.is_trackable_today = MagicMock(return_value=True)
        training_repository = MagicMock()

        training_repository.get_training_day.return_value = {
            "exercises": [{"exercise_id": 123}],
        }
        feedback_repo.set_exercise_status.return_value = None

        with pytest.raises(ExerciseStatusAlreadyFinalizedError):
            service.mark_exercise_not_completed_for_day(
                training_id="plan_1",
                day="2026-02-20",
                exercise_index=0,
                reason_code="brak_czasu",
                reason_text="",
                user_id="user_1",
                training_repository=training_repository,
            )

    def test_get_progress_for_day_returns_not_completed_reason_map(self):
        feedback_repo = MagicMock()
        service = TrainingService(feedback_repository=feedback_repo)
        training_repository = MagicMock()

        training_repository.get_training_day.return_value = {
            "exercises": [{"exercise_id": 100}, {"exercise_id": 200}],
        }
        feedback_repo.get_status_snapshot_for_day.return_value = {
            0: {"status": "completed"},
            1: {"status": "not_completed", "reason_code": "zbyt_trudne", "reason_text": "Za ciężkie"},
        }
        feedback_repo.get_exercise_opinions_bulk.return_value = {}

        payload = service.get_progress_for_day(
            training_id="plan_1",
            day="2026-02-20",
            user_id="user_1",
            training_repository=training_repository,
        )

        assert payload["completed_exercise_indices"] == [0]
        assert payload["not_completed_exercise_indices"] == [1]
        assert payload["not_completed_reasons_by_exercise_index"]["1"]["reason_code"] == "zbyt_trudne"


class TestPreferenceScorePenalty:
    """Tests for combined preference scoring."""

    def test_not_completed_penalty_lowers_final_score(self):
        feedback_repo = MagicMock()
        service = TrainingService(feedback_repository=feedback_repo)

        now = datetime.now(timezone.utc)
        feedback_repo.get_user_opinion_events.return_value = [
            {"exercise_id": 99, "rating": 5, "created_at": now - timedelta(days=1)}
        ]
        feedback_repo.get_user_not_completed_events.return_value = [
            {"exercise_id": 99, "reason_code": "bol_dyskomfort", "created_at": now - timedelta(days=1)}
        ]

        scores = service.get_user_preference_scores(user_id="user_1")

        assert 99 in scores
        assert scores[99] < 1.0
