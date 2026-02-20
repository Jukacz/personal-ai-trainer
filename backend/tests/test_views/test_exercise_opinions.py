"""Tests for exercise opinions view endpoints."""

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


class TestExerciseOpinionsView:
    """Test suite for exercise opinions endpoints."""

    def test_get_opinion_returns_200(self, test_client, mock_training_service):
        mock_training_service.get_exercise_opinion.return_value = {
            "exercise_id": 123,
            "rating": 4,
            "opinion": "Dobre",
            "updated_at": datetime.now(timezone.utc),
        }

        response = test_client.get("/api/v1/exercise-opinions/123")

        assert response.status_code == 200
        payload = response.json()
        assert payload["exercise_id"] == 123
        assert payload["rating"] == 4

    def test_put_opinion_returns_200(self, test_client, mock_training_service):
        mock_training_service.upsert_exercise_opinion.return_value = {
            "exercise_id": 123,
            "rating": 5,
            "opinion": "Super",
            "updated_at": datetime.now(timezone.utc),
        }

        response = test_client.put(
            "/api/v1/exercise-opinions/123",
            json={"rating": 5, "opinion": "Super"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["rating"] == 5
