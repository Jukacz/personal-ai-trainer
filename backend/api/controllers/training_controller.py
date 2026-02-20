"""Controller layer for training endpoints.

Coordinates between views, services, and repositories.
Handles background task execution for long-running operations.
"""

import logging
from datetime import datetime

from fastapi import BackgroundTasks

from api.exceptions.handlers import (
    ExerciseOpinionNotFoundError,
    TrainingConflictError,
    InvalidExerciseReplaceError,
    TaskNotFoundError,
    TrainingNotFoundError,
    TrainingGenerationError,
)
from api.repositories.training_repository import (
    TrainingRepository,
    get_training_repository,
)
from api.schemas.requests import (
    CompleteExerciseRequest,
    CreateQuickTrainingRequest,
    CreateTrainingRequest,
    ExerciseSuggestionsRequest,
    MarkExerciseNotCompletedRequest,
    QuickTrainingConflictsRequest,
    ReplaceExerciseRequest,
    TrainingConflictsRequest,
    UpsertExerciseOpinionRequest,
)
from api.schemas.responses import (
    CreateTrainingResponse,
    TrainingDashboardStatsResponse,
    ExerciseOpinionResponse,
    ExerciseSuggestionsResponse,
    MarkExerciseStatusResponse,
    ReplaceExerciseResponse,
    TaskStatusResponse,
    TrainingConflictItemResponse,
    TrainingCalendarDayItemResponse,
    TrainingCalendarDaysResponse,
    TrainingConflictsResponse,
    TrainingListResponse,
    TrainingListItem,
    TrainingPlanResponse,
    TrainingProgressResponse,
)
from api.services.training_service import (
    TrainingService,
    get_training_service,
)

logger = logging.getLogger(__name__)


class TrainingController:
    """Controller for training plan operations.

    Handles request processing, background task management,
    and response formatting.
    """

    def __init__(
        self,
        repository: TrainingRepository | None = None,
        service: TrainingService | None = None
    ):
        """Initialize the controller with dependencies.

        Args:
            repository: Training repository instance (optional)
            service: Training service instance (optional)
        """
        self.repository = repository or get_training_repository()
        self.service = service or get_training_service()

    def create_training_plan(
        self,
        request: CreateTrainingRequest,
        background_tasks: BackgroundTasks,
        user_id: str | None = None
    ) -> CreateTrainingResponse:
        """Create a new training plan generation task.

        Creates a task record and schedules background generation.

        Args:
            request: Training plan request parameters
            background_tasks: FastAPI background tasks handler
            user_id: Optional user ID to associate with the task and plan

        Returns:
            Response with task_id for status polling
        """
        difficulty = request.difficulty or "Intermediate"
        logger.info(
            f"[Controller] Creating training plan task: "
            f"age={request.age}, weight={request.weight}, difficulty={difficulty}, "
            f"selected_days={request.selected_days}, range={request.start_date}:{request.end_date}, "
            f"trainings_per_week={request.trainings_per_week}, user_id={user_id}"
        )

        conflict_dates = self.service.get_training_dates_in_range(
            start_date=request.start_date,
            end_date=request.end_date,
            selected_days=request.selected_days,
            trainings_per_week=request.trainings_per_week or len(request.selected_days),
        )
        conflicts = self.repository.get_conflicts_for_dates(
            conflict_dates,
            user_id=user_id,
        )

        if conflicts and not request.overwrite_conflicts:
            raise TrainingConflictError(
                "Selected days conflict with existing training dates",
                conflicts=conflicts,
            )

        if request.overwrite_conflicts and conflicts:
            requested_dates = (
                sorted(set(request.conflict_dates))
                if request.conflict_dates
                else sorted({item["date"] for item in conflicts})
            )
            self.repository.remove_conflicting_days(requested_dates, user_id=user_id)

        # Create task record
        task_id = self.repository.create_task(
            status="pending",
            message="Training plan generation task has been created",
            user_id=user_id
        )

        logger.info(f"[Controller] Task created: {task_id}")

        # Schedule background generation
        background_tasks.add_task(
            self._generate_plan_task,
            task_id=task_id,
            age=request.age,
            weight=request.weight,
            target_weight=request.target_weight,
            difficulty=difficulty,
            selected_days=request.selected_days,
            start_date=request.start_date,
            end_date=request.end_date,
            trainings_per_week=request.trainings_per_week,
            user_id=user_id
        )

        return CreateTrainingResponse(
            task_id=task_id,
            status="pending",
            message="Training plan generation task has been created",
            check_status_url=f"/api/v1/trainings/tasks/{task_id}"
        )

    def get_training_conflicts(
        self,
        request: TrainingConflictsRequest | list[str] | None = None,
        *,
        selected_days: list[str] | None = None,
        user_id: str | None = None,
    ) -> TrainingConflictsResponse:
        """Get conflicts for selected training days in planning range."""
        if selected_days is not None:
            conflict_dates = self.service.get_upcoming_training_dates(selected_days)
        elif isinstance(request, list):
            conflict_dates = self.service.get_upcoming_training_dates(request)
        elif request is None:
            conflict_dates = self.service.get_upcoming_training_dates(None)
        else:
            conflict_dates = self.service.get_training_dates_in_range(
                start_date=request.start_date,
                end_date=request.end_date,
                selected_days=request.selected_days,
                trainings_per_week=request.trainings_per_week or len(request.selected_days),
            )
        conflicts = self.repository.get_conflicts_for_dates(conflict_dates, user_id=user_id)

        return TrainingConflictsResponse(
            has_conflicts=bool(conflicts),
            conflict_dates=sorted({item["date"] for item in conflicts}),
            conflicts=[
                TrainingConflictItemResponse(
                    date=item["date"],
                    existing_training_id=item["existing_training_id"],
                    existing_training_name=item["existing_training_name"],
                )
                for item in conflicts
            ],
        )

    def get_quick_training_conflicts(
        self,
        request: QuickTrainingConflictsRequest,
        user_id: str | None = None,
    ) -> TrainingConflictsResponse:
        """Get conflicts for quick training (today only)."""
        quick_day = self.service.get_quick_training_date(request.timezone)
        conflicts = self.repository.get_conflicts_for_dates([quick_day], user_id=user_id)
        return TrainingConflictsResponse(
            has_conflicts=bool(conflicts),
            conflict_dates=sorted({item["date"] for item in conflicts}),
            conflicts=[
                TrainingConflictItemResponse(
                    date=item["date"],
                    existing_training_id=item["existing_training_id"],
                    existing_training_name=item["existing_training_name"],
                )
                for item in conflicts
            ],
        )

    def create_quick_training(
        self,
        request: CreateQuickTrainingRequest,
        background_tasks: BackgroundTasks,
        user_id: str | None = None,
        overwrite_conflicts: bool = False,
    ) -> CreateTrainingResponse:
        """Create quick one-day training generation task."""
        quick_day = self.service.get_quick_training_date()
        conflicts = self.repository.get_conflicts_for_dates([quick_day], user_id=user_id)

        if conflicts and not overwrite_conflicts:
            raise TrainingConflictError(
                "Selected days conflict with existing training dates",
                conflicts=conflicts,
            )
        if overwrite_conflicts and conflicts:
            self.repository.remove_conflicting_days([quick_day], user_id=user_id)

        task_id = self.repository.create_task(
            status="pending",
            message="Quick training generation task has been created",
            user_id=user_id,
        )

        background_tasks.add_task(
            self._generate_quick_training_task,
            task_id=task_id,
            difficulty=request.difficulty,
            user_id=user_id,
        )
        return CreateTrainingResponse(
            task_id=task_id,
            status="pending",
            message="Quick training generation task has been created",
            check_status_url=f"/api/v1/trainings/tasks/{task_id}",
        )

    def get_training_calendar_days(
        self,
        user_id: str | None = None,
    ) -> TrainingCalendarDaysResponse:
        """Return flat calendar days with training references."""
        days, duplicate_dates = self.repository.get_training_calendar_days(user_id=user_id)
        if duplicate_dates:
            logger.warning(
                "[Controller] Duplicate training dates detected for user %s, returning first entries only: %s",
                user_id,
                duplicate_dates,
            )

        return TrainingCalendarDaysResponse(
            days=[
                TrainingCalendarDayItemResponse(
                    date=item["date"],
                    training_id=item["training_id"],
                    training_name=item["training_name"],
                )
                for item in days
            ]
        )

    def get_dashboard_stats(
        self,
        *,
        user_id: str,
        window_days: int = 30,
    ) -> TrainingDashboardStatsResponse:
        """Return aggregated dashboard stats for selected date window."""
        payload = self.service.get_dashboard_stats(
            user_id=user_id,
            window_days=window_days,
            training_repository=self.repository,
        )
        return TrainingDashboardStatsResponse(**payload)

    def _generate_plan_task(
        self,
        task_id: str,
        age: int,
        weight: float,
        target_weight: float,
        difficulty: str = "Intermediate",
        selected_days: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        trainings_per_week: int | None = None,
        user_id: str | None = None
    ) -> None:
        """Background task for generating training plan.

        Updates task status throughout the generation process.

        Args:
            task_id: The task ID to update
            age: Client age
            weight: Current weight
            target_weight: Target weight
            difficulty: Training difficulty level (Novice, Intermediate, Advanced)
            selected_days: Selected days of week (monday-sunday)
            user_id: Optional user ID to associate with the training plan
        """
        logger.info(f"[Controller] Starting background task: {task_id}")

        # Update status to processing
        self.repository.update_task_status(
            task_id=task_id,
            status="processing",
            message="Training plan generation in progress..."
        )

        try:
            # Generate the plan
            plan_data = self.service.generate_training_plan(
                age=age,
                weight=weight,
                target_weight=target_weight,
                difficulty=difficulty,
                selected_days=selected_days,
                start_date=start_date,
                end_date=end_date,
                trainings_per_week=trainings_per_week,
                user_id=user_id,
            )

            # Save to database with user association
            training_id = self.repository.save_training_plan(
                plan_data,
                user_id=user_id
            )
            logger.info(f"[Controller] Training plan saved: {training_id}")

            # Update task with result
            self.repository.update_task_status(
                task_id=task_id,
                status="completed",
                message="Training plan has been generated successfully",
                result={
                    "training_id": training_id,
                    "schema_version": 2,
                }
            )

            logger.info(f"[Controller] Task completed successfully: {task_id}")

        except TrainingGenerationError as e:
            logger.error(f"[Controller] Training generation failed: {e.message}")
            self.repository.update_task_status(
                task_id=task_id,
                status="failed",
                message="Training plan generation failed",
                error=e.message
            )

        except Exception as e:
            logger.exception(f"[Controller] Unexpected error in task {task_id}")
            self.repository.update_task_status(
                task_id=task_id,
                status="failed",
                message="An unexpected error occurred",
                error=str(e)
            )

    def _generate_quick_training_task(
        self,
        task_id: str,
        difficulty: str = "Intermediate",
        user_id: str | None = None,
    ) -> None:
        """Background task for generating quick one-day training."""
        self.repository.update_task_status(
            task_id=task_id,
            status="processing",
            message="Quick training generation in progress...",
        )
        try:
            if user_id is None:
                raise ValueError("Quick training requires authenticated user_id")
            plan_data = self.service.generate_quick_training_for_today(
                difficulty=difficulty,
                user_id=user_id,
                training_repository=self.repository,
            )
            training_id = self.repository.save_training_plan(plan_data, user_id=user_id)
            self.repository.update_task_status(
                task_id=task_id,
                status="completed",
                message="Quick training has been generated successfully",
                result={
                    "training_id": training_id,
                    "schema_version": 2,
                },
            )
        except Exception as exc:
            logger.exception("[Controller] Unexpected error in quick task %s", task_id)
            self.repository.update_task_status(
                task_id=task_id,
                status="failed",
                message="Quick training generation failed",
                error=str(exc),
            )

    def get_task_status(
        self,
        task_id: str,
        user_id: str | None = None
    ) -> TaskStatusResponse:
        """Get the current status of a generation task.

        Args:
            task_id: The task ID to check
            user_id: Optional user ID to verify ownership

        Returns:
            Current task status

        Raises:
            TaskNotFoundError: If task does not exist or not owned by user
        """
        logger.debug(f"[Controller] Getting task status: {task_id}")

        task = self.repository.get_task(task_id, user_id=user_id)

        if not task:
            raise TaskNotFoundError(task_id)

        return TaskStatusResponse(
            task_id=task["_id"],
            status=task["status"],
            message=task["message"],
            result=task.get("result"),
            error=task.get("error"),
            created_at=task["created_at"],
            completed_at=task.get("completed_at")
        )

    def get_trainings_list(
        self,
        limit: int = 10,
        offset: int = 0,
        user_id: str | None = None
    ) -> TrainingListResponse:
        """Get paginated list of training plans.

        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip
            user_id: Optional user ID to filter trainings by owner

        Returns:
            Paginated list of training plan summaries
        """
        logger.info(
            f"[Controller] Getting trainings list: "
            f"limit={limit}, offset={offset}, user_id={user_id}"
        )

        data = self.repository.get_trainings_list(
            limit=limit,
            offset=offset,
            user_id=user_id
        )

        trainings = [
            TrainingListItem(
                id=t["id"],
                created_at=t["created_at"],
                difficulty=t.get("difficulty"),
                training_dates=t.get("training_dates", []),
                trainings_count=t.get("trainings_count", 0),
            )
            for t in data["trainings"]
        ]

        return TrainingListResponse(
            total=data["total"],
            trainings=trainings
        )

    def get_training_by_id(
        self,
        training_id: str,
        user_id: str | None = None
    ) -> TrainingPlanResponse:
        """Get a saved training plan by ID.

        Args:
            training_id: The training plan ID
            user_id: Optional user ID to verify ownership

        Returns:
            Complete training plan

        Raises:
            TrainingNotFoundError: If training does not exist or not owned by user
        """
        logger.info(f"[Controller] Getting training: {training_id}")

        training = self.repository.get_training_by_id(
            training_id,
            user_id=user_id
        )

        if not training:
            raise TrainingNotFoundError(training_id)

        return TrainingPlanResponse(
            id=training["_id"],
            trainings=training.get("trainings", []),
            created_at=training.get("created_at", datetime.now())
        )

    def get_exercise_suggestions(
        self,
        training_id: str,
        request: ExerciseSuggestionsRequest,
        user_id: str | None = None,
    ) -> ExerciseSuggestionsResponse:
        """Return replacement suggestions for one exercise."""
        training_day = self.repository.get_training_day(
            training_id=training_id,
            day=request.day,
            user_id=user_id,
        )
        if not training_day:
            raise TrainingNotFoundError(training_id)

        exercises = training_day.get("exercises", [])
        if request.exercise_index < 0 or request.exercise_index >= len(exercises):
            raise InvalidExerciseReplaceError("exercise_index is out of range for selected day")

        current_exercise = exercises[request.exercise_index]
        suggestions = self.service.suggest_exercise_replacements(
            current_exercise=current_exercise,
            body_parts=training_day.get("body_parts", []),
            mode=request.mode,
            query=request.query,
            limit=request.limit,
            refresh_seed=request.refresh_seed,
            user_id=user_id,
        )
        return ExerciseSuggestionsResponse(**suggestions)

    def replace_exercise(
        self,
        training_id: str,
        request: ReplaceExerciseRequest,
        user_id: str | None = None,
    ) -> ReplaceExerciseResponse:
        """Replace one exercise in selected training day."""
        training_day = self.repository.get_training_day(
            training_id=training_id,
            day=request.day,
            user_id=user_id,
        )
        if not training_day:
            raise TrainingNotFoundError(training_id)

        exercises = training_day.get("exercises", [])
        if request.exercise_index < 0 or request.exercise_index >= len(exercises):
            raise InvalidExerciseReplaceError("exercise_index is out of range for selected day")

        difficulty = training_day.get("difficulty", "Intermediate")
        replacement = self.service.build_replacement_exercise(
            replacement_exercise_id=request.replacement_exercise_id,
            difficulty=difficulty,
        )
        updated_time_required = max(6, len(exercises) * 6)

        update_result = self.repository.replace_training_day_exercise(
            training_id=training_id,
            day=request.day,
            exercise_index=request.exercise_index,
            exercise=replacement,
            time_required=updated_time_required,
            user_id=user_id,
        )
        if not update_result:
            raise InvalidExerciseReplaceError("Failed to replace exercise for selected day")

        return ReplaceExerciseResponse(
            training_id=training_id,
            day=request.day,
            exercise_index=request.exercise_index,
            exercise=update_result["exercise"],
            timeRequired=update_result["time_required"],
            updated_at=update_result["updated_at"],
        )

    def get_training_progress(
        self,
        training_id: str,
        day: str,
        user_id: str,
    ) -> TrainingProgressResponse:
        """Return progress state for selected training day."""
        payload = self.service.get_progress_for_day(
            training_id=training_id,
            day=day,
            user_id=user_id,
            training_repository=self.repository,
        )
        return TrainingProgressResponse(**payload)

    def complete_exercise(
        self,
        training_id: str,
        request: CompleteExerciseRequest,
        user_id: str,
    ) -> MarkExerciseStatusResponse:
        """Persist one-way completion for selected exercise."""
        payload = self.service.complete_exercise_for_day(
            training_id=training_id,
            day=request.day,
            exercise_index=request.exercise_index,
            user_id=user_id,
            training_repository=self.repository,
        )
        return MarkExerciseStatusResponse(**payload)

    def mark_exercise_not_completed(
        self,
        training_id: str,
        request: MarkExerciseNotCompletedRequest,
        user_id: str,
    ) -> MarkExerciseStatusResponse:
        """Persist one-way not-completed status for selected exercise."""
        payload = self.service.mark_exercise_not_completed_for_day(
            training_id=training_id,
            day=request.day,
            exercise_index=request.exercise_index,
            reason_code=request.reason_code,
            reason_text=request.reason_text,
            user_id=user_id,
            training_repository=self.repository,
        )
        return MarkExerciseStatusResponse(**payload)

    def upsert_exercise_opinion(
        self,
        exercise_id: int,
        request: UpsertExerciseOpinionRequest,
        user_id: str,
    ) -> ExerciseOpinionResponse:
        """Upsert opinion snapshot and append history event."""
        payload = self.service.upsert_exercise_opinion(
            user_id=user_id,
            exercise_id=exercise_id,
            rating=request.rating,
            opinion=request.opinion,
        )
        return ExerciseOpinionResponse(
            exercise_id=payload["exercise_id"],
            rating=payload["rating"],
            opinion=payload.get("opinion", ""),
            updated_at=payload["updated_at"],
        )

    def get_exercise_opinion(
        self,
        exercise_id: int,
        user_id: str,
    ) -> ExerciseOpinionResponse:
        """Get current snapshot opinion for selected exercise."""
        payload = self.service.get_exercise_opinion(
            user_id=user_id,
            exercise_id=exercise_id,
        )
        if not payload:
            raise ExerciseOpinionNotFoundError(exercise_id)

        return ExerciseOpinionResponse(
            exercise_id=payload["exercise_id"],
            rating=payload["rating"],
            opinion=payload.get("opinion", ""),
            updated_at=payload["updated_at"],
        )


# Singleton instance for dependency injection
_controller_instance: TrainingController | None = None


def get_training_controller() -> TrainingController:
    """Get the training controller singleton.

    Returns:
        TrainingController instance
    """
    global _controller_instance
    if _controller_instance is None:
        _controller_instance = TrainingController()
    return _controller_instance
