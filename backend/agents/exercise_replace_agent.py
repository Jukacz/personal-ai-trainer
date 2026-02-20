"""Agent responsible for ranking replacement exercise candidates."""

import json
import logging
import re
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from prompts.templates import EXERCISE_REPLACE_AGENT_PROMPT

logger = logging.getLogger(__name__)


def _extract_ids(raw_response: str) -> list[int]:
    """Extract list of exercise IDs from model response."""
    match = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw_response)
    payload = match.group(1).strip() if match else raw_response.strip()

    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        # Try to recover raw object from text
        obj = re.search(r'(\{[\s\S]*\})', payload)
        if not obj:
            return []
        data = json.loads(obj.group(1))

    ids = data.get("exercise_ids", [])
    if not isinstance(ids, list):
        return []
    parsed: list[int] = []
    for value in ids:
        if isinstance(value, int):
            parsed.append(value)
    return parsed


def create_exercise_replace_agent():
    """Create LLM-based candidate ranker for exercise replacement."""
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.2,
    )
    system_message = EXERCISE_REPLACE_AGENT_PROMPT.messages[0].prompt.template

    def run_agent(payload: dict[str, Any]) -> list[int]:
        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=json.dumps(payload, ensure_ascii=False)),
        ]
        response = llm.invoke(messages)
        content = response.content if isinstance(response.content, str) else str(response.content)
        return _extract_ids(content)

    return run_agent
