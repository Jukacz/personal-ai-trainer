# AI Personal Trainer - Backend

FastAPI backend for the AI Personal Trainer application with AI-powered workout plan generation, user authentication, and MongoDB persistence.

## Tech Stack

- **Python 3.13** - Modern Python with latest features
- **FastAPI** - High-performance async web framework
- **LangChain** - AI agent orchestration
- **Google Gemini** - LLM for plan generation
- **MongoDB** - NoSQL database
- **JWT** - Token-based authentication
- **bcrypt** - Secure password hashing
- **MuscleWiki API** - Exercise database

## Features

- JWT-based authentication (access + refresh tokens)
- Google OAuth integration
- User profile management
- AI-powered training plan generation
- Background task processing
- Exercise data caching from MuscleWiki API
- User-scoped training plans
- RESTful API with OpenAPI documentation

## Getting Started

### Prerequisites

- Python 3.11+
- MongoDB (via Docker or local installation)
- Google API Key (for Gemini)
- RapidAPI Key (for MuscleWiki)
- dotenvx (optional)

### Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file or set environment variables:

```env
# Required
GOOGLE_API_KEY=your-google-api-key
RAPIDAPI_KEY=your-rapidapi-key
JWT_SECRET_KEY=your-secure-secret-key

# Optional (with defaults)
MONGODB_URI=mongodb://admin:password123@localhost:27017/?authSource=admin
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
CORS_ALLOWED_ORIGINS=http://localhost:3000
COOKIE_SECURE=false
AUTO_SEED_MOCK_DATA_ON_USER_CREATE=false
AUTO_SEED_MOCK_PLANS_PER_USER=4
AUTO_SEED_MOCK_MIN_DAYS_PER_PLAN=3
AUTO_SEED_MOCK_MAX_DAYS_PER_PLAN=4
AUTO_SEED_MOCK_EXERCISES_PER_DAY=4
AUTO_SEED_MOCK_NOT_COMPLETED_RATE=0.2
AUTO_SEED_MOCK_OPINION_RATE=0.55
AUTO_SEED_MOCK_START_DAYS_AGO=45
AUTO_SEED_MOCK_BASE_SEED=20260220
```

### Running

```bash
# Start MongoDB
docker-compose up -d

# Run API server
python run_api.py

# Run API server with dotenvx
dotenvx run -f .env -- python run_api.py

# Or with Makefile shortcuts
make run
make run-dotenvx

# Or with auto-reload
uvicorn api.app:app --reload --host 0.0.0.0 --port 8000

# Or auto-reload with dotenvx
dotenvx run -f .env -- uvicorn api.app:app --reload --host 0.0.0.0 --port 8000

# Or with Makefile shortcuts
make run-uvicorn
make run-uvicorn-dotenvx
```

API will be available at `http://localhost:8000`

## Utility Scripts

Seed mock training history and tracking stats for all users:

```bash
../.venv/bin/python scripts/seed_mock_data_for_users.py --execute

# With dotenvx
dotenvx run -f .env -- ../.venv/bin/python scripts/seed_mock_data_for_users.py --execute

# Or with Makefile shortcuts
make seed-mock
make seed-mock-dotenvx
```

Seed for one selected user:

```bash
../.venv/bin/python scripts/seed_mock_data_for_users.py --execute --user-id <mongo_user_id>
```

Enable automatic seed for newly created users:

```env
AUTO_SEED_MOCK_DATA_ON_USER_CREATE=true
```

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Project Structure

```
backend/
├── api/
│   ├── auth/                   # Authentication module
│   │   ├── dependencies.py     # FastAPI dependencies (get_current_user)
│   │   ├── jwt.py              # JWT token management
│   │   └── password.py         # bcrypt password hashing
│   ├── controllers/            # Business logic layer
│   │   ├── auth_controller.py  # Auth operations
│   │   └── training_controller.py
│   ├── repositories/           # Data access layer
│   │   ├── user_repository.py  # User CRUD
│   │   └── training_repository.py
│   ├── schemas/                # Pydantic models
│   │   ├── auth_requests.py    # Auth request DTOs
│   │   ├── auth_responses.py   # Auth response DTOs
│   │   ├── requests.py         # Training requests
│   │   └── responses.py        # Training responses
│   ├── services/               # External services
│   │   ├── google_oauth_service.py
│   │   └── training_service.py
│   ├── views/                  # API routes
│   │   ├── auth.py             # Auth endpoints
│   │   └── trainings.py        # Training endpoints
│   └── app.py                  # FastAPI application
├── agents/                     # LangChain AI agents
│   ├── planner_agent.py        # Weekly plan generator
│   └── exercise_agent.py       # Exercise selector
├── database/
│   └── mongodb.py              # MongoDB operations
├── prompts/
│   └── templates.py            # AI prompt templates
├── schemas/
│   ├── models.py               # Domain models
│   └── user.py                 # User model
├── tools/
│   └── musclewiki.py           # MuscleWiki API tools
├── docker-compose.yml          # MongoDB container
├── requirements.txt            # Python dependencies
└── run_api.py                  # Entry point
```

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login with email/password |
| POST | `/api/v1/auth/google` | Authenticate with Google OAuth |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Logout (clear cookies) |
| GET | `/api/v1/auth/me` | Get current user profile |
| PATCH | `/api/v1/auth/me` | Update user profile |

### Training Plans (requires authentication)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/trainings` | Create training plan (async) |
| GET | `/api/v1/trainings` | List user's training plans |
| GET | `/api/v1/trainings/days` | Flat list of calendar training days |
| GET | `/api/v1/trainings/stats` | Aggregated dashboard analytics for selected date window |
| GET | `/api/v1/trainings/tasks/{id}` | Get task status |
| GET | `/api/v1/trainings/{id}` | Get full training plan |

## Architecture

### VCR Pattern (View-Controller-Repository)

```
Views (api/views/)
  ↓ HTTP routing, validation, auth
Controllers (api/controllers/)
  ↓ Business logic orchestration
Services (api/services/)
  ↓ Complex operations, external APIs
Repositories (api/repositories/)
  ↓ Data access
Database (MongoDB)
```

### Authentication Flow

```
1. Register/Login → Backend creates JWT tokens
2. Access token (30 min) → Sent in Authorization header
3. Refresh token (7 days) → Stored in httpOnly cookie
4. Protected routes use get_current_user dependency
5. On 401 → Frontend calls /auth/refresh
```

### AI Agent Flow

```
User Data → Planner Agent → Weekly Plan (body parts per day)
    ↓
Exercise Agent → Fill Exercises from MuscleWiki API
    ↓
Database → Store Complete Training Plan
```

## Database Collections

### users

```json
{
  "_id": ObjectId,
  "email": "user@example.com",
  "password_hash": "$2b$12$...",
  "google_id": "optional-google-sub",
  "name": "John Doe",
  "profile": {
    "age": 25,
    "weight": 75.0,
    "target_weight": 70.0
  },
  "created_at": ISODate,
  "updated_at": ISODate
}
```

### training_plans

```json
{
  "_id": ObjectId,
  "user_id": "user-id-string",
  "difficulty": "Intermediate",
  "created_at": ISODate,
  "updated_at": ISODate,
  "source_version": 2
}
```

### training_days

```json
{
  "_id": ObjectId,
  "plan_id": ObjectId,
  "user_id": "user-id-string",
  "day": "2024-01-15",
  "name": "Plecy i Biceps",
  "time_required": 48,
  "exercises": [...],
  "created_at": ISODate,
  "updated_at": ISODate
}
```

### training_tasks

```json
{
  "_id": ObjectId,
  "user_id": "user-id-string",
  "status": "pending|processing|completed|failed",
  "message": "Status message",
  "result": {
    "training_id": "plan-id",
    "schema_version": 2
  },
  "error": "Error message if failed",
  "created_at": ISODate,
  "completed_at": ISODate
}
```

## Security

- **Passwords**: bcrypt with work factor 12
- **Access tokens**: JWT, 30 min expiry
- **Refresh tokens**: JWT, 7 days, httpOnly cookie
- **CORS**: Restricted origins with credentials
- **Cookies**: secure=true in production, sameSite=lax

## Development

### Adding a New Endpoint

1. **Schema** (`api/schemas/`) - Define request/response models
2. **Repository** (`api/repositories/`) - Add data access methods
3. **Controller** (`api/controllers/`) - Add business logic
4. **View** (`api/views/`) - Add route with auth dependency

### Running Tests

```bash
pytest
```

### One-time migration script

```bash
python3 scripts/migrate_trainings_to_v2.py --dry-run --report-dir ./migration-reports
python3 scripts/migrate_trainings_to_v2.py --execute --report-dir ./migration-reports
```

### Type Checking

```bash
mypy .
```

### Linting

```bash
ruff check .
```

## Troubleshooting

### "Cannot connect to MongoDB"
- Ensure MongoDB is running: `docker-compose up -d`
- Check MONGODB_URI environment variable

### "JWT token invalid"
- Check JWT_SECRET_KEY is set
- Ensure token hasn't expired
- Verify Authorization header format: `Bearer <token>`

### "Google OAuth failed"
- Verify GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET
- Check redirect_uri matches Google Cloud Console config
- Ensure Google+ API is enabled

### "Training generation takes too long"
- Normal generation time is 1-3 minutes
- Check GOOGLE_API_KEY and RAPIDAPI_KEY are valid
- Check backend logs for agent errors

## Performance

- Task processing: 1-3 minutes
- Database queries: < 50ms
- Auth endpoints: < 100ms
- MongoDB indexes on: email, user_id, task_id

## License

Private project for AI Personal Trainer application.
