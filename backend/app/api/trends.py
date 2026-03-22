"""Trends API endpoints.

Provides envelope spending trends and over-budget analysis.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database import get_session
from app.services.trends import TrendsService

router = APIRouter(tags=["trends"])


class EnvelopeTrendItem(BaseModel):
    """Single envelope trend data point."""

    period_start: str
    budget_name: str | None
    group_name: str
    allocated: int
    spent: int
    pct_used: float
    over_budget: bool


class OverBudgetItem(BaseModel):
    """Chronically over-budget envelope."""

    budget_id: str
    budget_name: str | None
    group_name: str
    over_budget_count: int
    total_periods: int
    pct_over: float
    avg_overspend_pence: int


@router.get(
    "/accounts/{account_id}/trends/envelopes",
    response_model=list[EnvelopeTrendItem],
)
async def get_envelope_trends(
    account_id: str,
    months: int = Query(default=6, ge=1, le=24),
    budget_id: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    """Get envelope spending trends over the last N months."""
    try:
        account_uuid = UUID(account_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid account_id")

    budget_uuid = None
    if budget_id:
        try:
            budget_uuid = UUID(budget_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid budget_id")

    async with get_session() as session:
        service = TrendsService(session)
        return await service.get_envelope_trends(
            account_uuid, months=months, budget_id=budget_uuid,
        )


@router.get(
    "/accounts/{account_id}/trends/over-budget",
    response_model=list[OverBudgetItem],
)
async def get_over_budget_envelopes(
    account_id: str,
    months: int = Query(default=6, ge=1, le=24),
) -> list[dict[str, Any]]:
    """Get envelopes that are chronically over budget."""
    try:
        account_uuid = UUID(account_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid account_id")

    async with get_session() as session:
        service = TrendsService(session)
        return await service.get_over_budget_envelopes(
            account_uuid, months=months,
        )
