"""Budgets API endpoints."""

from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/budgets", tags=["budgets"])


class Budget(BaseModel):
    """Budget response model."""

    id: str
    category: str
    amount: int
    period: Literal["monthly", "weekly"]
    start_day: int


class BudgetCreate(BaseModel):
    """Request model for creating a budget."""

    category: str
    amount: int
    period: Literal["monthly", "weekly"] = "monthly"
    start_day: int = 1


class BudgetUpdate(BaseModel):
    """Request model for updating a budget."""

    category: str | None = None
    amount: int | None = None
    period: Literal["monthly", "weekly"] | None = None
    start_day: int | None = None


class BudgetStatus(BaseModel):
    """Budget status with spending info."""

    budget_id: str
    category: str
    amount: int
    spent: int
    remaining: int
    percentage: float
    status: Literal["under", "warning", "over"]
    period_start: str
    period_end: str


@router.get("", response_model=list[Budget])
async def get_budgets() -> list[dict[str, Any]]:
    """Get all budgets."""
    # TODO: Implement database query
    return []


@router.post("", response_model=Budget, status_code=201)
async def create_budget(data: BudgetCreate) -> dict[str, Any]:
    """Create a new budget."""
    # TODO: Implement database insert
    return {
        "id": "new-budget-id",
        "category": data.category,
        "amount": data.amount,
        "period": data.period,
        "start_day": data.start_day,
    }


@router.patch("/{budget_id}", response_model=Budget)
async def update_budget(budget_id: str, data: BudgetUpdate) -> dict[str, Any]:
    """Update an existing budget."""
    # TODO: Implement database update
    return {
        "id": budget_id,
        "category": data.category or "unknown",
        "amount": data.amount or 0,
        "period": data.period or "monthly",
        "start_day": data.start_day or 1,
    }


@router.delete("/{budget_id}", status_code=204)
async def delete_budget(budget_id: str) -> None:
    """Delete a budget."""
    # TODO: Implement database delete
    pass


@router.get("/status", response_model=list[BudgetStatus])
async def get_budget_statuses() -> list[dict[str, Any]]:
    """Get current status for all budgets."""
    # TODO: Implement budget status calculation
    return []
