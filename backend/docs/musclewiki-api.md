```markdown
## Endpoints

### Health & Metadata

#### GET /
Get basic API information and available endpoints.

**Parameters**: None

**Example Response**:
```json
{
  "name": "MuscleWiki API",
  "version": "2.0.0",
  "docs": "/docs",
  "endpoints": {
    "exercises": "/exercises",
    "search": "/search",
    "random": "/random",
    "categories": "/categories"
  }
}

```

---

#### GET /health

Check API health status and database statistics.

**Parameters**: None

**Example Response**:

```json
{
  "status": "healthy",
  "version": "2.0.0",
  "exercises_loaded": 1734
}

```

---

#### GET /statistics

Get comprehensive database statistics including exercise counts, category breakdown, difficulty distribution, and more.

**Parameters**: None

**Example Response**:

```json
{
  "total_exercises": 1734,
  "total_categories": 10,
  "total_muscles": 15,
  "categories": [
    {"name": "barbell", "display_name": "Barbell", "count": 150},
    {"name": "dumbbell", "display_name": "Dumbbell", "count": 200}
  ],
  "muscles": [
    {"name": "Biceps", "count": 45},
    {"name": "Chest", "count": 120}
  ],
  "difficulty_distribution": {
    "Novice": 500,
    "Intermediate": 800,
    "Advanced": 303
  },
  "mechanic_distribution": {
    "Compound": 900,
    "Isolation": 650
  },
  "force_distribution": {
    "Push": 600,
    "Pull": 550,
    "Static": 150
  },
  "average_steps_per_exercise": 3.5,
  "average_videos_per_exercise": 4.0,
  "total_videos": 6829
}

```

---

#### GET /categories

List all equipment categories with exercise counts.

**Parameters**: None

**Example Response**:

```json
[
  {"name": "barbell", "display_name": "Barbell", "count": 150},
  {"name": "dumbbell", "display_name": "Dumbbell", "count": 200},
  {"name": "bodyweight", "display_name": "Bodyweight", "count": 180},
  {"name": "cable", "display_name": "Cable", "count": 120}
]

```

---

#### GET /muscles

List all primary muscle groups with exercise counts.

**Parameters**: None

**Example Response**:

```json
[
  {"name": "Biceps", "count": 45},
  {"name": "Chest", "count": 120},
  {"name": "Quadriceps", "count": 85},
  {"name": "Triceps", "count": 52}
]

```

---

#### GET /filters

Get all available filter values for building dynamic UIs.

**Parameters**: None

**Example Response**:

```json
{
  "muscles": ["Biceps", "Chest", "Quadriceps", "Triceps"],
  "difficulties": ["Advanced", "Intermediate", "Novice"],
  "forces": ["Pull", "Push", "Static"],
  "mechanics": ["Compound", "Isolation"],
  "grips": ["Neutral", "Overhand", "Underhand"],
  "categories": ["Barbell", "Bodyweight", "Cable", "Dumbbell"]
}

```

---

### Exercise Endpoints

#### GET /exercises

List exercises with pagination and optional filtering. Returns minimal information optimized for list views.

**Query Parameters**:

* `limit` (integer, optional): Maximum results (1-100, default: 20)
* `offset` (integer, optional): Skip results (default: 0)
* `search` (string, optional): Text search in names and steps
* `gender` (string, optional): `male` or `female`
* `category` (string, optional): Equipment category
* `muscles` (array[string], optional): Muscle groups
* `difficulty` (string, optional): `novice`, `intermediate`, `advanced`
* `force` (string, optional): `push`, `pull`, `static`
* `mechanic` (string, optional): `isolation`, `compound`
* `grips` (array[string], optional): Grip types

**Example Response**:

```json
{
  "total": 45,
  "limit": 5,
  "offset": 0,
  "count": 5,
  "results": [
    {"id": 0, "name": "Barbell Curl"},
    {"id": 15, "name": "Barbell Bench Press"}
  ]
}

```

---

#### GET /exercises/{exercise_id}

Get detailed information for a specific exercise by ID.

**Path Parameters**:

* `exercise_id` (integer, required): Exercise ID

**Query Parameters**:

* `detail` (boolean, optional): Return additional metadata (default: false)
* `gender` (string, optional): Filter videos by gender

**Example Response**:

```json
{
  "id": 0,
  "name": "Barbell Curl",
  "primary_muscles": ["Biceps"],
  "category": "Barbell",
  "force": "Pull",
  "grips": ["Underhand"],
  "mechanic": "Isolation",
  "difficulty": "Intermediate",
  "steps": ["..."],
  "videos": [
    {
      "url": "https://...",
      "angle": "front",
      "gender": "male",
      "og_image": "https://..."
    }
  ]
}

```

---

#### GET /exercises/{exercise_id}/videos

Get only video URLs for a specific exercise.

**Path Parameters**:

* `exercise_id` (integer, required): Exercise ID

**Query Parameters**:

* `gender` (string, optional): Filter by gender

**Example Response**:

```json
[
  {
    "url": "https://...",
    "angle": "front",
    "gender": "female",
    "og_image": "https://..."
  }
]

```

---

### Search & Discovery

#### GET /search

Search exercises by text query with intelligent relevance scoring.

**Query Parameters**:

* `q` (string, required): Search query (min 2 characters)
* `limit` (integer, optional): Maximum results (1-50, default: 10)
* (Supports all filters from /exercises)

**Example Response**:

```json
[
  {
    "id": 0,
    "name": "Barbell Curl",
    "primary_muscles": ["Biceps"],
    "category": "Barbell",
    "steps": ["..."],
    "videos": ["..."]
  }
]

```

---

#### GET /random

Get a random exercise, optionally filtered by category.

**Query Parameters**:

* `category` (string, optional): Equipment category
* `gender` (string, optional): Filter videos by gender

**Example Response**:

```json
{
  "id": 342,
  "name": "Push Up",
  "primary_muscles": ["Chest", "Triceps"],
  "category": "Bodyweight",
  "steps": ["..."],
  "videos": ["..."]
}

```

---

### Workout Builders

#### GET /workouts/push

Get exercises with push force type.

**Query Parameters**:

* `limit` (integer, optional): Maximum results
* `difficulty` (string, optional): Filter by difficulty
* `category` (string, optional): Filter by equipment

---

#### GET /workouts/pull

Get exercises with pull force type.

**Query Parameters**:

* `limit` (integer, optional): Maximum results
* `difficulty` (string, optional): Filter by difficulty
* `category` (string, optional): Filter by equipment

```

```