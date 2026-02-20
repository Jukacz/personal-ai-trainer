"""Test suite for training controller.

Tests the business logic layer including:
- Creating training plan tasks
- Generating training plans in background
- Getting task status
- Getting training by ID
- Getting training list
"""

import pytest
from unittest.mock import MagicMock
from fastapi import BackgroundTasks

from api.controllers.training_controller import TrainingController
from api.schemas.requests import CreateTrainingRequest
from api.exceptions.handlers import (
    TrainingConflictError,
    TaskNotFoundError,
    TrainingNotFoundError,
    TrainingGenerationError,
)


class TestTrainingControllerInitialization:
    """Tests for TrainingController initialization."""

    def test_controller_initializes_with_dependencies(
        self, mock_training_repository, mock_training_service
    ):
        """Test controller initializes with provided dependencies.

        Verifies dependency injection works correctly.
        """
        controller = TrainingController(
            repository=mock_training_repository,
            service=mock_training_service,
        )

        assert controller.repository == mock_training_repository
        assert controller.service == mock_training_service

    def test_controller_initializes_with_default_dependencies(self):
        """Test controller initializes with default dependencies.

        Verifies fallback to default instances when not provided.
        """
        controller = TrainingController()

        assert controller.repository is not None
        assert controller.service is not None


class TestCreateTrainingPlan:
    """Tests for create_training_plan method."""

    def test_create_training_plan_creates_task(
        self, mock_training_repository, mock_training_service
    ):
        """Test that create_training_plan creates a task record.

        Verifies repository.create_task is called with correct parameters.
        """
        controller = TrainingController(
            repository=mock_training_repository,
            service=mock_training_service,
        )

        request = CreateTrainingRequest(
            age=30,
            weight=80.0,
            target_weight=75.0,
            difficulty="Intermediate",
            selected_days=["monday", "wednesday", "friday"],
        )
        background_tasks = MagicMock(spec=BackgroundTasks)

        controller.create_training_plan(
            request=request,
            background_tasks=background_tasks,
            user_id="test_user_123",
        )

        mock_training_repository.create_task.assert_called_once()
        call_kwargs = mock_training_repository.create_task.call_args.kwargs
        assert call_kwargs["status"] == "pending"
        assert call_kwargs["user_id"] == "test_user_123"

    def test_create_training_plan_schedules_background_task(
        self, mock_training_repository, mock_training_service
    ):
        """Test that create_training_plan schedules background task.

        Verifies background_tasks.add_task is called.
        """
        controller = TrainingController(
            repository=mock_training_repository,
            service=mock_training_service,
        )

        request = CreateTrainingRequest(age=30, weight=80.0, target_weight=75.0)
        background_tasks = MagicMock(spec=BackgroundTasks)

        controller.create_training_plan(
            request=request,
            background_tasks=background_tasks,
            user_id="test_user_123",
        )

        background_tasks.add_task.assert_called_once()

    def test_create_training_plan_returns_correct_response(
        self, mock_training_repository, mock_training_service
    ):
        """Test that create_training_plan returns correct response.

        Verifies response includes task_id and status.
        """
        controller = TrainingController(
            repository=mock_training_repository,
            service=mock_training_service,
        )

        request = CreateTrainingRequest(age=30, weight=80.0, target_weight=75.0)
        background_tasks = MagicMock(spec=BackgroundTasks)

        response = controller.create_training_plan(
            request=request,
            background_tasks=background_tasks,
            user_id="test_user_123",
        )

        assert response.task_id is not None
        assert response.status == "pending"
        assert response.check_status_url is not None
        assert response.task_id in response.check_status_url

    def test_create_training_plan_with_default_difficulty(
        self, mock_training_repository, mock_training_service
    ):
        """Test that create_training_plan uses default difficulty.

        Verifies 'Intermediate' is used when not specified.
        """
        controller = TrainingController(
            repository=mock_training_repository,
            service=mock_training_service,
        )

        request = CreateTrainingRequest(age=30, weight=80.0, target_weight=75.0)
        background_tasks = MagicMock(spec=BackgroundTasks)

        controller.create_training_plan(
            request=request,
            background_tasks=background_tasks,
        )

        background_tasks.add_task.assert_called_once()
        call_args = background_tasks.add_task.call_args
        assert call_args.kwargs["difficulty"] == "Intermediate"
        assert call_args.kwargs["selected_days"] == [
            "monday",
            "thursday",
            "saturday",
        ]

    def test_create_training_plan_passes_selected_days_to_task(
        self, mock_training_repository, mock_training_service
    ):
        """Test that create_training_plan passes selected_days to background task."""
        controller = TrainingController(
            repository=mock_training_repository,
            service=mock_training_service,
        )

        request = CreateTrainingRequest(
            age=30,
            weight=80.0,
            target_weight=75.0,
            selected_days=["tuesday", "thursday", "saturday"],
        )
        background_tasks = MagicMock(spec=BackgroundTasks)

        controller.create_training_plan(
            request=request,
            background_tasks=background_tasks,
        )

        call_args = background_tasks.add_task.call_args
        assert call_args.kwargs["selected_days"] == [
            "tuesday",
            "thursday",
            "saturday",
        ]

    def test_create_training_plan_raises_conflict_without_overwrite(
        self, mock_training_repository, mock_training_service
    ):
        """Test that conflict raises TrainingConflictError when overwrite is disabled."""
        mock_training_service.get_upcoming_training_dates.return_value = ["2024-01-15"]
        mock_training_repository.get_conflicts_for_dates.return_value = [
            {
                "date": "2024-01-15",
                "existing_training_id": "plan_1",
                "existing_training_name": "Plecy",
            }
        ]
        controller = TrainingController(
            repository=mock_training_repository,
            service=mock_training_service,
        )
        request = CreateTrainingRequest(selected_days=["monday", "thursday"])
        background_tasks = MagicMock(spec=BackgroundTasks)

        with pytest.raises(TrainingConflictError):
            controller.create_training_plan(
                request=request,
                background_tasks=background_tasks,
                user_id="test_user_123",
            )

    def test_create_training_plan_removes_conflicts_when_overwrite_enabled(
        self, mock_training_repository, mock_training_service
    ):
        """Test overwrite flow removes conflicting days before scheduling task."""
        mock_training_service.get_upcoming_training_dates.return_value = ["2024-01-15"]
        mock_training_repository.get_conflicts_for_dates.return_value = [
            {
                "date": "2024-01-15",
                "existing_training_id": "plan_1",
                "existing_training_name": "Plecy",
            }
        ]
        controller = TrainingController(
            repository=mock_training_repository,
            service=mock_training_service,
        )
        request = CreateTrainingRequest(
            selected_days=["monday", "thursday"],
            overwrite_conflicts=True,
            conflict_dates=["2024-01-15"],
        )
        background_tasks = MagicMock(spec=BackgroundTasks)

        response = controller.create_training_plan(
            request=request,
            background_tasks=background_tasks,
            user_id="test_user_123",
        )

        assert response.task_id is not None
        mock_training_repository.remove_conflicting_days.assert_called_once_with(
            ["2024-01-15"],
            user_id="test_user_123",
        )


class TestGeneratePlanTask:
    """Tests for _generate_plan_task background task."""

    def test_generate_plan_task_updates_status_to_processing(
        self, mock_training_repository, mock_training_service
    ):
        """Test that _generate_plan_task updates status to processing.

        Verifies initial status update happens.
        """
        controller = TrainingController(
            repository=mock_training_repository,
            service=mock_training_service,
        )

        controller._generate_plan_task(
            task_id="test_task_123",
            age=30,
            weight=80.0,
            target_weight=75.0,
            difficulty="Intermediate",
        )

        # First call should update to processing
        assert mock_training_repository.update_task_status.call_count >= 1

    def test_generate_plan_task_calls_service_generate(
        self, mock_training_repository, mock_training_service
    ):
        """Test that _generate_plan_task calls service.generate_training_plan.

        Verifies service is invoked with correct parameters.
        """
        controller = TrainingController(
            repository=mock_training_repository,
            service=mock_training_service,
        )

        controller._generate_plan_task(
            task_id="test_task_123",
            age=30,
            weight=80.0,
            target_weight=75.0,
            difficulty="Advanced",
            selected_days=["monday", "wednesday", "friday"],
        )

        mock_training_service.generate_training_plan.assert_called_once()
        call_kwargs = mock_training_service.generate_training_plan.call_args.kwargs
        assert call_kwargs["age"] == 30
        assert call_kwargs["weight"] == 80.0
        assert call_kwargs["target_weight"] == 75.0
        assert call_kwargs["difficulty"] == "Advanced"
        assert call_kwargs["selected_days"] == ["monday", "wednesday", "friday"]

    def test_generate_plan_task_saves_training_plan(
        self, mock_training_repository, mock_training_service
    ):
        """Test that _generate_plan_task saves the generated plan.

        Verifies repository.save_training_plan is called.
        """
        controller = TrainingController(
            repository=mock_training_repository,
            service=mock_training_service,
        )

        controller._generate_plan_task(
            task_id="test_task_123",
            age=30,
            weight=80.0,
            target_weight=75.0,
            user_id="test_user_123",
        )

        mock_training_repository.save_training_plan.assert_called_once()

    def test_generate_plan_task_updates_status_to_completed(
        self, mock_training_repository, mock_training_service
    ):
        """Test that _generate_plan_task updates status to completed.

        Verifies final status is set to completed with result.
        """
        controller = TrainingController(
            repository=mock_training_repository,
            service=mock_training_service,
        )

        controller._generate_plan_task(
            task_id="test_task_123",
            age=30,
            weight=80.0,
            target_weight=75.0,
        )

        # Check that update_task_status was called with completed status
        calls = mock_training_repository.update_task_status.call_args_list
        completed_calls = [
            c for c in calls
            if c.kwargs.get("status") == "completed"
        ]
        assert len(completed_calls) > 0

    def test_generate_plan_task_handles_generation_error(
        self, mock_training_repository, mock_training_service
    ):
        """Test that _generate_plan_task handles TrainingGenerationError.

        Verifies status is set to failed with error message.
        """
        mock_training_service.generate_training_plan.side_effect = (
            TrainingGenerationError("Generation failed", {"step": "planner"})
        )

        controller = TrainingController(
            repository=mock_training_repository,
            service=mock_training_service,
        )

        controller._generate_plan_task(
            task_id="test_task_123",
            age=30,
            weight=80.0,
            target_weight=75.0,
        )

        # Check that update_task_status was called with failed status
        calls = mock_training_repository.update_task_status.call_args_list
        failed_calls = [
            c for c in calls
            if c.kwargs.get("status") == "failed"
        ]
        assert len(failed_calls) > 0

    def test_generate_plan_task_handles_unexpected_error(
        self, mock_training_repository, mock_training_service
    ):
        """Test that _generate_plan_task handles unexpected errors.

        Verifies status is set to failed for any exception.
        """
        mock_training_service.generate_training_plan.side_effect = ValueError(
            "Unexpected error"
        )

        controller = TrainingController(
            repository=mock_training_repository,
            service=mock_training_service,
        )

        controller._generate_plan_task(
            task_id="test_task_123",
            age=30,
            weight=80.0,
            target_weight=75.0,
        )

        # Check that update_task_status was called with failed status
        calls = mock_training_repository.update_task_status.call_args_list
        failed_calls = [
            c for c in calls
            if c.kwargs.get("status") == "failed"
        ]
        assert len(failed_calls) > 0


class TestGetTaskStatus:
    """Tests for get_task_status method."""

    def test_get_task_status_returns_task_response(
        self,
        mock_training_repository,
        mock_training_service,
        sample_task_document,
    ):
        """Test that get_task_status returns TaskStatusResponse.

        Verifies all fields are mapped correctly.
        """
        mock_training_repository.get_task.return_value = sample_task_document

        controller = TrainingController(
            repository=mock_training_repository,
            service=mock_training_service,
        )

        response = controller.get_task_status("test_task_123")

        assert response.task_id == sample_task_document["_id"]
        assert response.status == sample_task_document["status"]
        assert response.message == sample_task_document["message"]

    def test_get_task_status_raises_if_not_found(
        self, mock_training_repository, mock_training_service
    ):
        """Test that get_task_status raises TaskNotFoundError if not found.

        Verifies proper exception handling.
        """
        mock_training_repository.get_task.return_value = None

        controller = TrainingController(
            repository=mock_training_repository,
            service=mock_training_service,
        )

        with pytest.raises(TaskNotFoundError):
            controller.get_task_status("nonexistent_task")

    def test_get_task_status_passes_user_id(
        self,
        mock_training_repository,
        mock_training_service,
        sample_task_document,
    ):
        """Test that get_task_status passes user_id to repository.

        Verifies security - users can only access their own tasks.
        """
        mock_training_repository.get_task.return_value = sample_task_document

        controller = TrainingController(
            repository=mock_training_repository,
            service=mock_training_service,
        )

        controller.get_task_status("test_task_123", user_id="test_user_123")

        mock_training_repository.get_task.assert_called_once_with(
            "test_task_123",
            user_id="test_user_123",
        )


class TestGetTrainingsListMethod:
    """Tests for get_trainings_list method."""

    def test_get_trainings_list_returns_response(
        self,
        mock_training_repository,
        mock_training_service,
        sample_training_list,
    ):
        """Test that get_trainings_list returns TrainingListResponse.

        Verifies correct response format with total and trainings.
        """
        mock_training_repository.get_trainings_list.return_value = (
            sample_training_list
        )

        controller = TrainingController(
            repository=mock_training_repository,
            service=mock_training_service,
        )

        response = controller.get_trainings_list()

        assert response.total == sample_training_list["total"]
        assert len(response.trainings) == len(sample_training_list["trainings"])

    def test_get_trainings_list_applies_pagination(
        self, mock_training_repository, mock_training_service
    ):
        """Test that get_trainings_list passes pagination parameters.

        Verifies limit and offset are forwarded to repository.
        """
        mock_training_repository.get_trainings_list.return_value = {
            "total": 100,
            "trainings": [],
        }

        controller = TrainingController(
            repository=mock_training_repository,
            service=mock_training_service,
        )

        controller.get_trainings_list(limit=20, offset=40)

        mock_training_repository.get_trainings_list.assert_called_once_with(
            limit=20,
            offset=40,
            user_id=None,
        )

    def test_get_trainings_list_filters_by_user(
        self, mock_training_repository, mock_training_service
    ):
        """Test that get_trainings_list filters by user_id.

        Verifies security - users only see their own trainings.
        """
        mock_training_repository.get_trainings_list.return_value = {
            "total": 5,
            "trainings": [],
        }

        controller = TrainingController(
            repository=mock_training_repository,
            service=mock_training_service,
        )

        controller.get_trainings_list(user_id="test_user_123")

        call_kwargs = (
            mock_training_repository.get_trainings_list.call_args.kwargs
        )
        assert call_kwargs["user_id"] == "test_user_123"


class TestGetTrainingCalendarDaysMethod:
    """Tests for get_training_calendar_days method."""

    def test_get_training_calendar_days_returns_response(
        self, mock_training_repository, mock_training_service
    ):
        """Controller maps repository rows into response schema."""
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
        controller = TrainingController(
            repository=mock_training_repository,
            service=mock_training_service,
        )

        response = controller.get_training_calendar_days(user_id="test_user_123")

        assert len(response.days) == 1
        assert response.days[0].date == "2026-02-24"

    def test_get_training_calendar_days_ignores_duplicate_diagnostics(
        self, mock_training_repository, mock_training_service
    ):
        """Controller should still return response when duplicates are detected."""
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
        controller = TrainingController(
            repository=mock_training_repository,
            service=mock_training_service,
        )

        response = controller.get_training_calendar_days(user_id="test_user_123")
        assert len(response.days) == 1
        assert response.days[0].date == "2026-02-24"


class TestGetTrainingConflictsMethod:
    """Tests for get_training_conflicts method."""

    def test_get_training_conflicts_returns_conflict_payload(
        self, mock_training_repository, mock_training_service
    ):
        """Test get_training_conflicts maps repository conflicts into response."""
        mock_training_service.get_upcoming_training_dates.return_value = ["2024-01-15"]
        mock_training_repository.get_conflicts_for_dates.return_value = [
            {
                "date": "2024-01-15",
                "existing_training_id": "plan_1",
                "existing_training_name": "Push",
            }
        ]
        controller = TrainingController(
            repository=mock_training_repository,
            service=mock_training_service,
        )

        response = controller.get_training_conflicts(
            selected_days=["monday", "thursday"],
            user_id="test_user_123",
        )

        assert response.has_conflicts is True
        assert response.conflict_dates == ["2024-01-15"]
        assert len(response.conflicts) == 1


class TestGetTrainingById:
    """Tests for get_training_by_id method."""

    def test_get_training_by_id_returns_response(
        self,
        mock_training_repository,
        mock_training_service,
        sample_training_document,
    ):
        """Test that get_training_by_id returns TrainingPlanResponse.

        Verifies all fields are mapped correctly.
        """
        mock_training_repository.get_training_by_id.return_value = (
            sample_training_document
        )

        controller = TrainingController(
            repository=mock_training_repository,
            service=mock_training_service,
        )

        response = controller.get_training_by_id("test_training_123")

        assert response.id == str(sample_training_document["_id"])
        # response.trainings is a list of TrainingDayResponse objects
        assert len(response.trainings) == len(sample_training_document.get("trainings", []))
        assert response.created_at is not None

    def test_get_training_by_id_raises_if_not_found(
        self, mock_training_repository, mock_training_service
    ):
        """Test that get_training_by_id raises TrainingNotFoundError.

        Verifies proper exception handling.
        """
        mock_training_repository.get_training_by_id.return_value = None

        controller = TrainingController(
            repository=mock_training_repository,
            service=mock_training_service,
        )

        with pytest.raises(TrainingNotFoundError):
            controller.get_training_by_id("nonexistent_training")

    def test_get_training_by_id_passes_user_id(
        self,
        mock_training_repository,
        mock_training_service,
        sample_training_document,
    ):
        """Test that get_training_by_id passes user_id to repository.

        Verifies security - users can only access their own trainings.
        """
        mock_training_repository.get_training_by_id.return_value = (
            sample_training_document
        )

        controller = TrainingController(
            repository=mock_training_repository,
            service=mock_training_service,
        )

        controller.get_training_by_id("test_training_123", user_id="test_user_123")

        mock_training_repository.get_training_by_id.assert_called_once_with(
            "test_training_123",
            user_id="test_user_123",
        )
