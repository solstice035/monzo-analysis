"""Pots API endpoints for Monzo pot integration."""

from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database import get_session
from app.services.pot import PotService
from app.services.budget import BudgetService

router = APIRouter(prefix="/pots", tags=["pots"])


class PotResponse(BaseModel):
    """Pot response model."""

    id: str
    monzo_id: str
    name: str
    balance: int
    deleted: bool


class PotContributionResponse(BaseModel):
    """Pot contribution response model."""

    transaction_id: str
    amount: int
    date: str
    description: str | None


class PotSummaryResponse(BaseModel):
    """Pot summary response model."""

    total_pots: int
    linked_pots: int
    unlinked_pots: int
    total_balance: int
    linked_balance: int
    unlinked_balance: int
    unlinked_pot_list: list[dict[str, Any]]


class SinkingFundStatusResponse(BaseModel):
    """Sinking fund status with pot integration."""

    budget_id: str
    budget_name: str | None
    category: str
    pot_id: str | None
    pot_name: str | None
    pot_balance: int | None
    target_amount: int
    monthly_contribution: int
    contributions_this_period: int
    expected_contributions: int
    variance: int
    on_track: bool
    target_month: int | None
    months_remaining: int
    projected_balance: int
    contribution_history: list[PotContributionResponse]


@router.get("", response_model=list[PotResponse])
async def get_pots(
    account_id: str = Query(..., description="Account ID to filter pots"),
    include_deleted: bool = Query(False, description="Include deleted pots"),
) -> list[dict[str, Any]]:
    """Get all pots for a specific account."""
    async with get_session() as session:
        service = PotService(session)
        if include_deleted:
            pots = await service.get_all_pots(account_id)
        else:
            pots = await service.get_active_pots(account_id)
        return [
            {
                "id": str(pot.id),
                "monzo_id": pot.monzo_id,
                "name": pot.name,
                "balance": pot.balance,
                "deleted": pot.deleted,
            }
            for pot in pots
        ]


@router.get("/summary", response_model=PotSummaryResponse)
async def get_pot_summary(
    account_id: str = Query(..., description="Account ID to get pot summary for"),
) -> dict[str, Any]:
    """Get pot summary with linked/unlinked statistics."""
    async with get_session() as session:
        service = PotService(session)
        return await service.get_pot_summary(account_id)


@router.get("/{monzo_pot_id}", response_model=PotResponse)
async def get_pot(monzo_pot_id: str) -> dict[str, Any]:
    """Get a specific pot by Monzo ID."""
    async with get_session() as session:
        service = PotService(session)
        pot = await service.get_pot_by_monzo_id(monzo_pot_id)
        if not pot:
            raise HTTPException(status_code=404, detail="Pot not found")
        return {
            "id": str(pot.id),
            "monzo_id": pot.monzo_id,
            "name": pot.name,
            "balance": pot.balance,
            "deleted": pot.deleted,
        }


@router.get("/{monzo_pot_id}/contributions", response_model=list[PotContributionResponse])
async def get_pot_contributions(
    monzo_pot_id: str,
    account_id: str = Query(..., description="Account ID"),
    since: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    until: str | None = Query(None, description="End date (YYYY-MM-DD)"),
) -> list[dict[str, Any]]:
    """Get contributions (transfers) to a pot."""
    async with get_session() as session:
        service = PotService(session)

        # Parse dates
        since_date = date.fromisoformat(since) if since else None
        until_date = date.fromisoformat(until) if until else None

        contributions = await service.get_pot_contributions(
            account_id=account_id,
            pot_monzo_id=monzo_pot_id,
            since=since_date,
            until=until_date,
        )

        return [
            {
                "transaction_id": str(c.transaction_id),
                "amount": c.amount,
                "date": c.date.isoformat(),
                "description": c.description,
            }
            for c in contributions
        ]


@router.get("/sinking-funds/status", response_model=list[SinkingFundStatusResponse])
async def get_sinking_funds_status(
    account_id: str = Query(..., description="Account ID to get sinking fund statuses for"),
) -> list[dict[str, Any]]:
    """Get status for all sinking fund budgets with pot integration."""
    async with get_session() as session:
        budget_service = BudgetService(session)
        pot_service = PotService(session)

        # Get all sinking fund budgets
        sinking_funds = await budget_service.get_all_sinking_funds(account_id)
        today = date.today()

        statuses = []
        for budget in sinking_funds:
            status = await pot_service.get_sinking_fund_pot_status(budget, today)
            if status:
                statuses.append({
                    "budget_id": str(status.budget_id),
                    "budget_name": status.budget_name,
                    "category": status.category,
                    "pot_id": status.pot_id,
                    "pot_name": status.pot_name,
                    "pot_balance": status.pot_balance,
                    "target_amount": status.target_amount,
                    "monthly_contribution": status.monthly_contribution,
                    "contributions_this_period": status.contributions_this_period,
                    "expected_contributions": status.expected_contributions,
                    "variance": status.variance,
                    "on_track": status.on_track,
                    "target_month": status.target_month,
                    "months_remaining": status.months_remaining,
                    "projected_balance": status.projected_balance,
                    "contribution_history": [
                        {
                            "transaction_id": str(c.transaction_id),
                            "amount": c.amount,
                            "date": c.date.isoformat(),
                            "description": c.description,
                        }
                        for c in status.contribution_history
                    ],
                })

        return statuses
