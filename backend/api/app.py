"""FastAPI application configuration and setup.

Main application entry point with middleware, exception handlers,
and route registration.
"""

import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from api.exceptions.handlers import (
    ExerciseAlreadyCompletedError,
    ExerciseOpinionNotFoundError,
    ExerciseStatusAlreadyFinalizedError,
    ExerciseTrackingNotAllowedError,
    TaskNotFoundError,
    TrainingConflictError,
    TrainingDateDuplicateError,
    InvalidExerciseReplaceError,
    TrainingNotFoundError,
    TrainingGenerationError,
    exercise_already_completed_error_handler,
    exercise_opinion_not_found_error_handler,
    exercise_status_already_finalized_error_handler,
    exercise_tracking_not_allowed_error_handler,
    generic_exception_handler,
    training_conflict_error_handler,
    training_date_duplicate_error_handler,
    invalid_exercise_replace_error_handler,
    task_not_found_handler,
    training_not_found_handler,
    training_generation_error_handler,
    validation_exception_handler,
)
from api.schemas.responses import HealthCheckResponse
from database.mongodb import ensure_training_indexes
from api.views.exercise_opinions import router as exercise_opinions_router
from api.views.trainings import router as trainings_router
from api.views.media import router as media_router
from api.views.auth import router as auth_router

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# API version
API_VERSION = "1.0.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler.

    Handles startup and shutdown events.

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("=" * 50)
    logger.info("AI Personal Trainer API starting...")
    logger.info(f"Version: {API_VERSION}")
    logger.info("=" * 50)
    try:
        ensure_training_indexes()
        logger.info("Training indexes ensured")
    except Exception as exc:
        logger.warning(f"Failed to ensure indexes at startup: {exc}")
    yield
    # Shutdown
    logger.info("AI Personal Trainer API shutting down...")


# Create FastAPI application
app = FastAPI(
    title="AI Personal Trainer API",
    description="""
## API for generating personalized training plans

This application uses artificial intelligence to create
weekly training plans tailored to individual user needs.

### Features

* **Plan generation** - Automatic creation of training schedules
* **Exercise selection** - Intelligent exercise selection from MuscleWiki database
* **Asynchronous processing** - Background generation without blocking

### Workflow

1. Send a POST request to `/api/v1/trainings`
2. You will receive a `task_id` to track progress
3. Poll `/api/v1/trainings/tasks/{task_id}` for status
4. When completed, retrieve the plan from `/api/v1/trainings/{training_id}`

### Technologies

* **LangChain** - AI agent orchestration
* **Google Gemini** - Language model
* **MuscleWiki API** - Exercise database
* **MongoDB** - Plan storage
    """,
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
# Open CORS policy for all origins and keep credentials enabled.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(TrainingNotFoundError, training_not_found_handler)
app.add_exception_handler(TaskNotFoundError, task_not_found_handler)
app.add_exception_handler(TrainingGenerationError, training_generation_error_handler)
app.add_exception_handler(TrainingConflictError, training_conflict_error_handler)
app.add_exception_handler(TrainingDateDuplicateError, training_date_duplicate_error_handler)
app.add_exception_handler(InvalidExerciseReplaceError, invalid_exercise_replace_error_handler)
app.add_exception_handler(ExerciseAlreadyCompletedError, exercise_already_completed_error_handler)
app.add_exception_handler(
    ExerciseStatusAlreadyFinalizedError,
    exercise_status_already_finalized_error_handler,
)
app.add_exception_handler(ExerciseTrackingNotAllowedError, exercise_tracking_not_allowed_error_handler)
app.add_exception_handler(ExerciseOpinionNotFoundError, exercise_opinion_not_found_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(trainings_router, prefix="/api/v1")
app.include_router(exercise_opinions_router, prefix="/api/v1")
app.include_router(media_router, prefix="/api/v1")


@app.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["System"],
    summary="Check service health",
    description="Endpoint to verify the service is running correctly.",
)
async def health_check() -> HealthCheckResponse:
    """Health check endpoint.

    Returns:
        Service health status
    """
    return HealthCheckResponse(
        status="healthy",
        version=API_VERSION
    )


@app.get(
    "/",
    tags=["System"],
    summary="API home page",
    description="Redirects to Swagger documentation.",
    include_in_schema=False,
)
async def root():
    """Root endpoint with API information.

    Returns:
        Basic API info and documentation links
    """
    return {
        "name": "AI Personal Trainer API",
        "version": API_VERSION,
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        },
        "endpoints": {
            "health": "/health",
            "auth": "/api/v1/auth",
            "trainings": "/api/v1/trainings"
        }
    }
