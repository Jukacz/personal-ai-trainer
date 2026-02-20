"""Test suite for training views (HTTP endpoints).

Tests the trainings API routes including:
- Creating training plans (POST /trainings)
- Getting task status (GET /trainings/tasks/{task_id})
- Getting training list (GET /trainings)
- Getting specific training (GET /trainings/{training_id})
"""

import pytest
from datetime import datetime, timezone


@pytest.fixture(autouse=True)
def setup_dependencies_override(
    test_client,
    mock_current_user,
    mock_training_repository,
    mock_training_service
):
    """Override dependencies for all view tests.

    This fixture automatically applies to all tests in this module.
    Overrides both authentication and controller dependencies.
    """
    from api.app import app
    from api.auth.dependencies import get_current_user
    from api.controllers.training_controller import get_training_controller, TrainingController

    # Create controller with mocked dependencies
    mock_controller = TrainingController(
        repository=mock_training_repository,
        service=mock_training_service
    )

    # Override the dependencies
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    app.dependency_overrides[get_training_controller] = lambda: mock_controller

    yield

    # Cleanup
    app.dependency_overrides.clear()


class TestCreateTrainingEndpoint:
    """Tests for POST /trainings endpoint."""

    def test_create_training_valid_request_returns_202(
        self,
        test_client,
        mock_training_repository,
        valid_create_training_request,
    ):
        """Test creating training plan with valid request returns 202 Accepted.

        Verifies:
        - Status code is 202 (Accepted)
        - Response contains task_id
        - Response contains check_status_url
        - Status is 'pending'
        """
        response = test_client.post(
            "/api/v1/trainings",
            json=valid_create_training_request,
        )

        assert response.status_code == 202
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "pending"
        assert "check_status_url" in data
        assert data["task_id"] in data["check_status_url"]

    def test_create_training_with_defaults_returns_202(
        self,
        test_client,
        minimal_create_training_request,
    ):
        """Test creating training plan with default values returns 202.

        Verifies that all fields are optional and defaults are applied.
        """
        response = test_client.post(
            "/api/v1/trainings",
            json=minimal_create_training_request,
        )

        assert response.status_code == 202
        data = response.json()
        assert "task_id" in data

    def test_create_training_invalid_age_returns_422(
        self,
        test_client,
    ):
        """Test creating training with invalid age (too low) returns 422.

        Verifies validation error for age < 16.
        """
        response = test_client.post(
            "/api/v1/trainings",
            json={"age": 10, "weight": 80.0, "target_weight": 75.0},
        )

        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "ValidationError"

    def test_create_training_invalid_weight_returns_422(
        self,
        test_client,
    ):
        """Test creating training with invalid weight returns 422.

        Verifies validation error for weight <= 30.
        """
        response = test_client.post(
            "/api/v1/trainings",
            json={"age": 30, "weight": 20.0, "target_weight": 75.0},
        )

        assert response.status_code == 422

    def test_create_training_calls_repository_create_task(
        self,
        test_client,
        mock_training_repository,
        valid_create_training_request,
    ):
        """Test that create_training calls repository.create_task.

        Verifies repository method is called with correct parameters.
        """
        response = test_client.post(
            "/api/v1/trainings",
            json=valid_create_training_request,
        )

        assert response.status_code == 202
        mock_training_repository.create_task.assert_called_once()

    def test_create_training_single_selected_day_returns_202(
        self,
        test_client,
    ):
        """Test creating training with one selected day is allowed."""
        response = test_client.post(
            "/api/v1/trainings",
            json={"selected_days": ["monday"]},
        )

        assert response.status_code == 202

    def test_create_training_invalid_selected_days_too_many_returns_422(
        self,
        test_client,
    ):
        """Test creating training with seven selected days returns 422."""
        response = test_client.post(
            "/api/v1/trainings",
            json={
                "selected_days": [
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday",
                    "saturday",
                    "sunday",
                ]
            },
        )

        assert response.status_code == 422

    def test_create_training_invalid_selected_days_duplicates_returns_422(
        self,
        test_client,
    ):
        """Test creating training with duplicate selected days returns 422."""
        response = test_client.post(
            "/api/v1/trainings",
            json={"selected_days": ["tuesday", "tuesday"]},
        )

        assert response.status_code == 422

    def test_create_training_with_valid_selected_days_returns_202(
        self,
        test_client,
    ):
        """Test creating training with valid selected days returns 202."""
        response = test_client.post(
            "/api/v1/trainings",
            json={"selected_days": ["tuesday", "thursday", "saturday"]},
        )

        assert response.status_code == 202

    def test_create_training_with_conflicts_returns_409(
        self,
        test_client,
        mock_training_repository,
    ):
        """Test create endpoint returns 409 when selected days conflict."""
        mock_training_repository.get_conflicts_for_dates.return_value = [
            {
                "date": "2024-01-15",
                "existing_training_id": "plan_1",
                "existing_training_name": "Plecy",
            }
        ]

        response = test_client.post(
            "/api/v1/trainings",
            json={"selected_days": ["monday", "thursday"]},
        )

        assert response.status_code == 409
        data = response.json()
        assert data["error"] == "TrainingConflictError"
        assert data["details"]["has_conflicts"] is True


class TestGetTaskStatusEndpoint:
    """Tests for GET /trainings/tasks/{task_id} endpoint."""

    def test_get_task_status_pending_returns_200(
        self,
        test_client,
        mock_training_repository,
        sample_task_document,
    ):
        """Test getting pending task status returns 200 with pending status.

        Verifies correct response for task still being processed.
        """
        mock_training_repository.get_task.return_value = sample_task_document

        response = test_client.get(
            "/api/v1/trainings/tasks/507f1f77bcf86cd799439011"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert data["error"] is None
        assert "created_at" in data

    def test_get_task_status_completed_returns_200_with_result(
        self,
        test_client,
        mock_training_repository,
        sample_completed_task_document,
    ):
        """Test getting completed task status returns 200 with result.

        Verifies response includes training_id when task is completed.
        """
        mock_training_repository.get_task.return_value = (
            sample_completed_task_document
        )

        response = test_client.get(
            "/api/v1/trainings/tasks/507f1f77bcf86cd799439011"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["result"] is not None
        assert "training_id" in data["result"]
        assert "completed_at" in data

    def test_get_task_status_failed_returns_200_with_error(
        self,
        test_client,
        mock_training_repository,
        sample_failed_task_document,
    ):
        """Test getting failed task status returns 200 with error message.

        Verifies response includes error when task failed.
        """
        mock_training_repository.get_task.return_value = (
            sample_failed_task_document
        )

        response = test_client.get(
            "/api/v1/trainings/tasks/507f1f77bcf86cd799439011"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert data["error"] is not None

    def test_get_task_status_not_found_returns_404(
        self,
        test_client,
        mock_training_repository,
    ):
        """Test getting non-existent task returns 404.

        Verifies proper error handling for missing tasks.
        """
        mock_training_repository.get_task.return_value = None

        response = test_client.get(
            "/api/v1/trainings/tasks/nonexistent"
        )

        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "NotFoundError"

    def test_get_task_status_calls_repository_with_user_id(
        self,
        test_client,
        mock_training_repository,
        sample_task_document,
    ):
        """Test that get_task_status passes user_id to repository.

        Verifies security check - users can only access their own tasks.
        """
        mock_training_repository.get_task.return_value = sample_task_document

        test_client.get("/api/v1/trainings/tasks/507f1f77bcf86cd799439011")

        mock_training_repository.get_task.assert_called_once()
        call_args = mock_training_repository.get_task.call_args
        assert "user_id" in call_args.kwargs or len(call_args.args) > 1


class TestGetTrainingsListEndpoint:
    """Tests for GET /trainings endpoint."""

    def test_get_trainings_list_returns_200(
        self,
        test_client,
        mock_training_repository,
        sample_training_list,
    ):
        """Test getting training list returns 200 with paginated results.

        Verifies correct response format with total and trainings list.
        """
        mock_training_repository.get_trainings_list.return_value = (
            sample_training_list
        )

        response = test_client.get("/api/v1/trainings")

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "trainings" in data
        assert data["total"] == 5
        assert len(data["trainings"]) == 2

    def test_get_trainings_list_with_limit(
        self,
        test_client,
        mock_training_repository,
        sample_training_list,
    ):
        """Test getting training list with custom limit parameter.

        Verifies limit parameter is passed to repository.
        """
        mock_training_repository.get_trainings_list.return_value = {
            "total": 5,
            "trainings": sample_training_list["trainings"][:1],
        }

        response = test_client.get("/api/v1/trainings?limit=1")

        assert response.status_code == 200
        mock_training_repository.get_trainings_list.assert_called_once()
        call_kwargs = mock_training_repository.get_trainings_list.call_args.kwargs
        assert call_kwargs["limit"] == 1

    def test_get_trainings_list_with_offset(
        self,
        test_client,
        mock_training_repository,
        sample_training_list,
    ):
        """Test getting training list with offset parameter.

        Verifies offset (pagination) parameter is passed to repository.
        """
        mock_training_repository.get_trainings_list.return_value = {
            "total": 5,
            "trainings": [],
        }

        response = test_client.get("/api/v1/trainings?offset=10")

        assert response.status_code == 200
        call_kwargs = mock_training_repository.get_trainings_list.call_args.kwargs
        assert call_kwargs["offset"] == 10

    def test_get_trainings_list_invalid_limit_returns_422(
        self,
        test_client,
        mock_training_repository,
    ):
        """Test getting trainings with invalid limit (too high) returns 422.

        Verifies validation for limit <= 100.
        """
        response = test_client.get("/api/v1/trainings?limit=1000")

        assert response.status_code == 422

    def test_get_trainings_list_empty_returns_200(
        self,
        test_client,
        mock_training_repository,
    ):
        """Test getting empty trainings list returns 200 with empty list.

        Verifies handling of users with no trainings.
        """
        mock_training_repository.get_trainings_list.return_value = {
            "total": 0,
            "trainings": [],
        }

        response = test_client.get("/api/v1/trainings")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["trainings"]) == 0


class TestTrainingConflictsEndpoint:
    """Tests for POST /trainings/conflicts endpoint."""

    def test_conflicts_endpoint_returns_200(
        self,
        test_client,
        mock_training_repository,
    ):
        """Test conflict endpoint returns response payload."""
        mock_training_repository.get_conflicts_for_dates.return_value = [
            {
                "date": "2024-01-15",
                "existing_training_id": "plan_1",
                "existing_training_name": "Plecy",
            }
        ]

        response = test_client.post(
            "/api/v1/trainings/conflicts",
            json={"selected_days": ["monday", "thursday"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_conflicts"] is True
        assert data["conflict_dates"] == ["2024-01-15"]


class TestTrainingCalendarDaysEndpoint:
    """Tests for GET /trainings/days endpoint."""

    def test_get_training_calendar_days_returns_200(
        self,
        test_client,
        mock_training_repository,
    ):
        """Calendar endpoint should return flat day entries."""
        mock_training_repository.get_training_calendar_days.return_value = (
            [
                {
                    "date": "2026-02-24",
                    "training_id": "699758e172715d47ea193230",
                    "training_name": "Plecy i Biceps",
                }
            ],
            [],
        )

        response = test_client.get("/api/v1/trainings/days")

        assert response.status_code == 200
        data = response.json()
        assert "days" in data
        assert len(data["days"]) == 1
        assert data["days"][0]["date"] == "2026-02-24"

    def test_get_training_calendar_days_returns_200_for_duplicates(
        self,
        test_client,
        mock_training_repository,
    ):
        """Duplicate-date diagnostics should not fail endpoint."""
        mock_training_repository.get_training_calendar_days.return_value = (
            [
                {
                    "date": "2026-02-24",
                    "training_id": "699758e172715d47ea193230",
                    "training_name": "Plecy i Biceps",
                }
            ],
            ["2026-02-24"],
        )

        response = test_client.get("/api/v1/trainings/days")

        assert response.status_code == 200
        data = response.json()
        assert len(data["days"]) == 1
        assert data["days"][0]["date"] == "2026-02-24"


class TestTrainingStatsEndpoint:
    """Tests for GET /trainings/stats endpoint."""

    def test_get_training_stats_returns_200(
        self,
        test_client,
        mock_training_service,
    ):
        """Stats endpoint should return aggregated dashboard payload."""
        mock_training_service.get_dashboard_stats.return_value = {
            "kpis": {
                "scheduled_trainings": 6,
                "completed_exercises_percent": 64,
                "not_completed_exercises": 5,
                "most_active_weekday": "Wt",
            },
            "training_trend": [{"date": "2026-02-20", "count": 1}],
            "status_distribution": [
                {"status": "completed", "value": 9},
                {"status": "not_completed", "value": 5},
                {"status": "pending", "value": 0},
            ],
            "weekday_distribution": [{"weekday": "Wt", "count": 2}],
        }

        response = test_client.get("/api/v1/trainings/stats?window_days=30")

        assert response.status_code == 200
        payload = response.json()
        assert payload["kpis"]["scheduled_trainings"] == 6
        assert payload["status_distribution"][0]["status"] == "completed"
        mock_training_service.get_dashboard_stats.assert_called_once()
        assert mock_training_service.get_dashboard_stats.call_args.kwargs["window_days"] == 30

    def test_get_training_stats_invalid_window_days_returns_422(
        self,
        test_client,
    ):
        """Stats endpoint should validate query params."""
        response = test_client.get("/api/v1/trainings/stats?window_days=0")
        assert response.status_code == 422


class TestGetTrainingByIdEndpoint:
    """Tests for GET /trainings/{training_id} endpoint."""

    def test_get_training_by_id_returns_200(
        self,
        test_client,
        mock_training_repository,
        sample_training_document,
    ):
        """Test getting training plan by ID returns 200 with plan details.

        Verifies complete training plan is returned.
        """
        mock_training_repository.get_training_by_id.return_value = (
            sample_training_document
        )

        response = test_client.get(
            "/api/v1/trainings/507f1f77bcf86cd799439012"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "507f1f77bcf86cd799439012"
        assert "trainings" in data
        assert "created_at" in data

    def test_get_training_by_id_with_exercises_returns_200(
        self,
        test_client,
        mock_training_repository,
        sample_training_document,
    ):
        """Test getting training with exercises returns complete data.

        Verifies exercises are included in response.
        """
        mock_training_repository.get_training_by_id.return_value = (
            sample_training_document
        )

        response = test_client.get(
            "/api/v1/trainings/507f1f77bcf86cd799439012"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["trainings"]) > 0
        first_training = data["trainings"][0]
        assert "exercises" in first_training
        assert len(first_training["exercises"]) > 0
        exercise = first_training["exercises"][0]
        assert "name" in exercise
        assert "videos" in exercise
        assert "steps" in exercise

    def test_get_training_by_id_not_found_returns_404(
        self,
        test_client,
        mock_training_repository,
    ):
        """Test getting non-existent training returns 404.

        Verifies proper error handling for missing trainings.
        """
        mock_training_repository.get_training_by_id.return_value = None

        response = test_client.get(
            "/api/v1/trainings/nonexistent"
        )

        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "NotFoundError"

    def test_get_training_by_id_invalid_id_format_returns_404(
        self,
        test_client,
        mock_training_repository,
    ):
        """Test getting training with invalid ID format returns 404.

        Verifies handling of malformed MongoDB ObjectId.
        """
        mock_training_repository.get_training_by_id.return_value = None

        response = test_client.get(
            "/api/v1/trainings/invalid-id-format"
        )

        assert response.status_code == 404

    def test_get_training_by_id_calls_repository_with_user_id(
        self,
        test_client,
        mock_training_repository,
        sample_training_document,
    ):
        """Test that get_training passes user_id to repository.

        Verifies security check - users can only access their own trainings.
        """
        mock_training_repository.get_training_by_id.return_value = (
            sample_training_document
        )

        test_client.get("/api/v1/trainings/507f1f77bcf86cd799439012")

        mock_training_repository.get_training_by_id.assert_called_once()
        call_args = mock_training_repository.get_training_by_id.call_args
        assert "user_id" in call_args.kwargs or len(call_args.args) > 1


class TestHealthCheckEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check_returns_200(self, test_client):
        """Test health check endpoint returns 200 with status.

        Verifies the service is running.
        """
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestExerciseReplacementEndpoints:
    """Tests for suggestions and replace exercise endpoints."""

    def test_get_exercise_suggestions_returns_200(
        self,
        test_client,
        mock_training_repository,
        mock_training_service,
    ):
        mock_training_repository.get_training_day.return_value = {
            "training_id": "507f1f77bcf86cd799439012",
            "difficulty": "Intermediate",
            "day": "2026-02-24",
            "name": "Plecy",
            "time_required": 36,
            "body_parts": ["Back"],
            "exercises": [
                {"name": "Exercise A", "exercise_id": 1, "primary_muscles": ["Back"], "videos": [], "repetitions": "3 x 12", "steps": []}
            ],
        }
        mock_training_service.suggest_exercise_replacements.return_value = {
            "mode": "manual",
            "context_source": "exercise_primary_muscles",
            "fallback_used": False,
            "suggestions": [
                {
                    "exercise_id": 2,
                    "name": "Exercise B",
                    "primary_muscles": ["Back"],
                    "difficulty": "Intermediate",
                    "category": "Barbell",
                    "videos": [],
                    "repetitions": "4 x 10",
                    "steps": ["Step 1"],
                }
            ],
        }

        response = test_client.post(
            "/api/v1/trainings/507f1f77bcf86cd799439012/exercises/suggestions",
            json={
                "day": "2026-02-24",
                "exercise_index": 0,
                "mode": "manual",
                "limit": 20,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "manual"
        assert len(data["suggestions"]) == 1

    def test_replace_exercise_returns_200(
        self,
        test_client,
        mock_training_repository,
        mock_training_service,
    ):
        mock_training_repository.get_training_day.return_value = {
            "training_id": "507f1f77bcf86cd799439012",
            "difficulty": "Intermediate",
            "day": "2026-02-24",
            "name": "Plecy",
            "time_required": 36,
            "body_parts": ["Back"],
            "exercises": [
                {"name": "Exercise A", "exercise_id": 1, "primary_muscles": ["Back"], "videos": [], "repetitions": "3 x 12", "steps": []}
            ],
        }
        mock_training_service.build_replacement_exercise.return_value = {
            "name": "Exercise Z",
            "exercise_id": 9,
            "primary_muscles": ["Back"],
            "difficulty": "Intermediate",
            "category": "Cable",
            "videos": [],
            "repetitions": "4 x 10",
            "steps": [],
        }
        mock_training_repository.replace_training_day_exercise.return_value = {
            "updated_at": datetime.now(timezone.utc),
            "time_required": 36,
            "exercise": mock_training_service.build_replacement_exercise.return_value,
        }

        response = test_client.patch(
            "/api/v1/trainings/507f1f77bcf86cd799439012/exercises/replace",
            json={
                "day": "2026-02-24",
                "exercise_index": 0,
                "replacement_exercise_id": 9,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["exercise_index"] == 0
        assert data["exercise"]["exercise_id"] == 9

    def test_replace_exercise_invalid_index_returns_422(
        self,
        test_client,
        mock_training_repository,
    ):
        mock_training_repository.get_training_day.return_value = {
            "training_id": "507f1f77bcf86cd799439012",
            "difficulty": "Intermediate",
            "day": "2026-02-24",
            "name": "Plecy",
            "time_required": 36,
            "body_parts": ["Back"],
            "exercises": [],
        }

        response = test_client.patch(
            "/api/v1/trainings/507f1f77bcf86cd799439012/exercises/replace",
            json={
                "day": "2026-02-24",
                "exercise_index": 0,
                "replacement_exercise_id": 9,
            },
        )

        assert response.status_code == 422

    def test_get_exercise_suggestions_not_found_returns_404(
        self,
        test_client,
        mock_training_repository,
    ):
        mock_training_repository.get_training_day.return_value = None

        response = test_client.post(
            "/api/v1/trainings/507f1f77bcf86cd799439012/exercises/suggestions",
            json={
                "day": "2026-02-24",
                "exercise_index": 0,
                "mode": "manual",
            },
        )

        assert response.status_code == 404
