"""Test suite for training service.

Tests the AI agent orchestration layer including:
- Generating training plans
- Extracting JSON from agent responses
- Handling errors from agents
- Applying difficulty instructions
"""

import pytest
from unittest.mock import MagicMock, patch

from api.services.training_service import TrainingService
from api.exceptions.handlers import TrainingGenerationError


class TestTrainingServiceInitialization:
    """Tests for TrainingService initialization."""

    def test_service_initializes(self):
        """Test service initializes successfully.

        Verifies no errors during initialization.
        """
        service = TrainingService()
        assert service is not None


class TestGetDifficultyInstruction:
    """Tests for _get_difficulty_instruction method."""

    def test_novice_instruction(self):
        """Test novice difficulty instruction is returned.

        Verifies correct Polish text for novice level.
        """
        service = TrainingService()
        instruction = service._get_difficulty_instruction("Novice")

        assert "Novice" or "prostsze" in instruction.lower()
        assert len(instruction) > 0

    def test_intermediate_instruction(self):
        """Test intermediate difficulty instruction is returned.

        Verifies correct text for intermediate level.
        """
        service = TrainingService()
        instruction = service._get_difficulty_instruction("Intermediate")

        assert len(instruction) > 0

    def test_advanced_instruction(self):
        """Test advanced difficulty instruction is returned.

        Verifies correct text for advanced level.
        """
        service = TrainingService()
        instruction = service._get_difficulty_instruction("Advanced")

        assert len(instruction) > 0

    def test_unknown_difficulty_returns_intermediate(self):
        """Test unknown difficulty defaults to intermediate.

        Verifies fallback behavior for unknown difficulty level.
        """
        service = TrainingService()
        instruction = service._get_difficulty_instruction("Unknown")

        # Should return intermediate as default
        intermediate = service._get_difficulty_instruction("Intermediate")
        assert instruction == intermediate


class TestGetUpcomingTrainingDates:
    """Tests for get_upcoming_training_dates method."""

    def test_get_upcoming_training_dates_returns_sorted_dates(self):
        """Selected days should return deterministic sorted upcoming week dates."""
        service = TrainingService()
        dates = service.get_upcoming_training_dates(["friday", "monday"])

        assert len(dates) == 2
        assert dates == sorted(dates)


class TestExtractJsonFromResponse:
    """Tests for _extract_json_from_response method."""

    def test_extract_json_from_code_block(self):
        """Test extracting JSON from markdown code block.

        Verifies JSON extraction from ```json...``` format.
        """
        service = TrainingService()
        response = """
        Here is the plan:
        ```json
        {"day": "2024-01-15", "name": "Back Day", "timeRequired": 60, "exercises": []}
        ```
        """

        result = service._extract_json_from_response(response)

        assert result["day"] == "2024-01-15"
        assert result["name"] == "Back Day"

    def test_extract_json_from_code_block_without_json_tag(self):
        """Test extracting JSON from code block without 'json' tag.

        Verifies JSON extraction from ``` ... ``` format.
        """
        service = TrainingService()
        response = """
        ```
        {"day": "2024-01-15", "exercises": []}
        ```
        """

        result = service._extract_json_from_response(response)

        assert result["day"] == "2024-01-15"

    def test_extract_raw_json_object(self):
        """Test extracting raw JSON object without code block.

        Verifies JSON extraction from plain JSON.
        """
        service = TrainingService()
        response = '{"day": "2024-01-15", "name": "Day 1", "exercises": []}'

        result = service._extract_json_from_response(response)

        assert result["day"] == "2024-01-15"

    def test_extract_json_with_surrounding_text(self):
        """Test extracting JSON with surrounding text.

        Verifies JSON extraction when mixed with other text.
        """
        service = TrainingService()
        response = """
        Based on your request, here is the plan:
        ```json
        {"day": "Monday", "exercises": [{"name": "Push-ups"}]}
        ```
        This plan is suitable for your level.
        """

        result = service._extract_json_from_response(response)

        assert result["day"] == "Monday"
        assert len(result["exercises"]) == 1

    def test_extract_json_invalid_json_raises_error(self):
        """Test extracting invalid JSON raises TrainingGenerationError.

        Verifies proper error handling for malformed JSON.
        """
        service = TrainingService()
        response = "```json\n{invalid json}\n```"

        with pytest.raises(TrainingGenerationError):
            service._extract_json_from_response(response)

    def test_extract_json_no_json_found_raises_error(self):
        """Test no JSON found raises TrainingGenerationError.

        Verifies error when JSON cannot be extracted.
        """
        service = TrainingService()
        response = "This response has no JSON in it at all"

        with pytest.raises(TrainingGenerationError):
            service._extract_json_from_response(response)


class TestGenerateTrainingPlan:
    """Tests for generate_training_plan method."""

    def test_generate_training_plan_calls_planner_agent(
        self,
        mock_planner_agent,
        mock_exercise_agent,
    ):
        """Test generate_training_plan invokes planner agent.

        Verifies planner agent is called with correct parameters.
        """
        with patch(
            "api.services.training_service.create_planner_agent",
            return_value=mock_planner_agent,
        ):
            with patch(
                "api.services.training_service.create_exercise_agent",
                return_value=mock_exercise_agent,
            ):
                service = TrainingService()

                service.generate_training_plan(
                    age=30,
                    weight=80.0,
                    target_weight=75.0,
                    difficulty="Intermediate",
                )

                mock_planner_agent.invoke.assert_called_once()

    def test_generate_training_plan_creates_exercise_agent(
        self,
        mock_planner_agent,
        mock_exercise_agent,
    ):
        """Test generate_training_plan creates exercise agent.

        Verifies exercise agent is created.
        """
        with patch(
            "api.services.training_service.create_planner_agent",
            return_value=mock_planner_agent,
        ):
            with patch(
                "api.services.training_service.create_exercise_agent",
                return_value=mock_exercise_agent,
            ) as mock_create_exercise:
                service = TrainingService()

                service.generate_training_plan()

                mock_create_exercise.assert_called_once()

    def test_generate_training_plan_invokes_exercise_agent_for_each_training(
        self,
        mock_planner_agent,
        mock_exercise_agent,
    ):
        """Test generate_training_plan invokes exercise agent for each training day.

        Verifies exercise agent is called multiple times for multiple training days.
        """
        # Setup planner to return 2 training days
        week_plan = MagicMock()
        week_plan.weekStart = "2024-01-15"
        week_plan.weekEnd = "2024-01-21"
        training_days = [
            MagicMock(day="2024-01-15", name="Day 1", bodyParts=["back"]),
            MagicMock(day="2024-01-16", name="Day 2", bodyParts=["legs"]),
        ]
        week_plan.trainings = training_days
        mock_planner_agent.invoke.return_value = week_plan

        with patch(
            "api.services.training_service.create_planner_agent",
            return_value=mock_planner_agent,
        ):
            with patch(
                "api.services.training_service.create_exercise_agent",
                return_value=mock_exercise_agent,
            ):
                service = TrainingService()

                service.generate_training_plan()

                # Exercise agent follows resolved target dates in selected range.
                assert mock_exercise_agent.call_count == 3

    def test_generate_training_plan_returns_complete_plan(
        self,
        mock_planner_agent,
        mock_exercise_agent,
    ):
        """Test generate_training_plan returns complete training plan.

        Verifies response structure and content.
        """
        with patch(
            "api.services.training_service.create_planner_agent",
            return_value=mock_planner_agent,
        ):
            with patch(
                "api.services.training_service.create_exercise_agent",
                return_value=mock_exercise_agent,
            ):
                service = TrainingService()

                result = service.generate_training_plan(difficulty="Advanced")

                assert "trainings" in result
                assert "difficulty" in result
                assert result["difficulty"] == "Advanced"
                assert isinstance(result["trainings"], list)

    def test_generate_training_plan_with_different_difficulties(
        self,
        mock_planner_agent,
        mock_exercise_agent,
    ):
        """Test generate_training_plan with different difficulty levels.

        Verifies plan is generated for all difficulty levels.
        """
        with patch(
            "api.services.training_service.create_planner_agent",
            return_value=mock_planner_agent,
        ):
            with patch(
                "api.services.training_service.create_exercise_agent",
                return_value=mock_exercise_agent,
            ):
                service = TrainingService()

                for difficulty in ["Novice", "Intermediate", "Advanced"]:
                    result = service.generate_training_plan(difficulty=difficulty)
                    assert result["difficulty"] == difficulty

    def test_generate_training_plan_with_various_ages(
        self,
        mock_planner_agent,
        mock_exercise_agent,
    ):
        """Test generate_training_plan with various ages.

        Verifies plan generation for different age groups.
        """
        with patch(
            "api.services.training_service.create_planner_agent",
            return_value=mock_planner_agent,
        ):
            with patch(
                "api.services.training_service.create_exercise_agent",
                return_value=mock_exercise_agent,
            ):
                service = TrainingService()

                for age in [16, 30, 65]:
                    result = service.generate_training_plan(age=age)
                    assert "trainings" in result

    def test_generate_training_plan_planner_agent_error_raises(
        self,
        mock_planner_agent,
    ):
        """Test generate_training_plan handles planner agent error.

        Verifies TrainingGenerationError is raised when planner fails.
        """
        mock_planner_agent.invoke.side_effect = ValueError("API Error")

        with patch(
            "api.services.training_service.create_planner_agent",
            return_value=mock_planner_agent,
        ):
            service = TrainingService()

            with pytest.raises(TrainingGenerationError):
                service.generate_training_plan()

    def test_generate_training_plan_exercise_agent_creation_error_raises(self):
        """Test generate_training_plan handles exercise agent creation error.

        Verifies error when exercise agent creation fails.
        """
        mock_planner_agent = MagicMock()
        week_plan = MagicMock()
        week_plan.trainings = [MagicMock(day="2024-01-15", bodyParts=["back"])]
        mock_planner_agent.invoke.return_value = week_plan

        with patch(
            "api.services.training_service.create_planner_agent",
            return_value=mock_planner_agent,
        ):
            with patch(
                "api.services.training_service.create_exercise_agent",
                side_effect=ValueError("Agent creation failed"),
            ):
                service = TrainingService()

                with pytest.raises(TrainingGenerationError):
                    service.generate_training_plan()

    def test_generate_training_plan_exercise_agent_invocation_error_raises(
        self,
        mock_planner_agent,
        mock_exercise_agent,
    ):
        """Test generate_training_plan handles exercise agent invocation error.

        Verifies error when exercise agent invocation fails.
        """
        mock_exercise_agent.side_effect = ValueError("Agent invocation failed")

        with patch(
            "api.services.training_service.create_planner_agent",
            return_value=mock_planner_agent,
        ):
            with patch(
                "api.services.training_service.create_exercise_agent",
                return_value=mock_exercise_agent,
            ):
                service = TrainingService()

                with pytest.raises(TrainingGenerationError):
                    service.generate_training_plan()

    def test_generate_training_plan_uses_correct_parameters(
        self,
        mock_planner_agent,
        mock_exercise_agent,
    ):
        """Test generate_training_plan passes correct parameters to agents.

        Verifies all parameters are forwarded correctly.
        """
        with patch(
            "api.services.training_service.create_planner_agent",
            return_value=mock_planner_agent,
        ) as mock_create_planner:
            with patch(
                "api.services.training_service.create_exercise_agent",
                return_value=mock_exercise_agent,
            ):
                service = TrainingService()

                age, weight, target_weight = 25, 75.5, 70.0
                service.generate_training_plan(
                    age=age,
                    weight=weight,
                    target_weight=target_weight,
                    difficulty="Novice",
                    selected_days=["friday", "monday", "wednesday"],
                )

                # Verify create_planner_agent was called with correct params
                call_kwargs = mock_create_planner.call_args.kwargs
                assert call_kwargs["age"] == age
                assert call_kwargs["weight"] == weight
                assert call_kwargs["target_weight"] == target_weight
                assert call_kwargs["difficulty"] == "Novice"
                assert call_kwargs["selected_days"] == [
                    "monday",
                    "wednesday",
                    "friday",
                ]

    def test_generate_training_plan_uses_default_parameters(
        self,
        mock_planner_agent,
        mock_exercise_agent,
    ):
        """Test generate_training_plan uses default parameters.

        Verifies default values are applied when not specified.
        """
        with patch(
            "api.services.training_service.create_planner_agent",
            return_value=mock_planner_agent,
        ) as mock_create_planner:
            with patch(
                "api.services.training_service.create_exercise_agent",
                return_value=mock_exercise_agent,
            ):
                service = TrainingService()

                service.generate_training_plan()

                call_kwargs = mock_create_planner.call_args.kwargs
                # Verify defaults are used
                assert "age" in call_kwargs
                assert "weight" in call_kwargs
                assert "target_weight" in call_kwargs
                assert "difficulty" in call_kwargs
                assert call_kwargs["selected_days"] == [
                    "monday",
                    "thursday",
                    "saturday",
                ]


class TestExerciseReplacementSuggestions:
    """Tests for replacement suggestion flow."""

    @patch("api.services.training_service.fetch_exercise_details_by_id")
    @patch("api.services.training_service.fetch_exercises_list")
    def test_resolve_context_from_primary_muscles(
        self,
        mock_fetch_list,
        mock_fetch_details,
    ):
        service = TrainingService()
        mock_fetch_list.return_value = {"results": [{"id": 11}]}
        mock_fetch_details.return_value = {
            "id": 11,
            "name": "Barbell Curl",
            "primary_muscles": ["Biceps"],
            "difficulty": "Intermediate",
            "category": "Barbell",
        }

        result = service.suggest_exercise_replacements(
            current_exercise={"exercise_id": 10, "primary_muscles": ["Biceps"]},
            body_parts=["Chest"],
            mode="manual",
            query=None,
            limit=20,
        )

        assert result["context_source"] == "exercise_primary_muscles"
        assert result["fallback_used"] is False
        assert len(result["suggestions"]) == 1

    @patch("api.services.training_service.fetch_exercise_details_by_id")
    @patch("api.services.training_service.fetch_exercises_list")
    def test_resolve_context_from_body_parts(
        self,
        mock_fetch_list,
        mock_fetch_details,
    ):
        service = TrainingService()
        mock_fetch_list.return_value = {"results": [{"id": 21}]}
        mock_fetch_details.return_value = {
            "id": 21,
            "name": "Romanian Deadlift",
            "primary_muscles": ["Hamstrings"],
            "difficulty": "Intermediate",
            "category": "Barbell",
        }

        result = service.suggest_exercise_replacements(
            current_exercise={},
            body_parts=["Hamstrings"],
            mode="manual",
            query=None,
            limit=20,
        )

        assert result["context_source"] == "training_day_body_parts"
        assert result["fallback_used"] is False

    @patch("api.services.training_service.fetch_exercise_details_by_id")
    @patch("api.services.training_service.fetch_exercises_list")
    def test_resolve_context_random_top_fallback(
        self,
        mock_fetch_list,
        mock_fetch_details,
    ):
        service = TrainingService()
        mock_fetch_list.return_value = {"results": [{"id": 31}]}
        mock_fetch_details.return_value = {
            "id": 31,
            "name": "Push Up",
            "primary_muscles": ["Chest"],
            "difficulty": "Novice",
            "category": "Bodyweight",
        }

        result = service.suggest_exercise_replacements(
            current_exercise={},
            body_parts=[],
            mode="manual",
            query=None,
            limit=20,
        )

        assert result["context_source"] == "random_top"
        assert result["fallback_used"] is True

    @patch("api.services.training_service.create_exercise_replace_agent")
    @patch("api.services.training_service.fetch_exercise_details_by_id")
    @patch("api.services.training_service.fetch_exercises_list")
    def test_ai_mode_returns_three_suggestions(
        self,
        mock_fetch_list,
        mock_fetch_details,
        mock_create_agent,
    ):
        service = TrainingService()
        mock_fetch_list.return_value = {"results": [{"id": 41}, {"id": 42}, {"id": 43}]}
        mock_fetch_details.side_effect = [
            {"id": 41, "name": "A", "primary_muscles": ["Chest"], "difficulty": "Intermediate", "category": "Cable"},
            {"id": 42, "name": "B", "primary_muscles": ["Chest"], "difficulty": "Intermediate", "category": "Cable"},
            {"id": 43, "name": "C", "primary_muscles": ["Chest"], "difficulty": "Intermediate", "category": "Cable"},
        ]
        mock_create_agent.return_value = MagicMock(return_value=[41, 42, 43])

        result = service.suggest_exercise_replacements(
            current_exercise={"exercise_id": 99, "primary_muscles": ["Chest"]},
            body_parts=["Chest"],
            mode="ai",
            query=None,
            limit=20,
        )

        assert result["mode"] == "ai"
        assert len(result["suggestions"]) == 3

    @patch("api.services.training_service.create_exercise_replace_agent")
    @patch("api.services.training_service.fetch_exercise_details_by_id")
    @patch("api.services.training_service.fetch_exercises_list")
    def test_ai_mode_invalid_agent_result_falls_back(
        self,
        mock_fetch_list,
        mock_fetch_details,
        mock_create_agent,
    ):
        service = TrainingService()
        mock_fetch_list.return_value = {"results": [{"id": 51}, {"id": 52}, {"id": 53}]}
        mock_fetch_details.side_effect = [
            {"id": 51, "name": "A", "primary_muscles": ["Back"], "difficulty": "Intermediate", "category": "Cable"},
            {"id": 52, "name": "B", "primary_muscles": ["Back"], "difficulty": "Intermediate", "category": "Cable"},
            {"id": 53, "name": "C", "primary_muscles": ["Back"], "difficulty": "Intermediate", "category": "Cable"},
        ]
        mock_create_agent.return_value = MagicMock(return_value=[9999])

        result = service.suggest_exercise_replacements(
            current_exercise={"exercise_id": 1, "primary_muscles": ["Back"]},
            body_parts=["Back"],
            mode="ai",
            query=None,
            limit=20,
        )

        assert result["fallback_used"] is True
        assert len(result["suggestions"]) == 3


class TestDashboardStats:
    """Tests for dashboard stats aggregation."""

    def test_get_dashboard_stats_aggregates_counts(self):
        """Service should aggregate trend, statuses and KPIs from repository data."""
        service = TrainingService()
        training_repository = MagicMock()
        training_repository.get_training_days_for_window.return_value = [
            {"training_id": "plan_1", "day": "2026-02-19", "exercises_count": 4},
            {"training_id": "plan_1", "day": "2026-02-20", "exercises_count": 5},
        ]
        training_repository.get_completion_summary_for_window.return_value = {
            "plan_1|2026-02-19": {"completed": 2, "not_completed": 1},
            "plan_1|2026-02-20": {"completed": 3, "not_completed": 1},
        }

        stats = service.get_dashboard_stats(
            user_id="user_1",
            window_days=2,
            training_repository=training_repository,
        )

        assert stats["kpis"]["scheduled_trainings"] == 2
        assert stats["kpis"]["not_completed_exercises"] == 2
        assert stats["status_distribution"][0]["value"] == 5
        assert stats["status_distribution"][1]["value"] == 2
        assert stats["status_distribution"][2]["value"] == 2
        assert len(stats["training_trend"]) == 2
