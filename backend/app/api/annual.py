"""Annual view API endpoints.

Returns a year-long matrix of budget groups × months with
allocated/spent/available for each cell.
"""

from datetime import date
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.database import get_session
from app.services.annual import AnnualService

router = APIRouter(tags=["annual"])


@router.get("/accounts/{account_id}/annual")
async def get_annual_view(
    account_id: str,
    year: int = Query(default=None, description="Calendar year (default: current year)"),
) -> dict[str, Any]:
    """Get annual budget overview for a given year."""
    try:
        account_uuid = UUID(account_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid account_id")

    if year is None:
        year = date.today().year

    if year < 2000 or year > 2100:
        raise HTTPException(status_code=400, detail="Year must be between 2000 and 2100")

    async with get_session() as session:
        service = AnnualService(session)
        return await service.get_annual_view(account_uuid, year)
