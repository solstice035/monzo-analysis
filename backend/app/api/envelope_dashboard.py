"""Envelope dashboard API endpoints.

Returns budget groups with envelope statuses for current or historical periods.
Sinking funds excluded. Soft-deleted budgets excluded.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import get_session
from app.services.envelope_dashboard import EnvelopeDashboardService

router = APIRouter(tags=["envelope-dashboard"])


class EnvelopeItemResponse(BaseModel):
    """Single envelope within a group."""

    budget_id: str
    budget_name: str | None
    category: str
    allocated: int
    original_allocated: int
    rollover: int
    spent: int
    available: int
    pct_used: float


class EnvelopeGroupResponse(BaseModel):
    """Budget group with its envelopes."""

    group_id: str
    group_name: str
    icon: str | None
    display_order: int
    total_allocated: int
    total_spent: int
    total_available: int
    envelopes: list[EnvelopeItemResponse]


class EnvelopeDashboardResponse(BaseModel):
    """Full envelope dashboard response."""

    period_id: str
    period_start: str
    period_end: str
    period_status: str
    groups: list[EnvelopeGroupResponse]
    total_allocated: int
    total_spent: int
    total_available: int


@router.get(
    "/accounts/{account_id}/periods/current/envelopes",
    response_model=EnvelopeDashboardResponse,
)
async def get_current_envelopes(account_id: str) -> dict[str, Any]:
    """Get envelope dashboard for the current active period."""
    try:
        account_uuid = UUID(account_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid account_id")

    async with get_session() as session:
        service = EnvelopeDashboardService(session)
        result = await service.get_envelope_dashboard(account_uuid)

        if not result:
            raise HTTPException(
                status_code=404,
                detail="No active period found for this account",
            )

        return result


@router.get(
    "/accounts/{account_id}/periods/{period_id}/envelopes",
    response_model=EnvelopeDashboardResponse,
)
async def get_period_envelopes(account_id: str, period_id: str) -> dict[str, Any]:
    """Get envelope dashboard for a specific historical period."""
    try:
        account_uuid = UUID(account_id)
        period_uuid = UUID(period_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    async with get_session() as session:
        service = EnvelopeDashboardService(session)
        result = await service.get_envelope_dashboard(
            account_uuid, period_id=period_uuid
        )

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Period not found or doesn't belong to this account",
            )

        return result
