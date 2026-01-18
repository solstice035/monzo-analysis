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
