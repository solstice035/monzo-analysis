"""Dashboard API endpoints."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class CategorySpend(BaseModel):
    """Category spending info."""

    category: str
    amount: int


class DashboardSummary(BaseModel):
    """Dashboard summary response model."""

    balance: int
    spend_today: int
    spend_this_month: int
    transaction_count: int
    top_categories: list[CategorySpend]


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary() -> dict[str, Any]:
    """Get dashboard summary data."""
    # TODO: Implement database aggregation
    return {
        "balance": 0,
        "spend_today": 0,
        "spend_this_month": 0,
        "transaction_count": 0,
        "top_categories": [],
    }
