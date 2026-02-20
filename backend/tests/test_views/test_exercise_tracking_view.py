"""Tests for exercise tracking status endpoints."""

from datetime import datetime, timezone

import pytest


@pytest.fixture(autouse=True)
def setup_dependencies_override(
    test_client,
    mock_current_user,
    mock_training_repository,
    mock_training_service,
):
    """Override auth and controller dependencies."""
    from api.app import app
    from api.auth.dependencies import get_current_user
    from api.controllers.training_controller import TrainingController, get_training_controller

    mock_controller = TrainingController(
        repository=mock_training_repository,
        service=mock_training_service,
    )

    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    app.dependency_overrides[get_training_controller] = lambda: mock_controller
    yield
    app.dependency_overrides.clear()


class TestExerciseTrackingView:
    """Test suite for complete/not-completed routes."""

    def test_complete_returns_201(self, test_client, mock_training_service):
        mock_training_service.complete_exercise_for_day.return_value = {
            "training_id": "plan_1",
            "day": "2026-02-20",
            "exercise_index": 1,
            "exercise_id": 456,
            "status": "completed",
            "reason_code": None,
            "reason_text": None,
            "updated_at": datetime.now(timezone.utc),
            "completed_at": datetime.now(timezone.utc),
            "existing_opinion": None,
        }

        response = test_client.post(
            "/api/v1/trainings/plan_1/exercises/complete",
            json={"day": "2026-02-20", "exercise_index": 1},
        )

        assert response.status_code == 201
        payload = response.json()
        assert payload["status"] == "completed"

    def test_not_completed_returns_201(self, test_client, mock_training_service):
        mock_training_service.mark_exercise_not_completed_for_day.return_value = {
            "training_id": "plan_1",
            "day": "2026-02-20",
            "exercise_index": 2,
            "exercise_id": 789,
            "status": "not_completed",
            "reason_code": "brak_czasu",
            "reason_text": "Spotkanie",
            "updated_at": datetime.now(timezone.utc),
            "completed_at": None,
            "existing_opinion": None,
        }

        response = test_client.post(
            "/api/v1/trainings/plan_1/exercises/not-completed",
            json={
                "day": "2026-02-20",
                "exercise_index": 2,
                "reason_code": "brak_czasu",
                "reason_text": "Spotkanie",
            },
        )

        assert response.status_code == 201
        payload = response.json()
        assert payload["status"] == "not_completed"
        assert payload["reason_code"] == "brak_czasu"

    def test_not_completed_invalid_reason_returns_422(self, test_client):
        response = test_client.post(
            "/api/v1/trainings/plan_1/exercises/not-completed",
            json={
                "day": "2026-02-20",
                "exercise_index": 2,
                "reason_code": "invalid_reason",
            },
        )

        assert response.status_code == 422
