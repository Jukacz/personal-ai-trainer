"""Training routes - API endpoints for training plans.

Provides REST endpoints for creating, retrieving, and managing
AI-generated training plans. All endpoints require authentication.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status

from api.auth.dependencies import get_current_user
from api.controllers.training_controller import (
    TrainingController,
    get_training_controller,
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
)
from api.schemas.responses import (
    CreateTrainingResponse,
    ErrorResponse,
    ExerciseSuggestionsResponse,
    MarkExerciseStatusResponse,
    ReplaceExerciseResponse,
    TaskStatusResponse,
    TrainingDashboardStatsResponse,
    TrainingCalendarDaysResponse,
    TrainingConflictsResponse,
    TrainingListResponse,
    TrainingPlanResponse,
    TrainingProgressResponse,
)

router = APIRouter(
    prefix="/trainings",
    tags=["Trainings"],
)


@router.get(
    "",
    response_model=TrainingListResponse,
    summary="List training plans",
    description="""
Returns a paginated list of training plans owned by the authenticated user.

**Query parameters:**
- `limit`: Maximum number of results to return (default: 10, max: 100)
- `offset`: Number of results to skip for pagination (default: 0)

Results are sorted by creation date in descending order (newest first).
Each item includes the plan ID, creation timestamp, and difficulty level.

**Authorization:**
Requires Bearer token in Authorization header.
    """,
    responses={
        200: {
            "description": "List of training plans",
            "model": TrainingListResponse,
        },
        401: {
            "description": "Not authenticated",
            "model": ErrorResponse,
        },
    },
)
async def get_trainings_list(
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of results to return"
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Number of results to skip"
    ),
    user: dict = Depends(get_current_user),
    controller: TrainingController = Depends(get_training_controller),
) -> TrainingListResponse:
    """Get paginated list of training plans for the authenticated user.

    Args:
        limit: Maximum number of results
        offset: Number of results to skip
        user: Current authenticated user
        controller: Training controller instance

    Returns:
        Paginated list of training summaries
    """
    user_id = str(user["_id"])
    return controller.get_trainings_list(limit=limit, offset=offset, user_id=user_id)


@router.get(
    "/days",
    response_model=TrainingCalendarDaysResponse,
    summary="List training calendar days",
    description="""
Returns a flat list of training calendar days with `training_id` references.
Used by the dashboard calendar to render markers and resolve clicked days.
If duplicate entries exist for the same date, only the first entry is returned.
    """,
    responses={
        200: {
            "description": "Calendar days list",
            "model": TrainingCalendarDaysResponse,
        },
        401: {
            "description": "Not authenticated",
            "model": ErrorResponse,
        },
    },
)
async def get_training_calendar_days(
    user: dict = Depends(get_current_user),
    controller: TrainingController = Depends(get_training_controller),
) -> TrainingCalendarDaysResponse:
    """Get flat list of training days for calendar rendering."""
    user_id = str(user["_id"])
    return controller.get_training_calendar_days(user_id=user_id)


@router.get(
    "/stats",
    response_model=TrainingDashboardStatsResponse,
    summary="Get dashboard stats",
    description="""
Returns aggregated dashboard analytics for the authenticated user in selected date window.

**Query parameters:**
- `window_days`: Number of days in analytics window counting back from today (default: 30, min: 1, max: 365)
    """,
    responses={
        200: {
            "description": "Dashboard analytics payload",
            "model": TrainingDashboardStatsResponse,
        },
        401: {
            "description": "Not authenticated",
            "model": ErrorResponse,
        },
    },
)
async def get_training_dashboard_stats(
    window_days: int = Query(
        default=30,
        ge=1,
        le=365,
        description="Number of days in analytics window",
    ),
    user: dict = Depends(get_current_user),
    controller: TrainingController = Depends(get_training_controller),
) -> TrainingDashboardStatsResponse:
    """Get aggregated dashboard stats for selected date window."""
    user_id = str(user["_id"])
    return controller.get_dashboard_stats(user_id=user_id, window_days=window_days)


@router.post(
    "",
    response_model=CreateTrainingResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create a new training plan",
    description="""
Creates a new training plan generation task for the authenticated user.

Plan generation occurs asynchronously in the background. This endpoint returns
immediately with a task identifier (task_id) that can be used to check the
generation status.

**Generation process:**
1. Planner agent creates a weekly schedule with body parts
2. Exercise agent selects exercises from MuscleWiki API
3. Result is saved to the database and associated with the user

**Range planning behavior:**
- Trainings are generated only in selected `start_date`-`end_date` window
- Weekly frequency is controlled by `trainings_per_week`
- `selected_days` count must equal `trainings_per_week`

**Typical generation time:** 1-3 minutes

**Authorization:**
Requires Bearer token in Authorization header.
    """,
    responses={
        202: {
            "description": "Task has been created",
            "model": CreateTrainingResponse,
        },
        401: {
            "description": "Not authenticated",
            "model": ErrorResponse,
        },
        422: {
            "description": "Invalid input data",
            "model": ErrorResponse,
        },
        409: {
            "description": "Conflict with existing training dates",
            "model": ErrorResponse,
        },
    },
)
async def create_training_plan(
    request: CreateTrainingRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
    controller: TrainingController = Depends(get_training_controller),
) -> CreateTrainingResponse:
    """Create a new training plan generation task.

    Args:
        request: Training plan parameters
        background_tasks: FastAPI background task handler
        user: Current authenticated user
        controller: Training controller instance

    Returns:
        Task creation response with task_id
    """
    user_id = str(user["_id"])
    return controller.create_training_plan(request, background_tasks, user_id=user_id)


@router.post(
    "/conflicts",
    response_model=TrainingConflictsResponse,
    summary="Check selected day conflicts",
    description="""
Checks whether selected training days conflict with already saved training dates
for the authenticated user in the upcoming full week.
    """,
    responses={
        200: {
            "description": "Conflict check result",
            "model": TrainingConflictsResponse,
        },
        401: {
            "description": "Not authenticated",
            "model": ErrorResponse,
        },
        422: {
            "description": "Invalid input data",
            "model": ErrorResponse,
        },
    },
)
async def get_training_conflicts(
    request: TrainingConflictsRequest,
    user: dict = Depends(get_current_user),
    controller: TrainingController = Depends(get_training_controller),
) -> TrainingConflictsResponse:
    """Check conflicts for selected days."""
    user_id = str(user["_id"])
    return controller.get_training_conflicts(request, user_id=user_id)


@router.post(
    "/quick/conflicts",
    response_model=TrainingConflictsResponse,
    summary="Check quick training conflicts",
    description="""
Checks whether today's quick training conflicts with already saved training date
for the authenticated user.
    """,
    responses={
        200: {
            "description": "Conflict check result",
            "model": TrainingConflictsResponse,
        },
        401: {
            "description": "Not authenticated",
            "model": ErrorResponse,
        },
        422: {
            "description": "Invalid input data",
            "model": ErrorResponse,
        },
    },
)
async def get_quick_training_conflicts(
    request: QuickTrainingConflictsRequest,
    user: dict = Depends(get_current_user),
    controller: TrainingController = Depends(get_training_controller),
) -> TrainingConflictsResponse:
    """Check conflicts for quick training."""
    user_id = str(user["_id"])
    return controller.get_quick_training_conflicts(request, user_id=user_id)


@router.post(
    "/quick",
    response_model=CreateTrainingResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create quick training for today",
    responses={
        202: {
            "description": "Task has been created",
            "model": CreateTrainingResponse,
        },
        401: {
            "description": "Not authenticated",
            "model": ErrorResponse,
        },
        422: {
            "description": "Invalid input data",
            "model": ErrorResponse,
        },
        409: {
            "description": "Conflict with existing training date",
            "model": ErrorResponse,
        },
    },
)
async def create_quick_training(
    request: CreateQuickTrainingRequest,
    background_tasks: BackgroundTasks,
    overwrite_conflicts: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    controller: TrainingController = Depends(get_training_controller),
) -> CreateTrainingResponse:
    """Create quick one-day training generation task."""
    user_id = str(user["_id"])
    return controller.create_quick_training(
        request=request,
        background_tasks=background_tasks,
        user_id=user_id,
        overwrite_conflicts=overwrite_conflicts,
    )


@router.get(
    "/tasks/{task_id}",
    response_model=TaskStatusResponse,
    summary="Check task status",
    description="""
Returns the current status of a training plan generation task.

**Possible statuses:**
- `pending` - Task is waiting to be processed
- `processing` - Generation in progress
- `completed` - Plan has been generated successfully
- `failed` - An error occurred during generation

When status is `completed`, the `result` field contains a reference
(`training_id`) to retrieve the saved plan.

**Authorization:**
Requires Bearer token in Authorization header. Users can only access their own tasks.
    """,
    responses={
        200: {
            "description": "Task status",
            "model": TaskStatusResponse,
        },
        401: {
            "description": "Not authenticated",
            "model": ErrorResponse,
        },
        404: {
            "description": "Task not found",
            "model": ErrorResponse,
        },
    },
)
async def get_task_status(
    task_id: str,
    user: dict = Depends(get_current_user),
    controller: TrainingController = Depends(get_training_controller),
) -> TaskStatusResponse:
    """Get the current status of a generation task.

    Args:
        task_id: Unique task identifier
        user: Current authenticated user
        controller: Training controller instance

    Returns:
        Current task status
    """
    user_id = str(user["_id"])
    return controller.get_task_status(task_id, user_id=user_id)


@router.get(
    "/{training_id}",
    response_model=TrainingPlanResponse,
    summary="Get training plan",
    description="""
Returns a saved training plan by its identifier.

The plan contains complete information about trainings, including:
- Training dates
- Training names
- Estimated duration
- List of exercises with video instructions and execution steps

**Authorization:**
Requires Bearer token in Authorization header. Users can only access their own plans.
    """,
    responses={
        200: {
            "description": "Training plan",
            "model": TrainingPlanResponse,
        },
        401: {
            "description": "Not authenticated",
            "model": ErrorResponse,
        },
        404: {
            "description": "Plan not found",
            "model": ErrorResponse,
        },
    },
)
async def get_training_by_id(
    training_id: str,
    user: dict = Depends(get_current_user),
    controller: TrainingController = Depends(get_training_controller),
) -> TrainingPlanResponse:
    """Get a saved training plan by ID.

    Args:
        training_id: Training plan identifier
        user: Current authenticated user
        controller: Training controller instance

    Returns:
        Complete training plan
    """
    user_id = str(user["_id"])
    return controller.get_training_by_id(training_id, user_id=user_id)


@router.post(
    "/{training_id}/exercises/suggestions",
    response_model=ExerciseSuggestionsResponse,
    summary="Get exercise replacement suggestions",
    description="""
Returns replacement candidates for a selected exercise in a saved training plan.

Modes:
- `manual`: list candidates filtered by exercise primary muscles or training day body parts
- `ai`: returns top 3 AI-ranked candidates from the same candidate pool
    """,
    responses={
        200: {"description": "Suggestions list", "model": ExerciseSuggestionsResponse},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        404: {"description": "Training not found", "model": ErrorResponse},
        422: {"description": "Invalid request", "model": ErrorResponse},
    },
)
async def get_exercise_suggestions(
    training_id: str,
    request: ExerciseSuggestionsRequest,
    user: dict = Depends(get_current_user),
    controller: TrainingController = Depends(get_training_controller),
) -> ExerciseSuggestionsResponse:
    """Get exercise replacement suggestions for selected training day."""
    user_id = str(user["_id"])
    return controller.get_exercise_suggestions(training_id, request, user_id=user_id)


@router.patch(
    "/{training_id}/exercises/replace",
    response_model=ReplaceExerciseResponse,
    summary="Replace exercise in training day",
    description="""
Replaces one exercise in selected training day and recalculates day duration.

Replacement is persisted immediately and reflected in next training fetch.
    """,
    responses={
        200: {"description": "Exercise replaced", "model": ReplaceExerciseResponse},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        404: {"description": "Training not found", "model": ErrorResponse},
        422: {"description": "Invalid request", "model": ErrorResponse},
    },
)
async def replace_exercise(
    training_id: str,
    request: ReplaceExerciseRequest,
    user: dict = Depends(get_current_user),
    controller: TrainingController = Depends(get_training_controller),
) -> ReplaceExerciseResponse:
    """Replace selected exercise in training day."""
    user_id = str(user["_id"])
    return controller.replace_exercise(training_id, request, user_id=user_id)


@router.get(
    "/{training_id}/progress",
    response_model=TrainingProgressResponse,
    summary="Get training progress for selected day",
    responses={
        200: {"description": "Training progress", "model": TrainingProgressResponse},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        404: {"description": "Training not found", "model": ErrorResponse},
        422: {"description": "Invalid request", "model": ErrorResponse},
    },
)
async def get_training_progress(
    training_id: str,
    day: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    user: dict = Depends(get_current_user),
    controller: TrainingController = Depends(get_training_controller),
) -> TrainingProgressResponse:
    """Get completion and opinion state for selected day."""
    user_id = str(user["_id"])
    return controller.get_training_progress(training_id, day, user_id=user_id)


@router.post(
    "/{training_id}/exercises/complete",
    response_model=MarkExerciseStatusResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Mark exercise as completed",
    responses={
        201: {"description": "Exercise completion persisted", "model": MarkExerciseStatusResponse},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        404: {"description": "Training not found", "model": ErrorResponse},
        409: {"description": "Exercise status already finalized", "model": ErrorResponse},
        422: {"description": "Tracking not allowed or invalid request", "model": ErrorResponse},
    },
)
async def complete_exercise(
    training_id: str,
    request: CompleteExerciseRequest,
    user: dict = Depends(get_current_user),
    controller: TrainingController = Depends(get_training_controller),
) -> MarkExerciseStatusResponse:
    """Persist one-way completion for selected exercise."""
    user_id = str(user["_id"])
    return controller.complete_exercise(training_id, request, user_id=user_id)


@router.post(
    "/{training_id}/exercises/not-completed",
    response_model=MarkExerciseStatusResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Mark exercise as not completed",
    responses={
        201: {"description": "Exercise not-completed status persisted", "model": MarkExerciseStatusResponse},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        404: {"description": "Training not found", "model": ErrorResponse},
        409: {"description": "Exercise status already finalized", "model": ErrorResponse},
        422: {"description": "Tracking not allowed or invalid request", "model": ErrorResponse},
    },
)
async def mark_exercise_not_completed(
    training_id: str,
    request: MarkExerciseNotCompletedRequest,
    user: dict = Depends(get_current_user),
    controller: TrainingController = Depends(get_training_controller),
) -> MarkExerciseStatusResponse:
    """Persist one-way not-completed status for selected exercise."""
    user_id = str(user["_id"])
    return controller.mark_exercise_not_completed(training_id, request, user_id=user_id)
