"""Tests for OAuth authentication flow."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    from app.main import create_app

    app = create_app()

    # Import and include auth router
    from app.api.auth import router as auth_router

    app.include_router(auth_router)

    with TestClient(app) as client:
        yield client


class TestLoginEndpoint:
    """Tests for the /auth/login endpoint."""

    def test_login_redirects_to_monzo(self, client: TestClient) -> None:
        """Login should redirect to Monzo OAuth authorization URL."""
        response = client.get("/auth/login", follow_redirects=False)

        assert response.status_code == 307
        location = response.headers.get("location")
        assert location is not None
        assert location.startswith("https://auth.monzo.com/")

    def test_login_includes_required_oauth_params(self, client: TestClient) -> None:
        """Login redirect should include required OAuth parameters."""
        response = client.get("/auth/login", follow_redirects=False)

        location = response.headers.get("location")
        parsed = urlparse(location)
        params = parse_qs(parsed.query)

        assert "client_id" in params
        assert "redirect_uri" in params
        assert "response_type" in params
        assert params["response_type"][0] == "code"

    def test_login_includes_state_parameter(self, client: TestClient) -> None:
        """Login redirect should include state parameter for CSRF protection."""
        response = client.get("/auth/login", follow_redirects=False)

        location = response.headers.get("location")
        parsed = urlparse(location)
        params = parse_qs(parsed.query)

        assert "state" in params
        assert len(params["state"][0]) >= 16  # Sufficient entropy


class TestCallbackEndpoint:
    """Tests for the /auth/callback endpoint."""

    @pytest.mark.asyncio
    async def test_callback_exchanges_code_for_tokens(self, client: TestClient) -> None:
        """Callback should exchange authorization code for tokens."""
        mock_response = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        with patch("app.api.auth.monzo_exchange_code", new_callable=AsyncMock) as mock_exchange:
            mock_exchange.return_value = mock_response

            with patch("app.api.auth.store_tokens", new_callable=AsyncMock) as mock_store:
                response = client.get("/auth/callback?code=test_code&state=test_state")

                assert response.status_code == 200
                mock_exchange.assert_called_once_with("test_code")
                mock_store.assert_called_once()

    def test_callback_without_code_returns_error(self, client: TestClient) -> None:
        """Callback without authorization code should return error."""
        response = client.get("/auth/callback")

        assert response.status_code == 400
        assert "code" in response.json()["detail"].lower()

    def test_callback_with_error_returns_error(self, client: TestClient) -> None:
        """Callback with OAuth error should return error."""
        response = client.get("/auth/callback?error=access_denied&error_description=User%20denied")

        assert response.status_code == 400
        assert "denied" in response.json()["detail"].lower()


class TestAuthStatusEndpoint:
    """Tests for the /auth/status endpoint."""

    @pytest.mark.asyncio
    async def test_status_returns_authenticated_when_valid_token(self, client: TestClient) -> None:
        """Status should return authenticated when valid token exists."""
        from app.models import Auth

        mock_auth = Auth(
            access_token="test_token",
            refresh_token="test_refresh",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        with patch("app.api.auth.get_current_auth", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_auth

            response = client.get("/auth/status")

            assert response.status_code == 200
            data = response.json()
            assert data["authenticated"] is True
            assert "expires_at" in data

    @pytest.mark.asyncio
    async def test_status_returns_unauthenticated_when_no_token(self, client: TestClient) -> None:
        """Status should return unauthenticated when no token exists."""
        with patch("app.api.auth.get_current_auth", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            response = client.get("/auth/status")

            assert response.status_code == 200
            data = response.json()
            assert data["authenticated"] is False

    @pytest.mark.asyncio
    async def test_status_returns_expired_when_token_expired(self, client: TestClient) -> None:
        """Status should indicate expired when token has expired."""
        from app.models import Auth

        mock_auth = Auth(
            access_token="test_token",
            refresh_token="test_refresh",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )

        with patch("app.api.auth.get_current_auth", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_auth

            response = client.get("/auth/status")

            assert response.status_code == 200
            data = response.json()
            assert data["authenticated"] is True
            assert data["expired"] is True


class TestMonzoClient:
    """Tests for the Monzo API client."""

    @pytest.mark.asyncio
    async def test_exchange_code_calls_monzo_api(self) -> None:
        """Exchange code should call Monzo token endpoint."""
        from unittest.mock import MagicMock

        from app.services.monzo import exchange_code_for_tokens

        mock_response_data = {
            "access_token": "test_access",
            "refresh_token": "test_refresh",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        # Create mock response
        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        # Mock the AsyncClient context manager
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with patch("httpx.AsyncClient") as MockAsyncClient:
            MockAsyncClient.return_value.__aenter__.return_value = mock_client
            MockAsyncClient.return_value.__aexit__.return_value = None

            result = await exchange_code_for_tokens("test_code")

            assert result["access_token"] == "test_access"
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_token_calls_monzo_api(self) -> None:
        """Refresh token should call Monzo token endpoint."""
        from unittest.mock import MagicMock

        from app.services.monzo import refresh_access_token

        mock_response_data = {
            "access_token": "new_access",
            "refresh_token": "new_refresh",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        # Create mock response
        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        # Mock the AsyncClient context manager
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with patch("httpx.AsyncClient") as MockAsyncClient:
            MockAsyncClient.return_value.__aenter__.return_value = mock_client
            MockAsyncClient.return_value.__aexit__.return_value = None

            result = await refresh_access_token("old_refresh")

            assert result["access_token"] == "new_access"
            mock_client.post.assert_called_once()
