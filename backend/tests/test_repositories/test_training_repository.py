"""Test suite for training repository.

Tests the data access layer including:
- Saving training plans to MongoDB
- Retrieving training plans
- Creating and updating task records
- Retrieving task status
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from bson import ObjectId

from api.repositories.training_repository import TrainingRepository


class TestTrainingRepositorySaveTrainingPlan:
    """Tests for save_training_plan method."""

    def test_save_training_plan_delegates_to_db_function(self):
        """Test that save_training_plan delegates to database module.

        Verifies database.mongodb.save_training_plan is called.
        """
        with patch(
            "api.repositories.training_repository.db_save_training_plan",
            return_value="507f1f77bcf86cd799439012",
        ) as mock_db_save:
            repo = TrainingRepository()
            plan_data = {
                "trainings": [],
                "difficulty": "Intermediate",
            }

            result = repo.save_training_plan(plan_data, user_id="test_user_123")

            assert result == "507f1f77bcf86cd799439012"
            mock_db_save.assert_called_once_with(
                plan_data,
                user_id="test_user_123",
            )

    def test_save_training_plan_without_user_id(self):
        """Test saving training plan without user association.

        Verifies user_id can be optional.
        """
        with patch(
            "api.repositories.training_repository.db_save_training_plan",
            return_value="507f1f77bcf86cd799439012",
        ) as mock_db_save:
            repo = TrainingRepository()
            plan_data = {"trainings": []}

            repo.save_training_plan(plan_data)

            mock_db_save.assert_called_once_with(plan_data, user_id=None)


class TestTrainingRepositoryGetTrainingsListMethod:
    """Tests for get_trainings_list method."""

    def test_get_trainings_list_delegates_to_db_function(self):
        """Test that get_trainings_list delegates to database module.

        Verifies database.mongodb.get_all_trainings is called.
        """
        expected_result = {
            "total": 5,
            "trainings": [
                {"id": "id1", "created_at": None, "difficulty": "Intermediate"}
            ],
        }

        with patch(
            "api.repositories.training_repository.db_get_all_trainings",
            return_value=expected_result,
        ) as mock_db_get:
            repo = TrainingRepository()

            result = repo.get_trainings_list(limit=10, offset=0)

            assert result == expected_result
            mock_db_get.assert_called_once_with(
                limit=10,
                offset=0,
                user_id=None,
            )

    def test_get_trainings_list_with_pagination(self):
        """Test get_trainings_list with limit and offset.

        Verifies pagination parameters are passed correctly.
        """
        with patch(
            "api.repositories.training_repository.db_get_all_trainings",
            return_value={"total": 100, "trainings": []},
        ) as mock_db_get:
            repo = TrainingRepository()

            repo.get_trainings_list(limit=20, offset=40)

            mock_db_get.assert_called_once_with(limit=20, offset=40, user_id=None)

    def test_get_trainings_list_with_user_filter(self):
        """Test get_trainings_list filters by user_id.

        Verifies user_id is passed to database layer.
        """
        with patch(
            "api.repositories.training_repository.db_get_all_trainings",
            return_value={"total": 5, "trainings": []},
        ) as mock_db_get:
            repo = TrainingRepository()

            repo.get_trainings_list(user_id="test_user_123")

            call_kwargs = mock_db_get.call_args.kwargs
            assert call_kwargs["user_id"] == "test_user_123"


class TestTrainingRepositoryGetTrainingById:
    """Tests for get_training_by_id method."""

    def test_get_training_by_id_returns_training(
        self, mock_mongo_client, mock_mongo_database
    ):
        """Test get_training_by_id returns training document.

        Verifies training is retrieved from MongoDB.
        """
        expected_doc = {
            "_id": ObjectId(),
            "trainings": [],
            "createdAt": datetime.now(timezone.utc),
        }

        mock_collection = MagicMock()
        mock_collection.find_one.return_value = expected_doc
        mock_mongo_database.__getitem__.return_value = mock_collection

        with patch(
            "api.repositories.training_repository.get_client",
            return_value=mock_mongo_client,
        ):
            with patch(
                "api.repositories.training_repository.get_database",
                return_value=mock_mongo_database,
            ):
                repo = TrainingRepository()
                training_id = str(expected_doc["_id"])

                result = repo.get_training_by_id(training_id)

                assert result is not None
                assert result["_id"] == str(expected_doc["_id"])

    def test_get_training_by_id_not_found_returns_none(
        self, mock_mongo_client, mock_mongo_database
    ):
        """Test get_training_by_id returns None if not found.

        Verifies None is returned for missing trainings.
        """
        mock_collection = MagicMock()
        mock_collection.find_one.return_value = None
        mock_mongo_database.__getitem__.return_value = mock_collection

        with patch(
            "api.repositories.training_repository.get_client",
            return_value=mock_mongo_client,
        ):
            with patch(
                "api.repositories.training_repository.get_database",
                return_value=mock_mongo_database,
            ):
                repo = TrainingRepository()

                result = repo.get_training_by_id("507f1f77bcf86cd799439012")

                assert result is None

    def test_get_training_by_id_with_invalid_id_returns_none(
        self, mock_mongo_client, mock_mongo_database
    ):
        """Test get_training_by_id handles invalid ObjectId format.

        Verifies None is returned for invalid ID format.
        """
        mock_collection = MagicMock()
        mock_mongo_database.__getitem__.return_value = mock_collection

        with patch(
            "api.repositories.training_repository.get_client",
            return_value=mock_mongo_client,
        ):
            with patch(
                "api.repositories.training_repository.get_database",
                return_value=mock_mongo_database,
            ):
                repo = TrainingRepository()

                result = repo.get_training_by_id("invalid-id-format")

                assert result is None

    def test_get_training_by_id_filters_by_user(
        self, mock_mongo_client, mock_mongo_database
    ):
        """Test get_training_by_id includes user_id in query.

        Verifies security - only user's training is returned.
        """
        expected_doc = {
            "_id": ObjectId(),
            "trainings": [],
            "createdAt": datetime.now(timezone.utc),
            "user_id": "test_user_123",
        }

        mock_collection = MagicMock()
        mock_collection.find_one.return_value = expected_doc
        mock_mongo_database.__getitem__.return_value = mock_collection

        with patch(
            "api.repositories.training_repository.get_client",
            return_value=mock_mongo_client,
        ):
            with patch(
                "api.repositories.training_repository.get_database",
                return_value=mock_mongo_database,
            ):
                repo = TrainingRepository()
                training_id = str(expected_doc["_id"])

                repo.get_training_by_id(training_id, user_id="test_user_123")

                call_args = mock_collection.find_one.call_args
                query = call_args[0][0]
                assert query["user_id"] == "test_user_123"


class TestTrainingRepositoryConflicts:
    """Tests for conflict helpers."""

    def test_get_conflicts_for_dates_returns_matching_days(
        self, mock_mongo_client, mock_mongo_database
    ):
        """Test repository extracts conflicts from matching plans."""
        mock_collection = MagicMock()
        mock_collection.find.return_value = [
            {
                "_id": ObjectId("507f1f77bcf86cd799439012"),
                "trainings": [
                    {"day": "2024-01-15", "name": "Plecy"},
                    {"day": "2024-01-18", "name": "Nogi"},
                ],
            }
        ]
        mock_mongo_database.__getitem__.return_value = mock_collection

        with patch(
            "api.repositories.training_repository.get_client",
            return_value=mock_mongo_client,
        ), patch(
            "api.repositories.training_repository.get_database",
            return_value=mock_mongo_database,
        ):
            repo = TrainingRepository()
            result = repo.get_conflicts_for_dates(["2024-01-15"], user_id="test_user_123")

            assert len(result) == 1
            assert result[0]["date"] == "2024-01-15"

    def test_remove_conflicting_days_updates_or_deletes_documents(
        self, mock_mongo_client, mock_mongo_database
    ):
        """Test remove_conflicting_days prunes day entries and deletes empty plans."""
        mock_collection = MagicMock()
        mock_collection.find.return_value = [
            {
                "_id": ObjectId("507f1f77bcf86cd799439012"),
                "trainings": [{"day": "2024-01-15", "name": "Plecy"}, {"day": "2024-01-18", "name": "Nogi"}],
            },
            {
                "_id": ObjectId("507f1f77bcf86cd799439013"),
                "trainings": [{"day": "2024-01-15", "name": "Klatka"}],
            },
        ]
        mock_mongo_database.__getitem__.return_value = mock_collection

        with patch(
            "api.repositories.training_repository.get_client",
            return_value=mock_mongo_client,
        ), patch(
            "api.repositories.training_repository.get_database",
            return_value=mock_mongo_database,
        ):
            repo = TrainingRepository()
            affected = repo.remove_conflicting_days(["2024-01-15"], user_id="test_user_123")

            assert affected == 2
            mock_collection.update_one.assert_called_once()
            mock_collection.delete_one.assert_called_once()


class TestTrainingRepositoryCreateTask:
    """Tests for create_task method."""

    def test_create_task_inserts_document(
        self, mock_mongo_client, mock_mongo_database
    ):
        """Test create_task inserts task document.

        Verifies task is created in MongoDB.
        """
        task_id = ObjectId()
        mock_result = MagicMock()
        mock_result.inserted_id = task_id

        mock_collection = MagicMock()
        mock_collection.insert_one.return_value = mock_result
        mock_mongo_database.__getitem__.return_value = mock_collection

        with patch(
            "api.repositories.training_repository.get_client",
            return_value=mock_mongo_client,
        ):
            with patch(
                "api.repositories.training_repository.get_database",
                return_value=mock_mongo_database,
            ):
                repo = TrainingRepository()

                result = repo.create_task(status="pending", message="Test message")

                assert result == str(task_id)
                mock_collection.insert_one.assert_called_once()

    def test_create_task_with_default_values(
        self, mock_mongo_client, mock_mongo_database
    ):
        """Test create_task uses default values.

        Verifies default status and message are applied.
        """
        task_id = ObjectId()
        mock_result = MagicMock()
        mock_result.inserted_id = task_id

        mock_collection = MagicMock()
        mock_collection.insert_one.return_value = mock_result
        mock_mongo_database.__getitem__.return_value = mock_collection

        with patch(
            "api.repositories.training_repository.get_client",
            return_value=mock_mongo_client,
        ):
            with patch(
                "api.repositories.training_repository.get_database",
                return_value=mock_mongo_database,
            ):
                repo = TrainingRepository()

                repo.create_task()

                mock_collection.insert_one.assert_called_once()
                call_args = mock_collection.insert_one.call_args[0][0]
                assert call_args["status"] == "pending"
                assert call_args["created_at"] is not None

    def test_create_task_associates_with_user(
        self, mock_mongo_client, mock_mongo_database
    ):
        """Test create_task associates task with user_id.

        Verifies user_id is included in document.
        """
        task_id = ObjectId()
        mock_result = MagicMock()
        mock_result.inserted_id = task_id

        mock_collection = MagicMock()
        mock_collection.insert_one.return_value = mock_result
        mock_mongo_database.__getitem__.return_value = mock_collection

        with patch(
            "api.repositories.training_repository.get_client",
            return_value=mock_mongo_client,
        ):
            with patch(
                "api.repositories.training_repository.get_database",
                return_value=mock_mongo_database,
            ):
                repo = TrainingRepository()

                repo.create_task(user_id="test_user_123")

                call_args = mock_collection.insert_one.call_args[0][0]
                assert call_args["user_id"] == "test_user_123"


class TestTrainingRepositoryUpdateTaskStatus:
    """Tests for update_task_status method."""

    def test_update_task_status_updates_document(
        self, mock_mongo_client, mock_mongo_database
    ):
        """Test update_task_status updates task document.

        Verifies MongoDB update_one is called.
        """
        mock_result = MagicMock()
        mock_result.modified_count = 1

        mock_collection = MagicMock()
        mock_collection.update_one.return_value = mock_result
        mock_mongo_database.__getitem__.return_value = mock_collection

        with patch(
            "api.repositories.training_repository.get_client",
            return_value=mock_mongo_client,
        ):
            with patch(
                "api.repositories.training_repository.get_database",
                return_value=mock_mongo_database,
            ):
                repo = TrainingRepository()

                success = repo.update_task_status(
                    task_id="507f1f77bcf86cd799439011",
                    status="processing",
                    message="Processing...",
                )

                assert success is True
                mock_collection.update_one.assert_called_once()

    def test_update_task_status_sets_completed_at_for_terminal_states(
        self, mock_mongo_client, mock_mongo_database
    ):
        """Test update_task_status sets completed_at for completed/failed.

        Verifies timestamp is added for terminal states.
        """
        mock_result = MagicMock()
        mock_result.modified_count = 1

        mock_collection = MagicMock()
        mock_collection.update_one.return_value = mock_result
        mock_mongo_database.__getitem__.return_value = mock_collection

        with patch(
            "api.repositories.training_repository.get_client",
            return_value=mock_mongo_client,
        ):
            with patch(
                "api.repositories.training_repository.get_database",
                return_value=mock_mongo_database,
            ):
                repo = TrainingRepository()

                repo.update_task_status(
                    task_id="507f1f77bcf86cd799439011",
                    status="completed",
                    message="Done",
                )

                call_args = mock_collection.update_one.call_args[0]
                update_data = call_args[1]["$set"]
                assert "completed_at" in update_data

    def test_update_task_status_includes_result_and_error(
        self, mock_mongo_client, mock_mongo_database
    ):
        """Test update_task_status includes result and error in update.

        Verifies result and error are properly included.
        """
        mock_result = MagicMock()
        mock_result.modified_count = 1

        mock_collection = MagicMock()
        mock_collection.update_one.return_value = mock_result
        mock_mongo_database.__getitem__.return_value = mock_collection

        with patch(
            "api.repositories.training_repository.get_client",
            return_value=mock_mongo_client,
        ):
            with patch(
                "api.repositories.training_repository.get_database",
                return_value=mock_mongo_database,
            ):
                repo = TrainingRepository()

                repo.update_task_status(
                    task_id="507f1f77bcf86cd799439011",
                    status="completed",
                    message="Done",
                    result={"training_id": "123"},
                    error=None,
                )

                call_args = mock_collection.update_one.call_args[0]
                update_data = call_args[1]["$set"]
                assert update_data["result"] == {"training_id": "123"}

    def test_update_task_status_invalid_id_returns_false(
        self, mock_mongo_client, mock_mongo_database
    ):
        """Test update_task_status returns False for invalid ID.

        Verifies graceful handling of invalid ObjectId format.
        """
        with patch(
            "api.repositories.training_repository.get_client",
            return_value=mock_mongo_client,
        ):
            with patch(
                "api.repositories.training_repository.get_database",
                return_value=mock_mongo_database,
            ):
                repo = TrainingRepository()

                success = repo.update_task_status(
                    task_id="invalid-id",
                    status="completed",
                    message="Done",
                )

                assert success is False


class TestTrainingRepositoryGetTask:
    """Tests for get_task method."""

    def test_get_task_returns_task_document(
        self, mock_mongo_client, mock_mongo_database
    ):
        """Test get_task returns task document.

        Verifies task is retrieved from MongoDB.
        """
        task_doc = {
            "_id": ObjectId(),
            "status": "pending",
            "message": "Processing",
            "created_at": datetime.now(timezone.utc),
        }

        mock_collection = MagicMock()
        mock_collection.find_one.return_value = task_doc
        mock_mongo_database.__getitem__.return_value = mock_collection

        with patch(
            "api.repositories.training_repository.get_client",
            return_value=mock_mongo_client,
        ):
            with patch(
                "api.repositories.training_repository.get_database",
                return_value=mock_mongo_database,
            ):
                repo = TrainingRepository()

                result = repo.get_task("507f1f77bcf86cd799439011")

                assert result is not None
                assert result["_id"] == str(task_doc["_id"])
                assert result["status"] == "pending"

    def test_get_task_not_found_returns_none(
        self, mock_mongo_client, mock_mongo_database
    ):
        """Test get_task returns None if not found.

        Verifies None is returned for missing tasks.
        """
        mock_collection = MagicMock()
        mock_collection.find_one.return_value = None
        mock_mongo_database.__getitem__.return_value = mock_collection

        with patch(
            "api.repositories.training_repository.get_client",
            return_value=mock_mongo_client,
        ):
            with patch(
                "api.repositories.training_repository.get_database",
                return_value=mock_mongo_database,
            ):
                repo = TrainingRepository()

                result = repo.get_task("nonexistent")

                assert result is None

    def test_get_task_filters_by_user(
        self, mock_mongo_client, mock_mongo_database
    ):
        """Test get_task includes user_id in query.

        Verifies security - only user's task is returned.
        """
        task_doc = {
            "_id": ObjectId(),
            "status": "pending",
            "message": "Processing",
            "user_id": "test_user_123",
        }

        mock_collection = MagicMock()
        mock_collection.find_one.return_value = task_doc
        mock_mongo_database.__getitem__.return_value = mock_collection

        with patch(
            "api.repositories.training_repository.get_client",
            return_value=mock_mongo_client,
        ):
            with patch(
                "api.repositories.training_repository.get_database",
                return_value=mock_mongo_database,
            ):
                repo = TrainingRepository()

                repo.get_task("507f1f77bcf86cd799439011", user_id="test_user_123")

                call_args = mock_collection.find_one.call_args[0][0]
                assert call_args["user_id"] == "test_user_123"

    def test_get_task_with_invalid_id_returns_none(
        self, mock_mongo_client, mock_mongo_database
    ):
        """Test get_task handles invalid ObjectId format.

        Verifies None is returned for invalid ID format.
        """
        with patch(
            "api.repositories.training_repository.get_client",
            return_value=mock_mongo_client,
        ):
            with patch(
                "api.repositories.training_repository.get_database",
                return_value=mock_mongo_database,
            ):
                repo = TrainingRepository()

                result = repo.get_task("invalid-id-format")

                assert result is None


class TestTrainingRepositoryExerciseReplacement:
    """Tests for replacing single exercise in training day."""

    def test_replace_training_day_exercise_updates_day_document(self, mock_mongo_client):
        training_days = MagicMock()
        training_days.find_one.return_value = {
            "exercises": [
                {"name": "A", "exercise_id": 1},
                {"name": "B", "exercise_id": 2},
            ]
        }

        with patch(
            "api.repositories.training_repository.get_client",
            return_value=mock_mongo_client,
        ), patch(
            "api.repositories.training_repository.get_training_days_collection",
            return_value=training_days,
        ):
            repo = TrainingRepository()
            result = repo.replace_training_day_exercise(
                training_id="507f1f77bcf86cd799439012",
                day="2026-02-24",
                exercise_index=1,
                exercise={"name": "Z", "exercise_id": 99},
                time_required=24,
                user_id="test_user_123",
            )

            assert result is not None
            assert result["time_required"] == 24
            training_days.update_one.assert_called_once()

    def test_replace_training_day_exercise_invalid_index_returns_none(self, mock_mongo_client):
        training_days = MagicMock()
        training_days.find_one.return_value = {"exercises": [{"name": "A", "exercise_id": 1}]}

        with patch(
            "api.repositories.training_repository.get_client",
            return_value=mock_mongo_client,
        ), patch(
            "api.repositories.training_repository.get_training_days_collection",
            return_value=training_days,
        ):
            repo = TrainingRepository()
            result = repo.replace_training_day_exercise(
                training_id="507f1f77bcf86cd799439012",
                day="2026-02-24",
                exercise_index=5,
                exercise={"name": "Z", "exercise_id": 99},
                time_required=24,
                user_id="test_user_123",
            )

            assert result is None
