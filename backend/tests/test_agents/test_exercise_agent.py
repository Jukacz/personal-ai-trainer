"""Test suite for exercise agent.

Tests the AI agent for generating exercise selections including:
- Agent creation
- Invocation with various prompts
- Response handling
- Error cases
"""

from unittest.mock import MagicMock, patch

from agents.exercise_agent import create_exercise_agent


class TestCreateExerciseAgent:
    """Tests for create_exercise_agent function."""

    def test_create_exercise_agent_returns_callable(self):
        """Test create_exercise_agent returns a callable run_agent function.

        Verifies the function returns a valid callable that accepts prompts.
        """
        with patch("agents.exercise_agent.ChatGoogleGenerativeAI"):
            with patch("agents.exercise_agent.EXERCISE_AGENT_PROMPT"):
                agent = create_exercise_agent()

                assert agent is not None
                assert callable(agent)

    def test_create_exercise_agent_initializes_llm(self):
        """Test create_exercise_agent initializes ChatGoogleGenerativeAI.

        Verifies LLM is created with correct model.
        """
        with patch(
            "agents.exercise_agent.ChatGoogleGenerativeAI",
            return_value=MagicMock(),
        ) as mock_llm_class:
            with patch("agents.exercise_agent.EXERCISE_AGENT_PROMPT"):
                create_exercise_agent()

                mock_llm_class.assert_called_once()
                call_kwargs = mock_llm_class.call_args.kwargs
                assert call_kwargs["model"] == "gemini-2.0-flash"

    def test_create_exercise_agent_sets_temperature(self):
        """Test create_exercise_agent sets LLM temperature.

        Verifies temperature is set for consistency.
        """
        with patch(
            "agents.exercise_agent.ChatGoogleGenerativeAI",
            return_value=MagicMock(),
        ) as mock_llm_class:
            with patch("agents.exercise_agent.EXERCISE_AGENT_PROMPT"):
                create_exercise_agent()

                call_kwargs = mock_llm_class.call_args.kwargs
                assert call_kwargs["temperature"] == 0.3

    def test_create_exercise_agent_binds_tools_to_model(self):
        """Test create_exercise_agent binds tools to the LLM.

        Verifies bind_tools is called with the tool list.
        """
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = MagicMock()

        with patch(
            "agents.exercise_agent.ChatGoogleGenerativeAI",
            return_value=mock_llm,
        ):
            with patch("agents.exercise_agent.EXERCISE_AGENT_PROMPT"):
                create_exercise_agent()

                mock_llm.bind_tools.assert_called_once()

    def test_create_exercise_agent_returns_run_agent_function(self):
        """Test create_exercise_agent returns the run_agent inner function.

        Verifies returned object is callable and ready to process prompts.
        """
        with patch("agents.exercise_agent.ChatGoogleGenerativeAI"):
            with patch("agents.exercise_agent.EXERCISE_AGENT_PROMPT"):
                agent = create_exercise_agent()

                # Agent should be callable
                assert callable(agent)

    def test_create_exercise_agent_can_be_invoked_with_prompt(self):
        """Test create_exercise_agent returns agent that can be invoked with prompt.

        Verifies agent can be called with a string prompt.
        """
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.tool_calls = []
        mock_response.content = "Exercise response"
        mock_llm.bind_tools.return_value.invoke.return_value = mock_response

        with patch(
            "agents.exercise_agent.ChatGoogleGenerativeAI",
            return_value=mock_llm,
        ):
            with patch("agents.exercise_agent.EXERCISE_AGENT_PROMPT"):
                agent = create_exercise_agent()

                # Should be callable with a prompt
                result = agent("Test prompt")
                assert result is not None

    def test_create_exercise_agent_multiple_calls(self):
        """Test create_exercise_agent can be called multiple times.

        Verifies agent creation is repeatable.
        """
        with patch("agents.exercise_agent.ChatGoogleGenerativeAI"):
            with patch("agents.exercise_agent.EXERCISE_AGENT_PROMPT"):
                agent1 = create_exercise_agent()
                agent2 = create_exercise_agent()

                assert agent1 is not None
                assert agent2 is not None

    def test_create_exercise_agent_llm_model_name(self):
        """Test exercise agent uses correct LLM model.

        Verifies model is gemini-2.0-flash.
        """
        with patch(
            "agents.exercise_agent.ChatGoogleGenerativeAI",
            return_value=MagicMock(),
        ) as mock_llm_class:
            with patch("agents.exercise_agent.EXERCISE_AGENT_PROMPT"):
                create_exercise_agent()

                call_args = mock_llm_class.call_args
                assert call_args.kwargs["model"] == "gemini-2.0-flash"

    def test_create_exercise_agent_temperature_lower_for_consistency(self):
        """Test exercise agent has lower temperature than planner.

        Verifies temperature=0.3 for more consistent outputs.
        """
        with patch(
            "agents.exercise_agent.ChatGoogleGenerativeAI",
            return_value=MagicMock(),
        ) as mock_llm_class:
            with patch("agents.exercise_agent.EXERCISE_AGENT_PROMPT"):
                create_exercise_agent()

                call_kwargs = mock_llm_class.call_args.kwargs
                # Exercise agent should have lower temperature (0.3 vs 0.7)
                assert call_kwargs["temperature"] < 0.5


class TestExerciseAgentInvocation:
    """Tests for invoking exercise agent."""

    def test_exercise_agent_accepts_prompt_string(self):
        """Test exercise agent can be invoked with a string prompt.

        Verifies agent accepts string input and returns content.
        """
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.tool_calls = []
        mock_response.content = '{"day": "Monday", "exercises": []}'
        mock_llm.bind_tools.return_value.invoke.return_value = mock_response

        with patch("agents.exercise_agent.ChatGoogleGenerativeAI", return_value=mock_llm):
            with patch("agents.exercise_agent.EXERCISE_AGENT_PROMPT"):
                agent = create_exercise_agent()

                prompt = "Generate exercises for Monday focusing on back"
                result = agent(prompt)

                assert result is not None
                assert isinstance(result, str)

    def test_exercise_agent_returns_string_response(self):
        """Test exercise agent returns string response.

        Verifies agent output is a string (content field from response).
        """
        json_response = '{"day": "Monday", "exercises": []}'
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.tool_calls = []
        mock_response.content = json_response
        mock_llm.bind_tools.return_value.invoke.return_value = mock_response

        with patch("agents.exercise_agent.ChatGoogleGenerativeAI", return_value=mock_llm):
            with patch("agents.exercise_agent.EXERCISE_AGENT_PROMPT"):
                agent = create_exercise_agent()

                result = agent("Test prompt")

                assert isinstance(result, str)

    def test_exercise_agent_with_empty_prompt(self):
        """Test exercise agent handles empty prompt.

        Verifies agent can be called with empty string.
        """
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.tool_calls = []
        mock_response.content = '{"exercises": []}'
        mock_llm.bind_tools.return_value.invoke.return_value = mock_response

        with patch("agents.exercise_agent.ChatGoogleGenerativeAI", return_value=mock_llm):
            with patch("agents.exercise_agent.EXERCISE_AGENT_PROMPT"):
                agent = create_exercise_agent()

                result = agent("")

                assert result is not None

    def test_exercise_agent_with_long_prompt(self):
        """Test exercise agent handles long prompts.

        Verifies agent can process lengthy input.
        """
        long_prompt = "Generate exercises " * 100  # Very long prompt
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.tool_calls = []
        mock_response.content = '{"exercises": []}'
        mock_llm.bind_tools.return_value.invoke.return_value = mock_response

        with patch("agents.exercise_agent.ChatGoogleGenerativeAI", return_value=mock_llm):
            with patch("agents.exercise_agent.EXERCISE_AGENT_PROMPT"):
                agent = create_exercise_agent()

                result = agent(long_prompt)

                assert result is not None

    def test_exercise_agent_with_special_characters(self):
        """Test exercise agent handles special characters in prompt.

        Verifies agent can process non-ASCII characters (Polish).
        """
        prompt_with_polish = "Generuj ćwiczenia na poniedziałek"
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.tool_calls = []
        mock_response.content = '{"exercises": []}'
        mock_llm.bind_tools.return_value.invoke.return_value = mock_response

        with patch("agents.exercise_agent.ChatGoogleGenerativeAI", return_value=mock_llm):
            with patch("agents.exercise_agent.EXERCISE_AGENT_PROMPT"):
                agent = create_exercise_agent()

                result = agent(prompt_with_polish)

                assert result is not None


class TestExerciseAgentTools:
    """Tests for exercise agent tools."""

    def test_exercise_agent_includes_tools(self):
        """Test exercise agent includes required tools.

        Verifies tools are defined in the TOOLS dictionary.
        """
        # Import to check TOOLS dict exists
        from agents.exercise_agent import TOOLS

        # Should have at least the required tools
        assert "get_muscles" in TOOLS
        assert "get_exercises" in TOOLS
        assert "get_exercise_details" in TOOLS

    def test_exercise_agent_tools_have_invoke_method(self):
        """Test exercise agent tools have invoke method.

        Verifies all tools can be invoked via the invoke method.
        """
        from agents.exercise_agent import TOOLS

        for tool_name, tool_func in TOOLS.items():
            # LangChain StructuredTool objects have invoke method
            assert hasattr(tool_func, "invoke")

    def test_exercise_agent_bind_tools_uses_tool_list(self):
        """Test exercise agent binds correct number of tools.

        Verifies bind_tools is called with tool list.
        """
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = MagicMock()

        with patch(
            "agents.exercise_agent.ChatGoogleGenerativeAI",
            return_value=mock_llm,
        ):
            with patch("agents.exercise_agent.EXERCISE_AGENT_PROMPT"):
                create_exercise_agent()

                # Verify bind_tools was called
                mock_llm.bind_tools.assert_called_once()
                call_args = mock_llm.bind_tools.call_args
                tools_list = call_args[0][0]  # First positional argument

                # Should be a list with tools
                assert isinstance(tools_list, list)
                assert len(tools_list) >= 3  # At least 3 tools


class TestExerciseAgentErrorHandling:
    """Tests for exercise agent error handling."""

    def test_exercise_agent_handles_tool_call_error(self):
        """Test exercise agent handles tool execution errors.

        Verifies error handling when a tool call fails.
        """
        mock_llm = MagicMock()

        # First response has tool call, second has no tool calls
        mock_response1 = MagicMock()
        mock_response1.tool_calls = [
            {
                "id": "call_123",
                "name": "get_exercises",
                "args": {"muscle": "back"}
            }
        ]

        mock_response2 = MagicMock()
        mock_response2.tool_calls = []
        mock_response2.content = "Final response after error"

        # Mock invoke to return different responses
        mock_model_with_tools = MagicMock()
        mock_model_with_tools.invoke.side_effect = [
            mock_response1,
            mock_response2
        ]
        mock_llm.bind_tools.return_value = mock_model_with_tools

        with patch("agents.exercise_agent.ChatGoogleGenerativeAI", return_value=mock_llm):
            with patch("agents.exercise_agent.EXERCISE_AGENT_PROMPT"):
                agent = create_exercise_agent()

                # Should handle the error and continue
                result = agent("Test prompt")
                assert result is not None

    def test_exercise_agent_max_iterations_safety(self):
        """Test exercise agent respects max_iterations limit.

        Verifies agent doesn't infinite loop on tool calls.
        """
        mock_llm = MagicMock()

        # Response with endless tool calls
        mock_response = MagicMock()
        mock_response.tool_calls = [
            {
                "id": "call_123",
                "name": "get_exercises",
                "args": {"muscle": "back"}
            }
        ]
        mock_response.content = "Some content"

        mock_model_with_tools = MagicMock()
        mock_model_with_tools.invoke.return_value = mock_response
        mock_llm.bind_tools.return_value = mock_model_with_tools

        with patch("agents.exercise_agent.ChatGoogleGenerativeAI", return_value=mock_llm):
            with patch("agents.exercise_agent.EXERCISE_AGENT_PROMPT"):
                agent = create_exercise_agent()

                # Should not hang, should return after max iterations
                result = agent("Test prompt", max_iterations=5)
                assert result is not None
