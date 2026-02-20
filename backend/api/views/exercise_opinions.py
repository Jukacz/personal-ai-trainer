"""Exercise opinion routes."""

from fastapi import APIRouter, Depends

from api.auth.dependencies import get_current_user
from api.controllers.training_controller import TrainingController, get_training_controller
from api.schemas.requests import UpsertExerciseOpinionRequest
from api.schemas.responses import ErrorResponse, ExerciseOpinionResponse

router = APIRouter(prefix="/exercise-opinions", tags=["Exercise Opinions"])


@router.get(
    "/{exercise_id}",
    response_model=ExerciseOpinionResponse,
    summary="Get current user opinion for exercise",
    responses={
        200: {"description": "Exercise opinion", "model": ExerciseOpinionResponse},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        404: {"description": "Opinion not found", "model": ErrorResponse},
    },
)
async def get_exercise_opinion(
    exercise_id: int,
    user: dict = Depends(get_current_user),
    controller: TrainingController = Depends(get_training_controller),
) -> ExerciseOpinionResponse:
    """Get latest opinion snapshot for selected exercise."""
    return controller.get_exercise_opinion(exercise_id=exercise_id, user_id=str(user["_id"]))


@router.put(
    "/{exercise_id}",
    response_model=ExerciseOpinionResponse,
    summary="Upsert current user opinion for exercise",
    responses={
        200: {"description": "Opinion saved", "model": ExerciseOpinionResponse},
        401: {"description": "Not authenticated", "model": ErrorResponse},
        422: {"description": "Invalid payload", "model": ErrorResponse},
    },
)
async def upsert_exercise_opinion(
    exercise_id: int,
    request: UpsertExerciseOpinionRequest,
    user: dict = Depends(get_current_user),
    controller: TrainingController = Depends(get_training_controller),
) -> ExerciseOpinionResponse:
    """Store user rating and opinion for selected exercise."""
    return controller.upsert_exercise_opinion(
        exercise_id=exercise_id,
        request=request,
        user_id=str(user["_id"]),
    )
