"""Surplus API endpoint.

Provides per-period surplus/deficit data with cumulative totals.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database import get_session
from app.services.surplus import SurplusService

router = APIRouter(tags=["surplus"])


class SurplusItem(BaseModel):
    """Per-period surplus data."""

    period_start: str
    period_end: str
    total_allocated: int
    total_spent: int
    surplus_pence: int
    cumulative_surplus_pence: int


@router.get(
    "/accounts/{account_id}/surplus",
    response_model=list[SurplusItem],
)
async def get_surplus(
    account_id: str,
    months: int = Query(default=12, ge=1, le=60),
) -> list[dict[str, Any]]:
    """Get per-period surplus data with cumulative totals."""
    try:
        account_uuid = UUID(account_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid account_id")

    async with get_session() as session:
        service = SurplusService(session)
        return await service.get_surplus(account_uuid, months=months)
