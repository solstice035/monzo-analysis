"""Monzo API client for authentication and data fetching."""

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.config import Settings

MONZO_AUTH_URL = "https://auth.monzo.com"
MONZO_API_URL = "https://api.monzo.com"


async def exchange_code_for_tokens(code: str, settings: Settings | None = None) -> dict[str, Any]:
    """Exchange authorization code for access and refresh tokens.

    Args:
        code: The authorization code from OAuth callback
        settings: Optional settings (uses default if not provided)

    Returns:
        Token response from Monzo API
    """
    if settings is None:
        settings = Settings()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MONZO_API_URL}/oauth2/token",
            data={
                "grant_type": "authorization_code",
                "client_id": settings.monzo_client_id,
                "client_secret": settings.monzo_client_secret,
                "redirect_uri": settings.monzo_redirect_uri,
                "code": code,
            },
        )
        response.raise_for_status()
        return response.json()


async def refresh_access_token(refresh_token: str, settings: Settings | None = None) -> dict[str, Any]:
    """Refresh the access token using refresh token.

    Args:
        refresh_token: The refresh token
        settings: Optional settings (uses default if not provided)

    Returns:
        New token response from Monzo API
    """
    if settings is None:
        settings = Settings()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MONZO_API_URL}/oauth2/token",
            data={
                "grant_type": "refresh_token",
                "client_id": settings.monzo_client_id,
                "client_secret": settings.monzo_client_secret,
                "refresh_token": refresh_token,
            },
        )
        response.raise_for_status()
        return response.json()


def build_authorization_url(state: str, settings: Settings | None = None) -> str:
    """Build the Monzo OAuth authorization URL.

    Args:
        state: CSRF state parameter
        settings: Optional settings (uses default if not provided)

    Returns:
        Authorization URL for redirect
    """
    if settings is None:
        settings = Settings()

    params = {
        "client_id": settings.monzo_client_id,
        "redirect_uri": settings.monzo_redirect_uri,
        "response_type": "code",
        "state": state,
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{MONZO_AUTH_URL}/?{query}"


def calculate_token_expiry(expires_in: int) -> datetime:
    """Calculate token expiry datetime from expires_in seconds.

    Args:
        expires_in: Seconds until token expires

    Returns:
        Datetime when token expires
    """
    return datetime.now(timezone.utc) + timedelta(seconds=expires_in)


async def fetch_accounts(access_token: str) -> list[dict[str, Any]]:
    """Fetch all accounts for the authenticated user.

    Args:
        access_token: Valid Monzo access token

    Returns:
        List of account objects
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MONZO_API_URL}/accounts",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return response.json()["accounts"]


async def fetch_transactions(
    access_token: str,
    account_id: str,
    since: datetime | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Fetch transactions for an account.

    Args:
        access_token: Valid Monzo access token
        account_id: Monzo account ID
        since: Only fetch transactions after this datetime
        limit: Maximum number of transactions (default 100)

    Returns:
        List of transaction objects
    """
    params: dict[str, Any] = {
        "account_id": account_id,
        "limit": limit,
        "expand[]": "merchant",
    }
    if since:
        params["since"] = since.strftime("%Y-%m-%dT%H:%M:%SZ")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MONZO_API_URL}/transactions",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
        )
        response.raise_for_status()
        return response.json()["transactions"]


async def fetch_pots(access_token: str, account_id: str) -> list[dict[str, Any]]:
    """Fetch all pots for an account.

    Args:
        access_token: Valid Monzo access token
        account_id: Monzo account ID

    Returns:
        List of pot objects
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MONZO_API_URL}/pots",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"current_account_id": account_id},
        )
        response.raise_for_status()
        return response.json()["pots"]


async def fetch_balance(access_token: str, account_id: str) -> dict[str, Any]:
    """Fetch current balance for an account.

    Args:
        access_token: Valid Monzo access token
        account_id: Monzo account ID

    Returns:
        Balance information
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MONZO_API_URL}/balance",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"account_id": account_id},
        )
        response.raise_for_status()
        return response.json()
