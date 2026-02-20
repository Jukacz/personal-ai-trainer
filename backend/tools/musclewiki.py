"""MuscleWiki API tools and helpers for fetching exercises."""

import json
import logging
import os
import random
from typing import Any

import httpx
from langchain.tools import tool

from database.mongodb import get_exercise, save_exercise

logger = logging.getLogger(__name__)


def _get_headers() -> dict[str, str]:
    """Get API headers with RapidAPI key."""
    api_key = os.getenv("RAPIDAPI_KEY", "")
    logger.debug(f"[HEADERS] RAPIDAPI_KEY present: {bool(api_key)}")
    return {
        "x-rapidapi-host": "musclewiki-api.p.rapidapi.com",
        "x-rapidapi-key": api_key,
    }


def fetch_exercises_list(
    muscles: list[str] | None = None,
    search: str | None = None,
    limit: int = 20,
    offset: int = 0,
    gender: str = "male",
) -> dict[str, Any]:
    """Fetch exercises from MuscleWiki with optional filters."""
    params: dict[str, Any] = {
        "limit": max(1, min(limit, 100)),
        "offset": max(0, offset),
        "gender": gender,
    }
    if muscles:
        params["muscles"] = muscles
    if search:
        params["search"] = search

    response = httpx.get(
        "https://musclewiki-api.p.rapidapi.com/exercises",
        headers=_get_headers(),
        params=params,
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()


def fetch_exercise_details_by_id(exercise_id: int) -> dict[str, Any]:
    """Fetch full exercise details with local-cache lookup first."""
    existing = get_exercise(exercise_id)
    if existing:
        existing.pop("_id", None)
        existing.pop("savedAt", None)
        existing.pop("exerciseId", None)
        return existing

    response = httpx.get(
        f"https://musclewiki-api.p.rapidapi.com/exercises/{exercise_id}",
        headers=_get_headers(),
        params={
            "details": "true",
            "gender": "male",
        },
        timeout=30.0,
    )
    response.raise_for_status()
    data = response.json()
    save_exercise(exercise_id, data)
    return data


@tool
def get_muscles() -> str:
    """Zwraca listę wszystkich dostępnych mięśni z MuscleWiki API.

    Użyj tego narzędzia najpierw, aby poznać dokładne nazwy mięśni
    dostępne w API. Nazwy te są wymagane do wyszukiwania ćwiczeń.

    Returns:
        JSON string z listą mięśni i liczbą dostępnych ćwiczeń dla każdego.
    """
    logger.info("=" * 50)
    logger.info("[TOOL CALLED] get_muscles()")
    logger.info("=" * 50)

    try:
        response = httpx.get(
            "https://musclewiki-api.p.rapidapi.com/muscles",
            headers=_get_headers(),
            timeout=30.0,
        )
        response.raise_for_status()
        logger.info(f"[get_muscles] Status: {response.status_code}")
        logger.debug(f"[get_muscles] Response length: {len(response.text)} chars")
        return response.text
    except Exception as e:
        logger.error(f"[get_muscles] ERROR: {e}")
        raise


@tool
def get_exercises(muscle: str) -> str:
    """Pobiera listę ćwiczeń dla danego mięśnia.

    Args:
        muscle: Nazwa mięśnia (dokładna nazwa z get_muscles, np. 'Biceps', 'Chest')

    Returns:
        JSON string z listą 2 losowych ćwiczeń zawierającą id, name i inne szczegóły.
    """
    # Hardcoded: always 2 exercises with random offset for variety
    limit = 2
    offset = random.randint(0, 100)

    logger.info("=" * 50)
    logger.info(f"[TOOL CALLED] get_exercises(muscle={muscle}, limit={limit}, offset={offset})")
    logger.info("=" * 50)

    try:
        data = fetch_exercises_list(
            muscles=[muscle],
            limit=limit,
            offset=offset,
            gender="male",
        )
        payload = json.dumps(data)
        logger.debug(f"[get_exercises] Response length: {len(payload)} chars")
        return payload
    except Exception as e:
        logger.error(f"[get_exercises] ERROR: {e}")
        raise


@tool
def get_exercise_details(exercise_id: int) -> str:
    """Pobiera szczegółowe informacje o ćwiczeniu wraz z video URL.

    Args:
        exercise_id: ID ćwiczenia uzyskane z get_exercises

    Returns:
        JSON string ze szczegółami ćwiczenia: name, steps, videos, difficulty.
    """
    logger.info("=" * 50)
    logger.info(f"[TOOL CALLED] get_exercise_details(exercise_id={exercise_id})")
    logger.info("=" * 50)

    try:
        data = fetch_exercise_details_by_id(exercise_id)
        return json.dumps(data)
    except Exception as e:
        logger.error(f"[API] ERROR: {e}")
        raise
