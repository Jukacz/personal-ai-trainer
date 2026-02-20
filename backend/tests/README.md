# Backend Test Suite

Comprehensive test suite for the AI Personal Trainer backend API. Tests cover all layers of the application following the View-Controller-Repository architecture.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures for all tests
├── test_views/              # HTTP endpoint tests
│   └── test_trainings.py   # Training API routes
├── test_controllers/        # Business logic tests
│   └── test_training_controller.py
├── test_repositories/       # Data access layer tests
│   └── test_training_repository.py
├── test_services/           # Service/orchestration tests
│   └── test_training_service.py
└── test_agents/             # LangChain agent tests
    ├── test_planner_agent.py
    └── test_exercise_agent.py
```

## Running Tests

### Run All Tests
```bash
cd backend
pytest
```

### Run with Coverage Report
```bash
pytest --cov=api --cov=agents --cov=database --cov-report=html
```

### Run Specific Test File
```bash
pytest tests/test_views/test_trainings.py
```

### Run Specific Test Class
```bash
pytest tests/test_controllers/test_training_controller.py::TestCreateTrainingPlan
```

### Run Specific Test
```bash
pytest tests/test_views/test_trainings.py::TestCreateTrainingEndpoint::test_create_training_valid_request_returns_202
```

### Run Tests Matching Pattern
```bash
pytest -k "test_create" -v
```

### Run with Verbose Output
```bash
pytest -v
```

### Run with Markers
```bash
# Run only view tests
pytest -m views

# Run only unit tests
pytest -m unit

# Run all except asyncio tests
pytest -m "not asyncio"
```

## Test Coverage

### Views (HTTP Endpoints)
- `test_trainings.py` - Training API endpoints
  - Creating training plans (POST /trainings)
  - Getting task status (GET /trainings/tasks/{task_id})
  - Listing training plans (GET /trainings)
  - Getting specific training (GET /trainings/{training_id})
  - Health check endpoint

### Controllers (Business Logic)
- `test_training_controller.py` - Training controller
  - Task creation and background task scheduling
  - Training plan generation orchestration
  - Task status retrieval
  - Training list pagination
  - Error handling for generation failures

### Repositories (Data Access)
- `test_training_repository.py` - Training repository
  - Saving training plans to MongoDB
  - Retrieving training plans with pagination
  - Task creation and status updates
  - User-specific filtering
  - Error handling for invalid ObjectIds

### Services (AI Orchestration)
- `test_training_service.py` - Training service
  - Planner agent invocation
  - Exercise agent creation and invocation
  - JSON response parsing
  - Difficulty-specific instructions
  - Multi-step plan generation
  - Error handling from agents

### Agents (LangChain)
- `test_planner_agent.py` - Planner agent
  - Agent creation with various parameters
  - LLM initialization
  - Structured output configuration
  - Parameter validation

- `test_exercise_agent.py` - Exercise agent
  - Agent creation
  - Tool integration
  - Prompt handling
  - Response parsing

## Test Categories

### Unit Tests
Tests for individual components in isolation with mocked dependencies.

### Integration Tests
Tests that verify components work together (e.g., controller + mocked repository).

### Error Cases
Tests for error handling and edge cases:
- Invalid input validation
- Missing data (404 errors)
- Service failures
- Malformed JSON responses
- Invalid ObjectId formats

### Parametrized Tests
Tests that run with multiple parameter combinations:
- Various age groups (16, 30, 65)
- Different difficulty levels (Novice, Intermediate, Advanced)
- Edge case values for weight/target_weight

## Fixtures

Common fixtures are defined in `conftest.py`:

### MongoDB Mocks
- `mock_mongo_client` - MongoDB client mock
- `mock_mongo_database` - Database mock
- `mock_tasks_collection` - Tasks collection mock
- `mock_trainings_collection` - Trainings collection mock

### Repository Mocks
- `mock_training_repository` - Training repository with default values
- `mock_user_repository` - User repository mock

### Service Mocks
- `mock_training_service` - Training service mock
- `mock_google_oauth_service` - OAuth service mock

### Agent Mocks
- `mock_planner_agent` - Planner agent mock
- `mock_exercise_agent` - Exercise agent mock

### Authentication
- `mock_current_user` - Sample authenticated user
- `mock_get_current_user` - Dependency for get_current_user

### Test Data
- `valid_create_training_request` - Valid training request
- `sample_task_document` - Sample MongoDB task document
- `sample_completed_task_document` - Completed task document
- `sample_failed_task_document` - Failed task document
- `sample_training_document` - Training plan document
- `sample_training_list` - Paginated training list

### Patching Fixtures
These automatically patch dependencies:
- `patch_get_training_repository` - Patches training repository
- `patch_get_training_service` - Patches training service
- `patch_mongodb_client` - Patches MongoDB client
- `patch_create_planner_agent` - Patches planner agent
- `patch_create_exercise_agent` - Patches exercise agent

## Best Practices Used

1. **Isolation**: Each test is independent and can run in any order
2. **Mocking**: External dependencies (MongoDB, LangChain, APIs) are mocked
3. **Fixtures**: Reusable test data and mocks
4. **Clear Names**: Test names describe the scenario and expected outcome
5. **Single Assertion**: Each test focuses on one behavior
6. **Arrange-Act-Assert**: Tests follow clear structure
7. **Error Cases**: Both success and failure paths are tested
8. **Type Safety**: Mocks are configured with proper specs

## Coverage Goals

- **Views**: 95%+ coverage
- **Controllers**: 95%+ coverage
- **Repositories**: 90%+ coverage
- **Services**: 90%+ coverage
- **Agents**: 85%+ coverage

## Continuous Integration

Tests can be integrated into CI/CD pipelines:

```bash
# Check coverage
pytest --cov=api --cov-report=term-missing

# Fail if coverage below threshold
pytest --cov=api --cov-fail-under=85

# Generate JUnit XML for CI
pytest --junitxml=test-results.xml

# Generate coverage reports
pytest --cov=api --cov-report=html
pytest --cov=api --cov-report=xml
```

## Common Issues

### Import Errors
Ensure backend is in Python path:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

### MongoDB Connection Errors
All MongoDB operations are mocked. If tests fail due to connection:
1. Check that mocks are properly configured
2. Verify patch paths match import locations
3. Ensure fixtures are used in test signatures

### Async Test Failures
Tests using async code require `@pytest.mark.asyncio`:
```python
@pytest.mark.asyncio
async def test_async_operation():
    ...
```

## Performance

Most tests run in milliseconds due to mocking. Full suite should complete in under 10 seconds.

For profiling:
```bash
pytest --durations=10  # Show slowest 10 tests
```

## Debugging Tests

### Verbose Output
```bash
pytest -vv -s  # Very verbose + print statements
```

### Drop into Debugger
```python
def test_something():
    import pdb; pdb.set_trace()  # Will pause here
    ...
```

### Use pytest --pdb
```bash
pytest --pdb  # Drops to debugger on failure
```

## Adding New Tests

When adding new features:

1. Write tests following the same structure
2. Use existing fixtures from conftest.py
3. Mock external dependencies
4. Test both success and failure cases
5. Update README with new test descriptions
6. Ensure coverage doesn't decrease

Example test file structure:
```python
class TestFeatureName:
    """Tests for feature_name functionality."""

    def test_feature_happy_path(self, mock_dependency):
        """Test feature works correctly with valid input.

        Verifies expected behavior.
        """
        # Arrange
        expected = "result"

        # Act
        result = function_under_test(input)

        # Assert
        assert result == expected

    def test_feature_error_case(self, mock_dependency):
        """Test feature handles errors correctly.

        Verifies error handling.
        """
        mock_dependency.side_effect = ValueError("Error")

        with pytest.raises(ValueError):
            function_under_test(input)
```
