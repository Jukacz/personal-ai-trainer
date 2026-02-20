"""Tests for auth controller user creation and mock seed behavior."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.controllers.auth_controller import AuthController
from api.schemas.auth_requests import GoogleAuthRequest, RegisterRequest


def _build_user(user_id: str, email: str, name: str = "Test User") -> dict:
    return {
        "_id": user_id,
        "email": email,
        "name": name,
        "password_hash": "hashed",
        "profile": {"age": None, "weight": None, "target_weight": None},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


class TestRegisterMockSeed:
    """Tests for registration flow with mock seed integration."""

    @patch("api.controllers.auth_controller.create_refresh_token", return_value="refresh-token")
    @patch("api.controllers.auth_controller.create_access_token", return_value="access-token")
    @patch("api.controllers.auth_controller.hash_password", return_value="hashed-password")
    def test_register_calls_seed_for_new_user(
        self,
        _mock_hash_password,
        _mock_access_token,
        _mock_refresh_token,
        mock_user_repository,
    ):
        mock_user_repository.get_by_email.return_value = None
        mock_user_repository.create.return_value = _build_user(
            user_id="507f1f77bcf86cd799439011",
            email="new@example.com",
            name="New User",
        )
        mock_seed_service = MagicMock()
        mock_seed_service.is_auto_seed_enabled.return_value = True

        controller = AuthController(
            repository=mock_user_repository,
            mock_seed_service=mock_seed_service,
        )

        request = RegisterRequest(
            email="new@example.com",
            password="StrongPass123",
            name="New User",
        )
        controller.register(request)

        mock_seed_service.seed_for_user.assert_called_once_with(
            user_id="507f1f77bcf86cd799439011",
            execute=True,
        )

    @patch("api.controllers.auth_controller.create_refresh_token", return_value="refresh-token")
    @patch("api.controllers.auth_controller.create_access_token", return_value="access-token")
    @patch("api.controllers.auth_controller.hash_password", return_value="hashed-password")
    def test_register_seed_error_does_not_fail_registration(
        self,
        _mock_hash_password,
        _mock_access_token,
        _mock_refresh_token,
        mock_user_repository,
    ):
        mock_user_repository.get_by_email.return_value = None
        mock_user_repository.create.return_value = _build_user(
            user_id="507f1f77bcf86cd799439012",
            email="seed-error@example.com",
            name="Seed Error",
        )
        mock_seed_service = MagicMock()
        mock_seed_service.is_auto_seed_enabled.return_value = True
        mock_seed_service.seed_for_user.side_effect = RuntimeError("seed failed")

        controller = AuthController(
            repository=mock_user_repository,
            mock_seed_service=mock_seed_service,
        )

        request = RegisterRequest(
            email="seed-error@example.com",
            password="StrongPass123",
            name="Seed Error",
        )
        response, refresh_token = controller.register(request)

        assert response.user.email == "seed-error@example.com"
        assert refresh_token == "refresh-token"


class TestGoogleAuthMockSeed:
    """Tests for Google auth flow with mock seed integration."""

    @pytest.mark.asyncio
    @patch("api.controllers.auth_controller.create_refresh_token", return_value="refresh-token")
    @patch("api.controllers.auth_controller.create_access_token", return_value="access-token")
    async def test_google_auth_calls_seed_only_for_new_user(
        self,
        _mock_access_token,
        _mock_refresh_token,
        mock_user_repository,
    ):
        mock_google_service = MagicMock()
        mock_google_service.exchange_code = AsyncMock(
            return_value={
                "sub": "google-sub-123",
                "email": "google-new@example.com",
                "name": "Google New",
            }
        )
        mock_user_repository.get_by_google_id.return_value = None
        mock_user_repository.get_by_email.return_value = None
        mock_user_repository.create.return_value = _build_user(
            user_id="507f1f77bcf86cd799439013",
            email="google-new@example.com",
            name="Google New",
        )
        mock_seed_service = MagicMock()
        mock_seed_service.is_auto_seed_enabled.return_value = True

        controller = AuthController(
            repository=mock_user_repository,
            google_service=mock_google_service,
            mock_seed_service=mock_seed_service,
        )

        request = GoogleAuthRequest(code="code-123", redirect_uri="http://localhost/callback")
        await controller.google_auth(request)

        mock_seed_service.seed_for_user.assert_called_once_with(
            user_id="507f1f77bcf86cd799439013",
            execute=True,
        )

    @pytest.mark.asyncio
    @patch("api.controllers.auth_controller.create_refresh_token", return_value="refresh-token")
    @patch("api.controllers.auth_controller.create_access_token", return_value="access-token")
    async def test_google_auth_does_not_seed_for_existing_user(
        self,
        _mock_access_token,
        _mock_refresh_token,
        mock_user_repository,
    ):
        existing_user = _build_user(
            user_id="507f1f77bcf86cd799439014",
            email="existing@example.com",
            name="Existing",
        )
        mock_google_service = MagicMock()
        mock_google_service.exchange_code = AsyncMock(
            return_value={
                "sub": "google-sub-existing",
                "email": "existing@example.com",
                "name": "Existing",
            }
        )
        mock_user_repository.get_by_google_id.return_value = existing_user
        mock_seed_service = MagicMock()
        mock_seed_service.is_auto_seed_enabled.return_value = True

        controller = AuthController(
            repository=mock_user_repository,
            google_service=mock_google_service,
            mock_seed_service=mock_seed_service,
        )

        request = GoogleAuthRequest(code="code-abc", redirect_uri="http://localhost/callback")
        await controller.google_auth(request)

        mock_seed_service.seed_for_user.assert_not_called()
