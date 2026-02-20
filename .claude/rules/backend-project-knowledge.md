# AI Personal Trainer - Backend Project Knowledge

This document contains project-specific knowledge for backend development. The ai-backend-specialist agent should use this context when implementing features or fixing issues.

---

## Documentation Maintenance

**IMPORTANT: After making significant changes, ALWAYS update the project documentation:**

Update `README.md` (project root) when:
- Adding new API endpoints
- Changing API request/response schemas
- Adding new environment variables
- Modifying Docker configuration
- Changing project structure
- Adding new dependencies to `requirements.txt`

Update this file (`backend-project-knowledge.md`) when:
- Adding new architectural patterns
- Creating new database collections
- Changing naming conventions
- Adding new common tasks/workflows

---

## Architecture: View-Controller-Repository Pattern

The API uses a layered VCR architecture:

```
backend/
├── api/
│   ├── views/           # HTTP routes, request validation, response formatting
│   │   └── trainings.py # POST /trainings, GET /tasks/{id}, GET /{id}
│   ├── controllers/     # Business logic orchestration, task management
│   │   └── training_controller.py
│   ├── repositories/    # Data access, wraps database/mongodb.py
│   │   └── training_repository.py
│   ├── services/        # Agent orchestration, complex operations
│   │   └── training_service.py
│   ├── schemas/         # API-specific Pydantic models
│   │   ├── requests.py  # CreateTrainingRequest
│   │   └── responses.py # TaskStatusResponse, TrainingPlanResponse
│   ├── exceptions/      # Custom exception handlers
│   │   └── handlers.py
│   └── app.py           # FastAPI app configuration
├── agents/              # LangChain agents (planner + exercise)
├── database/            # MongoDB operations (mongodb.py)
├── schemas/             # Domain models (models.py)
├── prompts/             # Agent prompt templates
├── tools/               # MuscleWiki API integration
└── run_api.py           # Entry point
```

---

## Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Planner Agent | `agents/planner_agent.py` | Generates weekly plan with body parts |
| Exercise Agent | `agents/exercise_agent.py` | Fills exercises using MuscleWiki API |
| Domain Models | `schemas/models.py` | Training, WeekPlan, Exercise, TrainingDay |
| API Schemas | `api/schemas/` | Request/response DTOs |
| MongoDB | `database/mongodb.py` | Data persistence |

---

## API Patterns

### 1. Async Processing with BackgroundTasks

Training generation is a long-running operation (2-5 minutes). We use async task pattern:

```
POST /api/v1/trainings → 202 Accepted + task_id
     ↓
Client polls GET /api/v1/trainings/tasks/{task_id}
     ↓
Status: pending → processing → completed/failed
     ↓
When completed: result contains training plan
```

### 2. Task Storage (MongoDB collection: `training_tasks`)

```python
{
    "task_id": "uuid-string",
    "status": "pending|processing|completed|failed",
    "message": "Status message",
    "result": {...},       # When completed
    "error": "...",        # When failed
    "created_at": datetime,
    "completed_at": datetime
}
```

### 3. Response Language

All API messages are in English. The AI-generated training content (exercise names, steps) is in Polish as per user requirements.

---

## Naming Conventions

| Context | Convention | Examples |
|---------|------------|----------|
| API URLs | kebab-case | `/api/v1/trainings`, `/tasks/{task_id}` |
| Request fields | English snake_case | `age`, `weight`, `target_weight` |
| Code identifiers | English snake_case | `training_controller`, `create_task()` |
| Domain models | English PascalCase | `Training`, `WeekPlan`, `Exercise` |
| Collections | English snake_case | `trainings`, `training_tasks` |

---

## Database Collections

| Collection | Purpose | Key Fields |
|------------|---------|------------|
| `trainings` | Saved training plans | `trainings[]`, `createdAt` |
| `exercises` | Cached MuscleWiki exercises | `exercise_id`, `name`, `videos` |
| `training_tasks` | Async task tracking | `task_id`, `status`, `result` |

---

## Adding New Endpoints

Follow this implementation order:

1. **Schema** (`api/schemas/`)
   - Define request model in `requests.py`
   - Define response model in `responses.py`
   - Add descriptions in `Field()`

2. **Repository** (`api/repositories/`)
   - Add data access methods
   - Wrap existing `database/mongodb.py` functions

3. **Service** (`api/services/`)
   - Add business logic (agent orchestration, etc.)
   - Keep it independent from HTTP layer

4. **Controller** (`api/controllers/`)
   - Coordinate repository and service
   - Handle BackgroundTasks for async operations

5. **View** (`api/views/`)
   - Add route with decorators
   - Swagger documentation (summary, description)
   - Proper HTTP status codes

### Example Endpoint Definition

```python
@router.post(
    "",
    response_model=CreateTrainingResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create a new training plan",
    description="""
    Starts generating a new training plan.

    Generation is an asynchronous process...
    """,
    responses={
        202: {"description": "Task has been created"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def create_training(...):
    ...
```

---

## Environment Variables

| Variable | Purpose | Required |
|----------|---------|----------|
| `GOOGLE_API_KEY` | Gemini model access | Yes |
| `RAPIDAPI_KEY` | MuscleWiki API access | Yes |

MongoDB connection is configured in `database/mongodb.py`:
- URI: `mongodb://admin:password123@localhost:27017/?authSource=admin`
- Database: `personal_trainer`

---

## Running the API

```bash
# Start MongoDB
cd backend
docker-compose up -d

# Install dependencies
pip install -r requirements.txt

# Run API server
python run_api.py
```

Access points:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json
- Health check: http://localhost:8000/health

---

## Common Tasks

### Add a new training-related endpoint
1. Check if domain model exists in `schemas/models.py`
2. Add API schema in `api/schemas/`
3. Add repository method in `api/repositories/training_repository.py`
4. Add controller method in `api/controllers/training_controller.py`
5. Add route in `api/views/trainings.py`

### Add a new resource (e.g., users)
1. Create `api/views/users.py` with router
2. Create `api/controllers/user_controller.py`
3. Create `api/repositories/user_repository.py`
4. Register router in `api/app.py`
