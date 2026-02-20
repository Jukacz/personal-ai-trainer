"""Exception handlers for FastAPI application.

Provides centralized error handling with user-facing messages.
"""

import logging
from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class TrainingNotFoundError(Exception):
    """Raised when a training plan is not found."""

    def __init__(self, training_id: str):
        self.training_id = training_id
        super().__init__(f"Training plan not found: {training_id}")


class TaskNotFoundError(Exception):
    """Raised when a task is not found."""

    def __init__(self, task_id: str):
        self.task_id = task_id
        super().__init__(f"Task not found: {task_id}")


class TrainingGenerationError(Exception):
    """Raised when training plan generation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class TrainingConflictError(Exception):
    """Raised when selected days conflict with existing trainings."""

    def __init__(self, message: str, conflicts: list[dict[str, str]]):
        self.message = message
        self.conflicts = conflicts
        super().__init__(message)


class TrainingDateDuplicateError(Exception):
    """Raised when more than one training exists for the same calendar date."""

    def __init__(self, duplicate_dates: list[str]):
        self.duplicate_dates = duplicate_dates
        message = "Duplicate training dates detected"
        super().__init__(message)


class InvalidExerciseReplaceError(Exception):
    """Raised when exercise replacement payload is invalid for a training day."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ExerciseAlreadyCompletedError(Exception):
    """Raised when exercise completion is persisted twice."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ExerciseStatusAlreadyFinalizedError(Exception):
    """Raised when exercise already has any final status."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ExerciseTrackingNotAllowedError(Exception):
    """Raised when tracking is attempted outside today's date."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ExerciseOpinionNotFoundError(Exception):
    """Raised when exercise opinion snapshot does not exist."""

    def __init__(self, exercise_id: int):
        self.exercise_id = exercise_id
        super().__init__(f"Exercise opinion not found: {exercise_id}")


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors.

    Transforms FastAPI validation errors into user-friendly messages.

    Args:
        request: The incoming request
        exc: The validation exception

    Returns:
        JSONResponse with error details
    """
    errors = exc.errors()
    error_messages = []

    for error in errors:
        field = " -> ".join(str(loc) for loc in error["loc"])
        error_type = error["type"]
        message = error.get("msg", "Invalid value")

        error_messages.append({
            "field": field,
            "message": message,
            "error_type": error_type
        })

    logger.warning(f"Validation error on {request.url.path}: {error_messages}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Invalid input data",
            "details": {"errors": error_messages}
        }
    )


async def training_not_found_handler(
    request: Request,
    exc: TrainingNotFoundError
) -> JSONResponse:
    """Handle training not found errors.

    Args:
        request: The incoming request
        exc: The exception

    Returns:
        JSONResponse with 404 status
    """
    logger.info(f"Training not found: {exc.training_id}")

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "NotFoundError",
            "message": f"Training plan with ID '{exc.training_id}' was not found",
            "details": {"training_id": exc.training_id}
        }
    )


async def task_not_found_handler(
    request: Request,
    exc: TaskNotFoundError
) -> JSONResponse:
    """Handle task not found errors.

    Args:
        request: The incoming request
        exc: The exception

    Returns:
        JSONResponse with 404 status
    """
    logger.info(f"Task not found: {exc.task_id}")

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "NotFoundError",
            "message": f"Task with ID '{exc.task_id}' was not found",
            "details": {"task_id": exc.task_id}
        }
    )


async def training_generation_error_handler(
    request: Request,
    exc: TrainingGenerationError
) -> JSONResponse:
    """Handle training generation errors.

    Args:
        request: The incoming request
        exc: The exception

    Returns:
        JSONResponse with 500 status
    """
    logger.error(f"Training generation error: {exc.message}", extra=exc.details)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "TrainingGenerationError",
            "message": exc.message,
            "details": exc.details
        }
    )


async def training_conflict_error_handler(
    request: Request,
    exc: TrainingConflictError
) -> JSONResponse:
    """Handle training date conflicts."""
    logger.info(f"Training conflicts detected: {len(exc.conflicts)}")

    conflict_dates = sorted({item["date"] for item in exc.conflicts})

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": "TrainingConflictError",
            "message": exc.message,
            "details": {
                "has_conflicts": True,
                "conflict_dates": conflict_dates,
                "conflicts": exc.conflicts,
            }
        }
    )


async def training_date_duplicate_error_handler(
    request: Request,
    exc: TrainingDateDuplicateError
) -> JSONResponse:
    """Handle duplicate training day dates."""
    logger.warning(f"Duplicate training dates detected: {exc.duplicate_dates}")

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": "TrainingDateDuplicateError",
            "message": "Duplicate training dates detected",
            "details": {
                "duplicate_dates": exc.duplicate_dates,
            }
        }
    )


async def invalid_exercise_replace_error_handler(
    request: Request,
    exc: InvalidExerciseReplaceError
) -> JSONResponse:
    """Handle invalid replacement constraints."""
    logger.info(f"Invalid exercise replacement request: {exc.message}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "InvalidExerciseReplaceError",
            "message": exc.message,
            "details": None,
        }
    )


async def exercise_already_completed_error_handler(
    request: Request,
    exc: ExerciseAlreadyCompletedError,
) -> JSONResponse:
    """Handle duplicate completion attempts."""
    logger.info(f"Exercise already completed: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": "ExerciseAlreadyCompletedError",
            "message": exc.message,
            "details": None,
        },
    )


async def exercise_status_already_finalized_error_handler(
    request: Request,
    exc: ExerciseStatusAlreadyFinalizedError,
) -> JSONResponse:
    """Handle duplicate final status attempts."""
    logger.info(f"Exercise status already finalized: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": "ExerciseStatusAlreadyFinalizedError",
            "message": exc.message,
            "details": None,
        },
    )


async def exercise_tracking_not_allowed_error_handler(
    request: Request,
    exc: ExerciseTrackingNotAllowedError,
) -> JSONResponse:
    """Handle completion attempts outside today's day window."""
    logger.info(f"Exercise tracking not allowed: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ExerciseTrackingNotAllowedError",
            "message": exc.message,
            "details": None,
        },
    )


async def exercise_opinion_not_found_error_handler(
    request: Request,
    exc: ExerciseOpinionNotFoundError,
) -> JSONResponse:
    """Handle missing opinion snapshot."""
    logger.info(f"Exercise opinion not found: {exc.exercise_id}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "NotFoundError",
            "message": f"Exercise opinion for '{exc.exercise_id}' was not found",
            "details": {"exercise_id": exc.exercise_id},
        },
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handle all uncaught exceptions.

    Logs the full exception for debugging but returns a generic
    user-friendly message.

    Args:
        request: The incoming request
        exc: The uncaught exception

    Returns:
        JSONResponse with 500 status and generic error message
    """
    logger.exception(
        f"Unhandled exception on {request.url.path}: {exc}",
        exc_info=exc
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected server error occurred. Please try again later.",
            "details": None
        }
    )
