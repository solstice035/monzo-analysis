"""Income tracking API endpoints.

Returns per-period income vs expense summaries.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.database import get_session
from app.services.income import IncomeService

router = APIRouter(tags=["income"])


@router.get("/accounts/{account_id}/income")
async def get_income_summary(
    account_id: str,
    months: int = Query(default=6, ge=1, le=24, description="Number of periods to include"),
) -> list[dict[str, Any]]:
    """Get income vs expense summary for recent periods."""
    try:
        account_uuid = UUID(account_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid account_id")

    async with get_session() as session:
        service = IncomeService(session)
        return await service.get_income_summary(account_uuid, months)
