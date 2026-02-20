"""Tests for range planning and quick-training helpers."""

from api.services.training_service import TrainingService


class TestTrainingModesService:
    """Coverage for date-range planning helpers."""

    def test_get_training_dates_in_range_filters_only_window(self):
        service = TrainingService()

        dates = service.get_training_dates_in_range(
            start_date="2026-02-23",  # monday
            end_date="2026-03-08",    # sunday
            selected_days=["monday", "wednesday", "friday"],
            trainings_per_week=3,
        )

        assert dates == [
            "2026-02-23",
            "2026-02-25",
            "2026-02-27",
            "2026-03-02",
            "2026-03-04",
            "2026-03-06",
        ]

    def test_get_training_dates_in_range_returns_empty_when_start_after_end(self):
        service = TrainingService()

        dates = service.get_training_dates_in_range(
            start_date="2026-03-10",
            end_date="2026-03-01",
            selected_days=["monday"],
            trainings_per_week=1,
        )

        assert dates == []
