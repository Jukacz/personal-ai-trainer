"""Tests for range-based and quick training creation views."""

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


class TestTrainingModesView:
    """Tests for new range and quick flows."""

    def test_create_training_accepts_range_payload(self, test_client):
        response = test_client.post(
            "/api/v1/trainings",
            json={
                "age": 30,
                "weight": 80,
                "target_weight": 75,
                "difficulty": "Intermediate",
                "start_date": "2026-02-23",
                "end_date": "2026-03-08",
                "trainings_per_week": 3,
                "selected_days": ["monday", "wednesday", "friday"],
            },
        )

        assert response.status_code == 202

    def test_create_training_rejects_days_and_weekly_count_mismatch(self, test_client):
        response = test_client.post(
            "/api/v1/trainings",
            json={
                "start_date": "2026-02-23",
                "end_date": "2026-03-08",
                "trainings_per_week": 2,
                "selected_days": ["monday", "wednesday", "friday"],
            },
        )

        assert response.status_code == 422

    def test_quick_training_conflicts_returns_200(self, test_client):
        response = test_client.post(
            "/api/v1/trainings/quick/conflicts",
            json={},
        )

        assert response.status_code == 200
        payload = response.json()
        assert "has_conflicts" in payload

    def test_create_quick_training_returns_202(self, test_client):
        response = test_client.post(
            "/api/v1/trainings/quick",
            json={"difficulty": "Intermediate"},
        )

        assert response.status_code == 202
        payload = response.json()
        assert "task_id" in payload
