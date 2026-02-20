"""Response schemas for API endpoints."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class CreateTrainingResponse(BaseModel):
    """Response returned when a training plan generation task is created.

    Returns immediately with a task_id that can be used to poll for status.
    """

    task_id: str = Field(description="Unique task identifier")
    status: str = Field(description="Task status", default="pending")
    message: str = Field(description="Status message")
    check_status_url: str = Field(description="URL to check task status")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "507f1f77bcf86cd799439011",
                "status": "pending",
                "message": "Training plan generation task has been created",
                "check_status_url": "/api/v1/trainings/tasks/507f1f77bcf86cd799439011"
            }
        }


class TaskResultResponse(BaseModel):
    """Reference payload returned for completed tasks."""

    training_id: str = Field(description="Reference to saved training plan")
    schema_version: int = Field(default=2, description="Result payload version")


class TaskStatusResponse(BaseModel):
    """Response containing the current status of a background task.

    Used for polling task completion and retrieving results.
    """

    task_id: str = Field(description="Unique task identifier")
    status: str = Field(description="Task status: pending, processing, completed, failed")
    message: str = Field(description="Status message")
    result: Optional[TaskResultResponse] = Field(
        default=None,
        description="Task result reference (available when status=completed)"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message (available when status=failed)"
    )
    created_at: datetime = Field(description="Task creation timestamp")
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Task completion timestamp"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "507f1f77bcf86cd799439011",
                "status": "completed",
                "message": "Training plan has been generated successfully",
                "result": {
                    "training_id": "507f1f77bcf86cd799439012",
                    "schema_version": 2
                },
                "error": None,
                "created_at": "2024-01-15T10:30:00Z",
                "completed_at": "2024-01-15T10:32:00Z"
            }
        }


class TrainingListItem(BaseModel):
    """Summary information for a training plan in list view."""

    id: str = Field(description="Training plan database ID")
    created_at: Optional[datetime] = Field(
        default=None,
        description="Plan creation timestamp"
    )
    difficulty: Optional[str] = Field(
        default=None,
        description="Training difficulty level"
    )
    training_dates: list[str] = Field(
        default_factory=list,
        description="List of training ISO dates in this plan"
    )
    trainings_count: int = Field(
        default=0,
        description="Number of training days in this plan"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439012",
                "created_at": "2024-01-15T10:32:00Z",
                "difficulty": "Intermediate",
                "training_dates": ["2024-01-15", "2024-01-17"],
                "trainings_count": 2
            }
        }


class TrainingListResponse(BaseModel):
    """Paginated list of training plan summaries."""

    total: int = Field(description="Total number of training plans")
    trainings: list[TrainingListItem] = Field(description="List of training summaries")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 25,
                "trainings": [
                    {
                        "id": "507f1f77bcf86cd799439012",
                        "created_at": "2024-01-15T10:32:00Z",
                        "difficulty": "Intermediate",
                        "training_dates": ["2024-01-15", "2024-01-17"],
                        "trainings_count": 2
                    },
                    {
                        "id": "507f1f77bcf86cd799439011",
                        "created_at": "2024-01-14T08:15:00Z",
                        "difficulty": "Novice",
                        "training_dates": ["2024-01-14", "2024-01-16"],
                        "trainings_count": 2
                    }
                ]
            }
        }


class TrainingConflictItemResponse(BaseModel):
    """Details of a single conflicting training day."""

    date: str = Field(description="Conflicting ISO training date")
    existing_training_id: str = Field(description="Existing training plan ID")
    existing_training_name: str = Field(description="Existing training day name")


class TrainingConflictsResponse(BaseModel):
    """Response with detected conflicts for selected days."""

    has_conflicts: bool = Field(description="Whether there are any date conflicts")
    conflict_dates: list[str] = Field(
        default_factory=list,
        description="List of conflicting ISO dates"
    )
    conflicts: list[TrainingConflictItemResponse] = Field(
        default_factory=list,
        description="Detailed conflict entries"
    )


class TrainingCalendarDayItemResponse(BaseModel):
    """Single calendar day entry with training reference."""

    date: str = Field(description="Training ISO date")
    training_id: str = Field(description="Training plan ID for this day")
    training_name: str = Field(description="Name of the training day")


class TrainingCalendarDaysResponse(BaseModel):
    """Calendar payload with all training days for the user."""

    days: list[TrainingCalendarDayItemResponse] = Field(
        default_factory=list,
        description="Flat list of calendar day entries"
    )


class TrainingStatsKpisResponse(BaseModel):
    """KPI summary for dashboard stats."""

    scheduled_trainings: int = Field(default=0, description="Number of scheduled training days in selected window")
    completed_exercises_percent: int = Field(
        default=0,
        description="Percentage of completed exercises among all exercises in selected window",
    )
    not_completed_exercises: int = Field(default=0, description="Number of not completed exercises")
    most_active_weekday: str = Field(default="Brak danych", description="Most active weekday label")


class TrainingTrendPointResponse(BaseModel):
    """Single trend point for one date."""

    date: str = Field(description="ISO date")
    count: int = Field(default=0, description="Number of scheduled trainings for this date")


class TrainingStatusDistributionPointResponse(BaseModel):
    """Exercise status distribution point."""

    status: str = Field(description='Status category: "completed", "not_completed", or "pending"')
    value: int = Field(default=0, description="Number of exercises in selected status")


class TrainingWeekdayDistributionPointResponse(BaseModel):
    """Weekday distribution point."""

    weekday: str = Field(description="Weekday label")
    count: int = Field(default=0, description="Number of trainings scheduled on this weekday")


class TrainingDashboardStatsResponse(BaseModel):
    """Dashboard analytics payload."""

    kpis: TrainingStatsKpisResponse = Field(description="Dashboard KPI summary")
    training_trend: list[TrainingTrendPointResponse] = Field(
        default_factory=list,
        description="Training count trend for selected date window",
    )
    status_distribution: list[TrainingStatusDistributionPointResponse] = Field(
        default_factory=list,
        description="Exercise status distribution for selected date window",
    )
    weekday_distribution: list[TrainingWeekdayDistributionPointResponse] = Field(
        default_factory=list,
        description="Training distribution by weekday",
    )


class VideoResponse(BaseModel):
    """Video information for an exercise."""

    url: str = Field(description="Video URL")
    angle: Optional[str] = Field(default=None, description="Recording angle")


class ExerciseResponse(BaseModel):
    """Single exercise with full details."""

    name: str = Field(description="Exercise name")
    exercise_id: int | None = Field(default=None, description="MuscleWiki exercise ID")
    primary_muscles: list[str] = Field(
        default_factory=list,
        description="Primary muscles for this exercise"
    )
    difficulty: Optional[str] = Field(default=None, description="Exercise difficulty")
    category: Optional[str] = Field(default=None, description="Exercise category")
    videos: list[VideoResponse] = Field(description="List of instructional videos")
    repetitions: str = Field(description="Sets x repetitions")
    steps: list[str] = Field(description="Exercise execution steps")


class TrainingDayResponse(BaseModel):
    """Complete training day with exercises."""

    day: str = Field(description="Training date")
    name: str = Field(description="Training name")
    timeRequired: int = Field(description="Estimated time in minutes")
    bodyParts: list[str] = Field(default_factory=list, description="Body parts for this day")
    exercises: list[ExerciseResponse] = Field(description="List of exercises")


class TrainingPlanResponse(BaseModel):
    """Complete training plan response."""

    id: str = Field(description="Training plan database ID")
    trainings: list[TrainingDayResponse] = Field(description="List of trainings")
    created_at: datetime = Field(description="Plan creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439012",
                "trainings": [
                    {
                        "day": "2024-01-15",
                        "name": "Back and Biceps",
                        "timeRequired": 48,
                        "exercises": [
                            {
                                "name": "Lat Pulldown",
                                "videos": [{"url": "https://example.com/video.mp4", "angle": "side"}],
                                "repetitions": "3 x 12",
                                "steps": ["Step 1", "Step 2"]
                            }
                        ]
                    }
                ],
                "created_at": "2024-01-15T10:32:00Z"
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response format."""

    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    details: Optional[dict[str, Any]] = Field(
        default=None,
        description="Additional error details"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid input data",
                "details": {"field": "age", "reason": "Value must be greater than 16"}
            }
        }


class ExerciseSuggestionItemResponse(BaseModel):
    """Single replacement candidate."""

    exercise_id: int = Field(description="MuscleWiki exercise ID")
    name: str = Field(description="Exercise name")
    primary_muscles: list[str] = Field(default_factory=list, description="Primary muscles")
    difficulty: Optional[str] = Field(default=None, description="Difficulty level")
    category: Optional[str] = Field(default=None, description="Exercise category")
    videos: list[VideoResponse] = Field(
        default_factory=list,
        description="Instructional videos for candidate"
    )
    repetitions: str = Field(description="Suggested sets x repetitions")
    steps: list[str] = Field(default_factory=list, description="Execution steps")


class ExerciseSuggestionsResponse(BaseModel):
    """Response with replacement candidates."""

    mode: str = Field(description="Suggestions mode")
    context_source: str = Field(
        description="Context source: exercise_primary_muscles, training_day_body_parts, random_top"
    )
    fallback_used: bool = Field(description="Whether fallback logic was used")
    suggestions: list[ExerciseSuggestionItemResponse] = Field(
        default_factory=list,
        description="List of suggested replacement exercises"
    )


class ExerciseOpinionResponse(BaseModel):
    """Snapshot opinion for user + exercise pair."""

    exercise_id: int = Field(description="MuscleWiki exercise ID")
    rating: int = Field(description="Rating from 1 to 5")
    opinion: str = Field(description="User feedback text")
    updated_at: datetime = Field(description="Last update timestamp")


class CompleteExerciseResponse(BaseModel):
    """Response returned after exercise completion."""

    training_id: str = Field(description="Training plan ID")
    day: str = Field(description="Training date")
    exercise_index: int = Field(description="Zero-based exercise index")
    exercise_id: int = Field(description="MuscleWiki exercise ID")
    status: str = Field(description='Final status: "completed" or "not_completed"')
    reason_code: str | None = Field(default=None, description="Reason code for not completed status")
    reason_text: str | None = Field(default=None, description="Optional reason text for not completed status")
    updated_at: datetime = Field(description="Status update timestamp")
    completed_at: datetime = Field(description="Completion timestamp")
    existing_opinion: ExerciseOpinionResponse | None = Field(
        default=None,
        description="Current opinion snapshot for this exercise, if exists",
    )


class MarkExerciseStatusResponse(BaseModel):
    """Response returned after persisting final exercise status."""

    training_id: str = Field(description="Training plan ID")
    day: str = Field(description="Training date")
    exercise_index: int = Field(description="Zero-based exercise index")
    exercise_id: int = Field(description="MuscleWiki exercise ID")
    status: str = Field(description='Final status: "completed" or "not_completed"')
    reason_code: str | None = Field(default=None, description="Reason code for not completed status")
    reason_text: str | None = Field(default=None, description="Optional reason text for not completed status")
    updated_at: datetime = Field(description="Status update timestamp")
    completed_at: datetime | None = Field(default=None, description="Completion timestamp when status is completed")
    existing_opinion: ExerciseOpinionResponse | None = Field(
        default=None,
        description="Current opinion snapshot for this exercise, if exists",
    )


class NotCompletedReasonResponse(BaseModel):
    """Reason payload for not-completed status."""

    reason_code: str = Field(description="Reason category code")
    reason_text: str = Field(description="Optional free-text reason")


class TrainingProgressResponse(BaseModel):
    """Progress state for selected training day."""

    day: str = Field(description="Training date")
    is_trackable_today: bool = Field(description="Whether tracking is enabled for this date")
    completed_exercise_indices: list[int] = Field(
        default_factory=list,
        description="Completed exercise indices",
    )
    not_completed_exercise_indices: list[int] = Field(
        default_factory=list,
        description="Not completed exercise indices",
    )
    not_completed_reasons_by_exercise_index: dict[str, NotCompletedReasonResponse] = Field(
        default_factory=dict,
        description="Reason map keyed by exercise_index string",
    )
    opinions_by_exercise_id: dict[str, ExerciseOpinionResponse] = Field(
        default_factory=dict,
        description="Opinion map keyed by exercise_id string",
    )


class ReplaceExerciseResponse(BaseModel):
    """Response returned after replacing exercise."""

    training_id: str = Field(description="Training plan database ID")
    day: str = Field(description="Training date")
    exercise_index: int = Field(description="Zero-based exercise index")
    exercise: ExerciseResponse = Field(description="Updated exercise payload")
    timeRequired: int = Field(description="Recalculated training day duration in minutes")
    updated_at: datetime = Field(description="Update timestamp")


class HealthCheckResponse(BaseModel):
    """Health check endpoint response."""

    status: str = Field(description="Service status")
    version: str = Field(description="API version")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0"
            }
        }
