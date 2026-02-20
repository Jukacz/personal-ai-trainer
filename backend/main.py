"""Main entry point for the AI Personal Trainer."""

import json
import logging
import re

from agents.exercise_agent import create_exercise_agent
from agents.planner_agent import create_planner_agent
from database.mongodb import save_training_plan
from dotenv import load_dotenv

# Setup logging BEFORE importing other modules
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def extract_json_from_response(response: str) -> dict | None:
    """Extract JSON from agent response (may be wrapped in markdown code blocks).

    Args:
        response: Raw response string from the agent

    Returns:
        Parsed JSON as dictionary, or None if parsing fails
    """
    # Try to find JSON in markdown code block
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", response)

    if json_match:
        json_str = json_match.group(1)
    else:
        # Try to find raw JSON (starts with {)
        json_match = re.search(r"(\{[\s\S]*\})", response)
        if json_match:
            json_str = json_match.group(1)
        else:
            return None

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"[JSON] Failed to parse: {e}")
        return None


def main() -> None:
    """Run the personal trainer workflow."""
    # Load environment variables
    load_dotenv()

    print("=" * 60)
    print("AI PERSONAL TRAINER - Generowanie planu treningowego")
    print("=" * 60)

    # Step 1: Generate weekly plan with body parts
    print("\n[1/3] Generowanie planu tygodnia...")
    planner = create_planner_agent()
    week_plan = planner.invoke({})

    print("\n=== PLAN TYGODNIA ===")
    print(f"Tydzień: {week_plan.weekStart} - {week_plan.weekEnd}")
    for training in week_plan.trainings:
        print(f"  {training.day}: {', '.join(training.bodyParts)}")

    # Step 2: Fill in exercises using MuscleWiki API
    print("\n[2/3] Wypełnianie ćwiczeń z MuscleWiki API...")

    run_agent = create_exercise_agent()

    input_message = f"""Wypełnij plan treningowy konkretnymi ćwiczeniami.

Plan tygodnia do wypełnienia:
{week_plan.model_dump_json(indent=2)}

Dla każdego dnia treningowego:
1. Użyj get_muscles() aby poznać dostępne nazwy mięśni
2. Dla każdej partii ciała (bodyParts) użyj get_exercises() aby pobrać ćwiczenia
3. Wybierz 2 ćwiczenia na partię ciała
4. Użyj get_exercise_details() dla wybranych ćwiczeń aby pobrać video URL
5. Zwróć kompletny plan z ćwiczeniami

Zwróć finalny JSON z treningami zawierającymi: day, name, timeRequired, exercises."""

    print("\n--- Agent wykonuje zapytania do API ---")
    result = run_agent(input_message)

    # Step 3: Print final result
    print("\n" + "=" * 60)
    print("FINALNY PLAN TRENINGOWY")
    print("=" * 60)
    print(result)

    # Step 4: Save to MongoDB
    print("\n[3/3] Zapisywanie do MongoDB...")

    final_plan = extract_json_from_response(result)

    if final_plan:
        try:
            doc_id = save_training_plan(final_plan)
            print("\n[MongoDB] Zapisano plan treningowy!")
            print(f"[MongoDB] ID dokumentu: {doc_id}")
        except Exception as e:
            logger.error(f"[MongoDB] Błąd zapisu: {e}")
            print(f"\n[MongoDB] Błąd zapisu do bazy: {e}")
    else:
        print("\n[MongoDB] Nie udało się sparsować JSON - plan nie został zapisany")


if __name__ == "__main__":
    main()
