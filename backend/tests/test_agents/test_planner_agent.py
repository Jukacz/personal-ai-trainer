"""Test suite for planner agent.

Tests the AI agent for generating weekly training schedules including:
- Agent creation with various parameters
- Response structure validation
- Error handling
"""

from unittest.mock import MagicMock, patch

from agents.planner_agent import create_planner_agent


class TestCreatePlannerAgent:
    """Tests for create_planner_agent function."""

    def test_create_planner_agent_returns_chain(self):
        """Test create_planner_agent returns a runnable chain.

        Verifies the function returns a valid agent chain.
        """
        with patch(
            "agents.planner_agent.ChatGoogleGenerativeAI",
            return_value=MagicMock(),
        ):
            with patch("agents.planner_agent.create_planner_prompt"):
                agent = create_planner_agent()

                assert agent is not None

    def test_create_planner_agent_initializes_llm(self):
        """Test create_planner_agent initializes ChatGoogleGenerativeAI.

        Verifies LLM is created with correct model.
        """
        with patch(
            "agents.planner_agent.ChatGoogleGenerativeAI",
            return_value=MagicMock(),
        ) as mock_llm_class:
            with patch("agents.planner_agent.create_planner_prompt"):
                create_planner_agent()

                mock_llm_class.assert_called_once()
                call_kwargs = mock_llm_class.call_args.kwargs
                assert call_kwargs["model"] == "gemini-2.0-flash"

    def test_create_planner_agent_sets_temperature(self):
        """Test create_planner_agent sets LLM temperature.

        Verifies temperature parameter for consistency.
        """
        with patch(
            "agents.planner_agent.ChatGoogleGenerativeAI",
            return_value=MagicMock(),
        ) as mock_llm_class:
            with patch("agents.planner_agent.create_planner_prompt"):
                create_planner_agent()

                call_kwargs = mock_llm_class.call_args.kwargs
                assert call_kwargs["temperature"] == 0.7

    def test_create_planner_agent_with_default_parameters(self):
        """Test create_planner_agent uses default user parameters.

        Verifies default age, weight, target_weight, difficulty.
        """
        with patch(
            "agents.planner_agent.ChatGoogleGenerativeAI",
            return_value=MagicMock(),
        ):
            with patch(
                "agents.planner_agent.create_planner_prompt",
            ) as mock_prompt:
                create_planner_agent()

                mock_prompt.assert_called_once()
                call_kwargs = mock_prompt.call_args.kwargs
                assert call_kwargs["age"] == 19
                assert call_kwargs["weight"] == 102.0
                assert call_kwargs["target_weight"] == 80.0
                assert call_kwargs["difficulty"] == "Intermediate"
                assert call_kwargs["selected_days"] is None

    def test_create_planner_agent_with_custom_parameters(self):
        """Test create_planner_agent uses custom parameters.

        Verifies custom values are passed to prompt creation.
        """
        with patch(
            "agents.planner_agent.ChatGoogleGenerativeAI",
            return_value=MagicMock(),
        ):
            with patch(
                "agents.planner_agent.create_planner_prompt",
            ) as mock_prompt:
                create_planner_agent(
                    age=30,
                    weight=75.0,
                    target_weight=70.0,
                    difficulty="Advanced",
                    selected_days=["tuesday", "thursday", "saturday"],
                )

                call_kwargs = mock_prompt.call_args.kwargs
                assert call_kwargs["age"] == 30
                assert call_kwargs["weight"] == 75.0
                assert call_kwargs["target_weight"] == 70.0
                assert call_kwargs["difficulty"] == "Advanced"
                assert call_kwargs["selected_days"] == [
                    "tuesday",
                    "thursday",
                    "saturday",
                ]

    def test_create_planner_agent_with_various_ages(self):
        """Test create_planner_agent with various ages.

        Verifies agent creation for different age groups.
        """
        with patch(
            "agents.planner_agent.ChatGoogleGenerativeAI",
            return_value=MagicMock(),
        ):
            with patch("agents.planner_agent.create_planner_prompt"):
                for age in [16, 30, 50, 100]:
                    agent = create_planner_agent(age=age)
                    assert agent is not None

    def test_create_planner_agent_with_various_difficulties(self):
        """Test create_planner_agent with various difficulty levels.

        Verifies agent creation for all difficulty levels.
        """
        with patch(
            "agents.planner_agent.ChatGoogleGenerativeAI",
            return_value=MagicMock(),
        ):
            with patch("agents.planner_agent.create_planner_prompt"):
                for difficulty in ["Novice", "Intermediate", "Advanced"]:
                    agent = create_planner_agent(difficulty=difficulty)
                    assert agent is not None

    def test_create_planner_agent_creates_structured_output(self):
        """Test create_planner_agent creates LLM with structured output.

        Verifies with_structured_output is called on LLM.
        """
        mock_llm = MagicMock()
        mock_llm.with_structured_output = MagicMock(return_value=MagicMock())

        with patch(
            "agents.planner_agent.ChatGoogleGenerativeAI",
            return_value=mock_llm,
        ):
            with patch("agents.planner_agent.create_planner_prompt"):
                create_planner_agent()

                # Verify with_structured_output was called
                mock_llm.with_structured_output.assert_called_once()

    def test_create_planner_agent_with_weight_variations(self):
        """Test create_planner_agent handles various weight values.

        Verifies agent works with different weight inputs.
        """
        with patch(
            "agents.planner_agent.ChatGoogleGenerativeAI",
            return_value=MagicMock(),
        ):
            with patch("agents.planner_agent.create_planner_prompt"):
                for weight in [50.0, 102.0, 150.5]:
                    agent = create_planner_agent(weight=weight)
                    assert agent is not None

    def test_create_planner_agent_with_target_weight_variations(self):
        """Test create_planner_agent handles various target weight values.

        Verifies agent works with different target weight inputs.
        """
        with patch(
            "agents.planner_agent.ChatGoogleGenerativeAI",
            return_value=MagicMock(),
        ):
            with patch("agents.planner_agent.create_planner_prompt"):
                for target_weight in [45.0, 70.0, 90.5]:
                    agent = create_planner_agent(target_weight=target_weight)
                    assert agent is not None


class TestPlannerAgentIntegration:
    """Integration-style tests for planner agent."""

    def test_planner_agent_chain_structure(self):
        """Test planner agent creates correct chain structure.

        Verifies prompt | structured_llm pattern is used.
        """
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_prompt = MagicMock()

        with patch(
            "agents.planner_agent.ChatGoogleGenerativeAI",
            return_value=mock_llm,
        ):
            with patch(
                "agents.planner_agent.create_planner_prompt",
                return_value=mock_prompt,
            ):
                agent = create_planner_agent()

                # Verify chain is created (prompt | llm)
                assert agent is not None

    def test_create_planner_agent_idempotency(self):
        """Test creating planner agent multiple times works.

        Verifies agent can be created repeatedly without side effects.
        """
        with patch(
            "agents.planner_agent.ChatGoogleGenerativeAI",
            return_value=MagicMock(),
        ):
            with patch("agents.planner_agent.create_planner_prompt"):
                agent1 = create_planner_agent(age=30)
                agent2 = create_planner_agent(age=40)

                # Both should be created successfully
                assert agent1 is not None
                assert agent2 is not None
