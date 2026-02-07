"""Tests for FastAPI application."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    from app.main import create_app

    app = create_app()
    with TestClient(app) as client:
        yield client


class TestHealthCheck:
    """Tests for the health check endpoint."""

    def test_health_check_returns_healthy(self, client: TestClient) -> None:
        """Health check endpoint should return healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestAppConfiguration:
    """Tests for app configuration."""

    def test_app_has_cors_middleware(self, client: TestClient) -> None:
        """App should have CORS middleware configured."""
        # Preflight request
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

    def test_app_metadata(self) -> None:
        """App should have proper metadata."""
        from app.main import create_app

        app = create_app()
        assert app.title == "Monzo Analysis"
        assert app.version == "0.1.0"

    def test_cors_configurable_via_settings(self) -> None:
        """CORS origins should be configurable via settings."""
        from app.config import Settings
        from app.main import create_app

        settings = Settings(
            database_url="postgresql+asyncpg://test:test@localhost/test",
            monzo_client_id="test",
            monzo_client_secret="test",
            monzo_redirect_uri="http://localhost:8000/auth/callback",
            secret_key="test-key",
            cors_origins="http://192.168.1.100,http://mymac.local",
        )
        app = create_app(settings)

        with TestClient(app) as tc:
            # Should allow the custom origin
            response = tc.options(
                "/health",
                headers={
                    "Origin": "http://192.168.1.100",
                    "Access-Control-Request-Method": "GET",
                },
            )
            assert response.headers.get("access-control-allow-origin") == "http://192.168.1.100"

    def test_cors_rejects_unlisted_origin(self) -> None:
        """CORS should not allow origins not in the list."""
        from app.config import Settings
        from app.main import create_app

        settings = Settings(
            database_url="postgresql+asyncpg://test:test@localhost/test",
            monzo_client_id="test",
            monzo_client_secret="test",
            monzo_redirect_uri="http://localhost:8000/auth/callback",
            secret_key="test-key",
            cors_origins="http://localhost:3000",
        )
        app = create_app(settings)

        with TestClient(app) as tc:
            response = tc.options(
                "/health",
                headers={
                    "Origin": "http://evil.com",
                    "Access-Control-Request-Method": "GET",
                },
            )
            # Should not include the origin header for unlisted origins
            assert response.headers.get("access-control-allow-origin") != "http://evil.com"

    def test_cors_handles_whitespace_in_origins(self) -> None:
        """CORS should trim whitespace from comma-separated origins."""
        from app.config import Settings
        from app.main import create_app

        settings = Settings(
            database_url="postgresql+asyncpg://test:test@localhost/test",
            monzo_client_id="test",
            monzo_client_secret="test",
            monzo_redirect_uri="http://localhost:8000/auth/callback",
            secret_key="test-key",
            cors_origins="http://localhost:3000 , http://localhost:5173 ",
        )
        app = create_app(settings)

        with TestClient(app) as tc:
            response = tc.options(
                "/health",
                headers={
                    "Origin": "http://localhost:5173",
                    "Access-Control-Request-Method": "GET",
                },
            )
            assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
