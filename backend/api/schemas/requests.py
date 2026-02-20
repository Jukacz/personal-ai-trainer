"""Request schemas for API endpoints."""

from datetime import date, timedelta
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

DayOfWeek = Literal[
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]

ExerciseSuggestionMode = Literal["ai", "manual"]


class CreateTrainingRequest(BaseModel):
    """Request body for creating a new training plan.

    All fields are optional and have default values based on
    a typical training client profile.
    """

    age: Optional[int] = Field(
        default=19,
        description="Client's age in years",
        ge=16,
        le=100
    )
    weight: Optional[float] = Field(
        default=102.0,
        description="Current weight in kg",
        gt=30.0,
        le=300.0
    )
    target_weight: Optional[float] = Field(
        default=80.0,
        description="Target weight in kg",
        gt=30.0,
        le=300.0
    )
    difficulty: Optional[Literal["Novice", "Intermediate", "Advanced"]] = Field(
        default="Intermediate",
        description="Training difficulty level"
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Planning window start date (YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )
    end_date: Optional[str] = Field(
        default=None,
        description="Planning window end date (YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )
    trainings_per_week: Optional[int] = Field(
        default=None,
        description="Number of trainings per calendar week",
        ge=1,
        le=6,
    )
    selected_days: list[DayOfWeek] = Field(
        default_factory=lambda: ["monday", "thursday", "saturday"],
        description="Selected training days in a week",
        min_length=1,
        max_length=6,
    )
    overwrite_conflicts: bool = Field(
        default=False,
        description="Whether to overwrite existing trainings that conflict by date"
    )
    conflict_dates: list[str] = Field(
        default_factory=list,
        description="ISO dates selected for overwrite when conflicts were confirmed"
    )

    @field_validator("selected_days")
    @classmethod
    def validate_selected_days_unique(cls, value: list[DayOfWeek]) -> list[DayOfWeek]:
        """Validate that selected days are unique."""
        if len(set(value)) != len(value):
            raise ValueError("selected_days must not contain duplicates")
        return value

    @staticmethod
    def _default_range() -> tuple[str, str]:
        today = date.today()
        days_until_next_monday = (7 - today.weekday()) % 7
        if days_until_next_monday == 0:
            days_until_next_monday = 7
        next_monday = today + timedelta(days=days_until_next_monday)
        next_sunday = next_monday + timedelta(days=6)
        return next_monday.isoformat(), next_sunday.isoformat()

    @model_validator(mode="after")
    def validate_range_and_weekly_lock(self) -> "CreateTrainingRequest":
        """Validate planning range and weekly lock rule."""
        if self.trainings_per_week is None:
            self.trainings_per_week = len(self.selected_days)

        if self.start_date is None and self.end_date is None:
            default_start, default_end = self._default_range()
            self.start_date = default_start
            self.end_date = default_end
        elif self.start_date is None or self.end_date is None:
            raise ValueError("start_date and end_date must be both provided")

        if len(self.selected_days) != self.trainings_per_week:
            raise ValueError("selected_days count must match trainings_per_week")

        parsed_start = date.fromisoformat(self.start_date)
        parsed_end = date.fromisoformat(self.end_date)
        if parsed_start > parsed_end:
            raise ValueError("start_date must be earlier than or equal to end_date")

        return self

    class Config:
        json_schema_extra = {
            "example": {
                "age": 19,
                "weight": 102.0,
                "target_weight": 80.0,
                "difficulty": "Intermediate",
                "start_date": "2026-02-23",
                "end_date": "2026-03-08",
                "trainings_per_week": 3,
                "selected_days": ["monday", "thursday", "saturday"],
                "overwrite_conflicts": False,
                "conflict_dates": [],
            }
        }


class TrainingConflictsRequest(BaseModel):
    """Request body for checking date conflicts against existing trainings."""

    start_date: Optional[str] = Field(
        default=None,
        description="Planning window start date (YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )
    end_date: Optional[str] = Field(
        default=None,
        description="Planning window end date (YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )
    trainings_per_week: Optional[int] = Field(
        default=None,
        description="Number of trainings per calendar week",
        ge=1,
        le=6,
    )
    selected_days: list[DayOfWeek] = Field(
        ...,
        description="Selected training days in a week",
        min_length=1,
        max_length=6,
    )

    @field_validator("selected_days")
    @classmethod
    def validate_selected_days_unique(cls, value: list[DayOfWeek]) -> list[DayOfWeek]:
        """Validate that selected days are unique."""
        if len(set(value)) != len(value):
            raise ValueError("selected_days must not contain duplicates")
        return value

    @model_validator(mode="after")
    def validate_range_and_weekly_lock(self) -> "TrainingConflictsRequest":
        """Validate planning range and weekly lock rule."""
        if self.trainings_per_week is None:
            self.trainings_per_week = len(self.selected_days)

        if self.start_date is None and self.end_date is None:
            default_start, default_end = CreateTrainingRequest._default_range()
            self.start_date = default_start
            self.end_date = default_end
        elif self.start_date is None or self.end_date is None:
            raise ValueError("start_date and end_date must be both provided")

        if len(self.selected_days) != self.trainings_per_week:
            raise ValueError("selected_days count must match trainings_per_week")

        parsed_start = date.fromisoformat(self.start_date)
        parsed_end = date.fromisoformat(self.end_date)
        if parsed_start > parsed_end:
            raise ValueError("start_date must be earlier than or equal to end_date")

        return self


class CreateQuickTrainingRequest(BaseModel):
    """Request body for creating one quick training for today's date."""

    difficulty: Literal["Novice", "Intermediate", "Advanced"] = Field(
        default="Intermediate",
        description="Training difficulty level",
    )


class QuickTrainingConflictsRequest(BaseModel):
    """Request body for checking quick-training conflicts."""

    timezone: str = Field(
        default="Europe/Warsaw",
        description="Timezone used to resolve today's date",
        min_length=3,
        max_length=64,
    )


class ExerciseSuggestionsRequest(BaseModel):
    """Request body for replacement candidates."""

    day: str = Field(
        ...,
        description="Training ISO date",
        min_length=10,
        max_length=10,
    )
    exercise_index: int = Field(
        ...,
        description="Zero-based index of exercise in the training day",
        ge=0,
    )
    mode: ExerciseSuggestionMode = Field(
        ...,
        description="Suggestions mode: ai or manual",
    )
    query: Optional[str] = Field(
        default=None,
        description="Optional text query for manual suggestions",
        max_length=100,
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=50,
        description="Maximum number of suggestions to return",
    )
    refresh_seed: Optional[int] = Field(
        default=None,
        ge=0,
        description="Optional seed used to refresh and diversify suggestions",
    )


class ReplaceExerciseRequest(BaseModel):
    """Request body for replacing exercise in an existing plan."""

    day: str = Field(
        ...,
        description="Training ISO date",
        min_length=10,
        max_length=10,
    )
    exercise_index: int = Field(
        ...,
        description="Zero-based index of exercise in the training day",
        ge=0,
    )
    replacement_exercise_id: int = Field(
        ...,
        description="MuscleWiki exercise ID to use as replacement",
        ge=0,
    )


class CompleteExerciseRequest(BaseModel):
    """Request body for marking exercise as completed."""

    day: str = Field(
        ...,
        description="Training ISO date",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )
    exercise_index: int = Field(
        ...,
        description="Zero-based index of exercise in the training day",
        ge=0,
    )


NotCompletedReasonCode = Literal[
    "brak_czasu",
    "zbyt_trudne",
    "bol_dyskomfort",
    "brak_sprzetu",
    "brak_motywacji",
    "inne",
]


class MarkExerciseNotCompletedRequest(BaseModel):
    """Request body for marking exercise as not completed."""

    day: str = Field(
        ...,
        description="Training ISO date",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )
    exercise_index: int = Field(
        ...,
        description="Zero-based index of exercise in the training day",
        ge=0,
    )
    reason_code: NotCompletedReasonCode = Field(
        ...,
        description="Reason category code for not completed status",
    )
    reason_text: Optional[str] = Field(
        default="",
        description="Optional free-text reason",
        max_length=500,
    )


class UpsertExerciseOpinionRequest(BaseModel):
    """Request body for exercise opinion upsert."""

    rating: int = Field(
        ...,
        description="User rating from 1 to 5",
        ge=1,
        le=5,
    )
    opinion: Optional[str] = Field(
        default="",
        description="Optional user opinion text",
        max_length=500,
    )
