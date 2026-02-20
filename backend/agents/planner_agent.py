"""Planner agent for generating weekly training schedule."""

from langchain_google_genai import ChatGoogleGenerativeAI

from prompts.templates import create_planner_prompt
from schemas.models import WeekPlan


def create_planner_agent(
    age: int = 19,
    weight: float = 102.0,
    target_weight: float = 80.0,
    difficulty: str = "Intermediate",
    selected_days: list[str] | None = None,
):
    """Create a planner agent that generates weekly training plans.

    The planner uses structured output to ensure the response
    matches the WeekPlan schema with dates and body parts.

    Args:
        age: Client age in years
        weight: Current weight in kg
        target_weight: Target weight in kg
        difficulty: Training difficulty level (Novice, Intermediate, Advanced)
        selected_days: Selected days of week (monday-sunday)

    Returns:
        A LangChain runnable chain that outputs WeekPlan.
    """
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.7,
    )

    structured_llm = llm.with_structured_output(WeekPlan)
    prompt = create_planner_prompt(
        age=age,
        weight=weight,
        target_weight=target_weight,
        difficulty=difficulty,
        selected_days=selected_days,
    )
    chain = prompt | structured_llm

    return chain
