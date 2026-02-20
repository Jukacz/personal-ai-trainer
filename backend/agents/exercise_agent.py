"""Exercise agent for filling in training plans with exercises."""

import logging

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from prompts.templates import EXERCISE_AGENT_PROMPT
from tools.musclewiki import get_exercises, get_exercise_details, get_muscles

logger = logging.getLogger(__name__)

# Map tool names to functions
TOOLS = {
    "get_muscles": get_muscles,
    "get_exercises": get_exercises,
    "get_exercise_details": get_exercise_details,
}


def create_exercise_agent():
    """Create an exercise agent with MuscleWiki API tools.

    Returns a function that runs the agent with tool calling loop.
    """
    tools = [get_muscles, get_exercises, get_exercise_details]

    # Log available tools
    logger.info("=" * 50)
    logger.info("[AGENT] Creating exercise agent with tools:")
    for t in tools:
        logger.info(f"  - {t.name}: {t.description[:50]}...")
    logger.info("=" * 50)

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.3,
    )

    # Bind tools to the model
    model_with_tools = llm.bind_tools(tools)

    # Extract system message from prompt template
    system_message = EXERCISE_AGENT_PROMPT.messages[0].prompt.template

    def run_agent(user_input: str, max_iterations: int = 15) -> str:
        """Run the agent with tool calling loop.

        Args:
            user_input: The user's request
            max_iterations: Maximum number of tool call iterations

        Returns:
            Final response from the model
        """
        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_input),
        ]

        for iteration in range(max_iterations):
            logger.info(f"[AGENT] Iteration {iteration + 1}/{max_iterations}")

            # Get model response
            response = model_with_tools.invoke(messages)
            messages.append(response)

            # Check if there are tool calls
            if not response.tool_calls:
                logger.info("[AGENT] No more tool calls, returning final response")
                return response.content

            # Execute each tool call
            logger.info(f"[AGENT] Processing {len(response.tool_calls)} tool call(s)")

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                logger.info(f"[AGENT] Calling tool: {tool_name} with args: {tool_args}")

                if tool_name in TOOLS:
                    tool_fn = TOOLS[tool_name]
                    try:
                        # Execute the tool
                        tool_result = tool_fn.invoke(tool_call)
                        messages.append(tool_result)
                        logger.info(f"[AGENT] Tool {tool_name} executed successfully")
                    except Exception as e:
                        logger.error(f"[AGENT] Tool {tool_name} failed: {e}")
                        # Add error message
                        from langchain_core.messages import ToolMessage
                        error_msg = ToolMessage(
                            content=f"Error executing tool: {e}",
                            tool_call_id=tool_call["id"],
                        )
                        messages.append(error_msg)
                else:
                    logger.warning(f"[AGENT] Unknown tool: {tool_name}")

        logger.warning("[AGENT] Max iterations reached")
        return response.content if response else "Max iterations reached"

    return run_agent


logger.info("[AGENT] Agent created successfully")
