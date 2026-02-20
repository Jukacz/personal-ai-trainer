"""Shared test fixtures and configuration for the test suite.

Provides common mocks, test data, and FastAPI test client configuration
for all test modules in the project.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from pymongo.collection import Collection
from pymongo.database import Database


# ============================================================================
# FastAPI Test Client
# ============================================================================

@pytest.fixture
def test_client() -> TestClient:
    """Provide a FastAPI test client for integration tests.

    Returns:
        TestClient instance configured for testing the API
    """
    from api.app import app
    return TestClient(app)


# ============================================================================
# MongoDB Mocks
# ============================================================================

@pytest.fixture
def mock_mongo_client():
    """Mock MongoDB MongoClient instance.

    Returns:
        MagicMock configured as a MongoDB client
    """
    client = MagicMock()
    return client


@pytest.fixture
def mock_mongo_database(mock_mongo_client):
    """Mock MongoDB Database instance.

    Args:
        mock_mongo_client: Mocked MongoClient fixture

    Returns:
        MagicMock configured as a MongoDB database
    """
    db = MagicMock(spec=Database)
    mock_mongo_client.__getitem__.return_value = db
    return db


@pytest.fixture
def mock_tasks_collection(mock_mongo_database):
    """Mock MongoDB tasks collection.

    Args:
        mock_mongo_database: Mocked Database fixture

    Returns:
        MagicMock configured as a MongoDB collection
    """
    collection = MagicMock(spec=Collection)
    mock_mongo_database.__getitem__.return_value = collection
    return collection


@pytest.fixture
def mock_trainings_collection(mock_mongo_database):
    """Mock MongoDB trainings collection.

    Args:
        mock_mongo_database: Mocked Database fixture

    Returns:
        MagicMock configured as a MongoDB collection for trainings
    """
    collection = MagicMock(spec=Collection)
    return collection


# ============================================================================
# Repository Mocks
# ============================================================================

@pytest.fixture
def mock_training_repository():
    """Mock TrainingRepository for controller/view tests.

    Returns:
        MagicMock configured as a TrainingRepository instance
    """
    repo = MagicMock()

    # Configure default return values
    repo.create_task.return_value = "507f1f77bcf86cd799439011"
    repo.update_task_status.return_value = True
    repo.get_task.return_value = {
        "_id": "507f1f77bcf86cd799439011",
        "status": "pending",
        "message": "Task created",
        "result": None,
        "error": None,
        "created_at": datetime.now(timezone.utc),
        "completed_at": None,
    }
    repo.get_training_by_id.return_value = {
        "_id": "507f1f77bcf86cd799439012",
        "trainings": [],
        "createdAt": datetime.now(timezone.utc),
    }
    repo.save_training_plan.return_value = "507f1f77bcf86cd799439012"
    repo.get_trainings_list.return_value = {
        "total": 0,
        "trainings": [],
    }
    repo.get_training_calendar_days.return_value = ([], [])
    repo.get_conflicts_for_dates.return_value = []
    repo.remove_conflicting_days.return_value = 0

    return repo


@pytest.fixture
def mock_user_repository():
    """Mock UserRepository for authentication tests.

    Returns:
        MagicMock configured as a UserRepository instance
    """
    repo = MagicMock()
    return repo


# ============================================================================
# Service Mocks
# ============================================================================

@pytest.fixture
def mock_training_service():
    """Mock TrainingService for controller tests.

    Returns:
        MagicMock configured as a TrainingService instance
    """
    service = MagicMock()

    # Configure default return value for training plan generation
    service.generate_training_plan.return_value = {
        "trainings": [
            {
                "day": "2024-01-15",
                "name": "Test Training",
                "timeRequired": 60,
                "exercises": [
                    {
                        "name": "Test Exercise",
                        "videos": [{"url": "https://example.com/video.mp4", "angle": "side"}],
                        "repetitions": "3 x 10",
                        "steps": ["Step 1", "Step 2"],
                    }
                ],
            }
        ],
        "difficulty": "Intermediate",
    }
    service.get_upcoming_training_dates.return_value = ["2024-01-15", "2024-01-18", "2024-01-20"]
    service.get_dashboard_stats.return_value = {
        "kpis": {
            "scheduled_trainings": 0,
            "completed_exercises_percent": 0,
            "not_completed_exercises": 0,
            "most_active_weekday": "Brak danych",
        },
        "training_trend": [],
        "status_distribution": [
            {"status": "completed", "value": 0},
            {"status": "not_completed", "value": 0},
            {"status": "pending", "value": 0},
        ],
        "weekday_distribution": [
            {"weekday": "Pon", "count": 0},
            {"weekday": "Wt", "count": 0},
            {"weekday": "Śr", "count": 0},
            {"weekday": "Czw", "count": 0},
            {"weekday": "Pt", "count": 0},
            {"weekday": "Sob", "count": 0},
            {"weekday": "Ndz", "count": 0},
        ],
    }

    return service


@pytest.fixture
def mock_google_oauth_service():
    """Mock GoogleOAuthService for authentication tests.

    Returns:
        MagicMock configured as a GoogleOAuthService instance
    """
    service = MagicMock()
    return service


# ============================================================================
# Agent Mocks
# ============================================================================

@pytest.fixture
def mock_planner_agent():
    """Mock planner agent for service tests.

    Returns:
        MagicMock configured as a planner agent
    """
    agent = MagicMock()

    # Configure default return value
    from schemas.models import WeekPlan, TrainingDay

    week_plan = MagicMock(spec=WeekPlan)
    week_plan.weekStart = "2024-01-15"
    week_plan.weekEnd = "2024-01-21"
    week_plan.trainings = [
        MagicMock(
            spec=TrainingDay,
            day="2024-01-15",
            name="Back Day",
            bodyParts=["back", "biceps"]
        )
    ]

    agent.invoke.return_value = week_plan
    return agent


@pytest.fixture
def mock_exercise_agent():
    """Mock exercise agent for service tests.

    Returns:
        MagicMock configured as an exercise agent
    """
    agent = MagicMock()

    # Configure default return value (JSON string)
    agent.return_value = """{
        "day": "2024-01-15",
        "name": "Back Training",
        "timeRequired": 60,
        "exercises": [
            {
                "name": "Lat Pulldown",
                "videos": [{"url": "https://example.com/video.mp4", "angle": "side"}],
                "repetitions": "3 x 12",
                "steps": ["Step 1", "Step 2"]
            }
        ]
    }"""

    return agent


# ============================================================================
# Authentication Mocks
# ============================================================================

@pytest.fixture
def mock_current_user():
    """Provide a mock authenticated user.

    Returns:
        Dictionary representing an authenticated user
    """
    return {
        "_id": "507f1f77bcf86cd799439099",
        "email": "test@example.com",
        "name": "Test User",
    }


@pytest.fixture
def mock_get_current_user(mock_current_user):
    """Mock the get_current_user dependency.

    Args:
        mock_current_user: Mock user fixture

    Returns:
        MagicMock configured to return mock user
    """
    return MagicMock(return_value=mock_current_user)


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def valid_create_training_request():
    """Provide valid training creation request data.

    Returns:
        Dictionary with valid training request parameters
    """
    return {
        "age": 30,
        "weight": 80.0,
        "target_weight": 75.0,
        "difficulty": "Intermediate",
        "selected_days": ["monday", "thursday", "saturday"],
    }


@pytest.fixture
def minimal_create_training_request():
    """Provide minimal training creation request (all defaults).

    Returns:
        Dictionary with minimal training request parameters
    """
    return {}


@pytest.fixture
def sample_task_document():
    """Provide a sample task document from MongoDB.

    Returns:
        Dictionary representing a training task
    """
    return {
        "_id": "507f1f77bcf86cd799439011",
        "status": "pending",
        "message": "Training plan generation task has been created",
        "result": None,
        "error": None,
        "created_at": datetime.now(timezone.utc),
        "completed_at": None,
        "user_id": "507f1f77bcf86cd799439099",
    }


@pytest.fixture
def sample_completed_task_document():
    """Provide a sample completed task document.

    Returns:
        Dictionary representing a completed training task
    """
    completed_at = datetime.now(timezone.utc)
    return {
        "_id": "507f1f77bcf86cd799439011",
        "status": "completed",
        "message": "Training plan has been generated successfully",
        "result": {
            "training_id": "507f1f77bcf86cd799439012",
            "trainings": [
                {
                    "day": "2024-01-15",
                    "name": "Back and Biceps",
                    "timeRequired": 60,
                    "exercises": [],
                }
            ],
        },
        "error": None,
        "created_at": datetime.now(timezone.utc),
        "completed_at": completed_at,
        "user_id": "507f1f77bcf86cd799439099",
    }


@pytest.fixture
def sample_failed_task_document():
    """Provide a sample failed task document.

    Returns:
        Dictionary representing a failed training task
    """
    return {
        "_id": "507f1f77bcf86cd799439011",
        "status": "failed",
        "message": "Training plan generation failed",
        "result": None,
        "error": "Failed to generate weekly plan: API error",
        "created_at": datetime.now(timezone.utc),
        "completed_at": datetime.now(timezone.utc),
        "user_id": "507f1f77bcf86cd799439099",
    }


@pytest.fixture
def sample_training_document():
    """Provide a sample training plan document from MongoDB.

    Returns:
        Dictionary representing a saved training plan
    """
    return {
        "_id": "507f1f77bcf86cd799439012",
        "trainings": [
            {
                "day": "2024-01-15",
                "name": "Back and Biceps",
                "timeRequired": 60,
                "exercises": [
                    {
                        "name": "Lat Pulldown",
                        "videos": [
                            {
                                "url": "https://example.com/video1.mp4",
                                "angle": "side",
                            }
                        ],
                        "repetitions": "3 x 12",
                        "steps": ["Sit down", "Pull down"],
                    }
                ],
            }
        ],
        "difficulty": "Intermediate",
        "createdAt": datetime.now(timezone.utc),
        "user_id": "507f1f77bcf86cd799439099",
    }


@pytest.fixture
def sample_training_list():
    """Provide sample training list data.

    Returns:
        Dictionary with paginated training list
    """
    return {
        "total": 5,
        "trainings": [
            {
                "id": "507f1f77bcf86cd799439012",
                "created_at": datetime.now(timezone.utc),
                "difficulty": "Intermediate",
                "training_dates": ["2024-01-15", "2024-01-18"],
                "trainings_count": 2,
            },
            {
                "id": "507f1f77bcf86cd799439013",
                "created_at": datetime.now(timezone.utc),
                "difficulty": "Advanced",
                "training_dates": ["2024-01-16", "2024-01-19"],
                "trainings_count": 2,
            },
        ],
    }


# ============================================================================
# Patching Fixtures
# ============================================================================

@pytest.fixture
def patch_get_training_repository(mock_training_repository):
    """Patch the get_training_repository function.

    Args:
        mock_training_repository: Mock repository fixture

    Yields:
        Patch context for training repository
    """
    with patch(
        "api.controllers.training_controller.get_training_repository",
        return_value=mock_training_repository,
    ):
        yield mock_training_repository


@pytest.fixture
def patch_get_training_service(mock_training_service):
    """Patch the get_training_service function.

    Args:
        mock_training_service: Mock service fixture

    Yields:
        Patch context for training service
    """
    with patch(
        "api.controllers.training_controller.get_training_service",
        return_value=mock_training_service,
    ):
        yield mock_training_service


@pytest.fixture
def patch_mongodb_client(mock_mongo_client):
    """Patch the get_client function from database.mongodb.

    Args:
        mock_mongo_client: Mock MongoDB client fixture

    Yields:
        Patch context for MongoDB client
    """
    with patch(
        "database.mongodb.get_client",
        return_value=mock_mongo_client,
    ):
        yield mock_mongo_client


@pytest.fixture
def patch_create_planner_agent(mock_planner_agent):
    """Patch the create_planner_agent function.

    Args:
        mock_planner_agent: Mock planner agent fixture

    Yields:
        Patch context for planner agent
    """
    with patch(
        "agents.planner_agent.create_planner_agent",
        return_value=mock_planner_agent,
    ):
        yield mock_planner_agent


@pytest.fixture
def patch_create_exercise_agent(mock_exercise_agent):
    """Patch the create_exercise_agent function.

    Args:
        mock_exercise_agent: Mock exercise agent fixture

    Yields:
        Patch context for exercise agent
    """
    with patch(
        "agents.exercise_agent.create_exercise_agent",
        return_value=mock_exercise_agent,
    ):
        yield mock_exercise_agent


# ============================================================================
# Parametrized Test Data
# ============================================================================

@pytest.fixture(params=[
    {"age": 16, "weight": 50.0, "target_weight": 45.0},
    {"age": 30, "weight": 80.0, "target_weight": 75.0},
    {"age": 65, "weight": 100.0, "target_weight": 90.0},
])
def various_ages(request):
    """Provide various age/weight combinations for parametrized tests.

    Yields:
        Dictionary with different age and weight values
    """
    return request.param


@pytest.fixture(params=["Novice", "Intermediate", "Advanced"])
def difficulty_levels(request):
    """Provide different difficulty levels for parametrized tests.

    Yields:
        String representing difficulty level
    """
    return request.param
