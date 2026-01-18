"""Authentication API endpoints."""

import secrets
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.config import Settings
from app.models import Auth
from app.services.monzo import (
    build_authorization_url,
    calculate_token_expiry,
    exchange_code_for_tokens as monzo_exchange_code,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# In-memory state storage (for CSRF protection)
# In production, use Redis or database
_oauth_states: set[str] = set()


class AuthStatus(BaseModel):
    """Response model for auth status."""

    authenticated: bool
    expired: bool = False
    expires_at: datetime | None = None


# Dependency functions that can be mocked in tests
async def get_current_auth() -> Auth | None:
    """Get the current auth tokens from database.

    This is a placeholder - actual implementation will use database.
    """
    # TODO: Implement database lookup
    return None


async def store_tokens(access_token: str, refresh_token: str, expires_at: datetime) -> Auth:
    """Store OAuth tokens in database.

    This is a placeholder - actual implementation will use database.
    """
    # TODO: Implement database storage
    return Auth(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
    )


@router.get("/login")
async def login() -> RedirectResponse:
    """Redirect to Monzo OAuth authorization page."""
    settings = Settings()

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    _oauth_states.add(state)

    auth_url = build_authorization_url(state, settings)
    return RedirectResponse(url=auth_url, status_code=307)


@router.get("/callback")
async def callback(
    code: str | None = Query(None),
    state: str | None = Query(None),
    error: str | None = Query(None),
    error_description: str | None = Query(None),
) -> dict[str, Any]:
    """Handle OAuth callback from Monzo."""
    # Check for OAuth errors
    if error:
        raise HTTPException(
            status_code=400,
            detail=f"OAuth error: {error_description or error}",
        )

    # Validate authorization code
    if not code:
        raise HTTPException(
            status_code=400,
            detail="Missing authorization code",
        )

    # Exchange code for tokens
    token_response = await monzo_exchange_code(code)

    # Calculate expiry
    expires_at = calculate_token_expiry(token_response.get("expires_in", 3600))

    # Store tokens
    await store_tokens(
        access_token=token_response["access_token"],
        refresh_token=token_response["refresh_token"],
        expires_at=expires_at,
    )

    return {"message": "Authentication successful", "expires_at": expires_at.isoformat()}


@router.get("/status")
async def status() -> AuthStatus:
    """Check current authentication status."""
    auth = await get_current_auth()

    if auth is None:
        return AuthStatus(authenticated=False)

    now = datetime.now(timezone.utc)
    expired = auth.expires_at < now

    return AuthStatus(
        authenticated=True,
        expired=expired,
        expires_at=auth.expires_at,
    )
