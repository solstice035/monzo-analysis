"""Pytest configuration and shared fixtures."""

import os
from unittest.mock import patch

import pytest

# Set test environment variables before any imports
TEST_ENV = {
    "DATABASE_URL": "postgresql+asyncpg://test:test@localhost/test",
    "MONZO_CLIENT_ID": "test-client-id",
    "MONZO_CLIENT_SECRET": "test-client-secret",
    "MONZO_REDIRECT_URI": "http://localhost:8000/auth/callback",
    "SECRET_KEY": "test-secret-key-for-testing",
}


@pytest.fixture(autouse=True)
def mock_env():
    """Mock environment variables for all tests."""
    with patch.dict(os.environ, TEST_ENV):
        yield
