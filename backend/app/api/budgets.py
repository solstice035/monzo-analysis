"""Budgets API endpoints."""

import csv
import io
from datetime import date
from typing import Any, Literal

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from app.database import get_session
from app.services.budget import BudgetService

router = APIRouter(prefix="/budgets", tags=["budgets"])


class BudgetResponse(BaseModel):
    """Budget response model."""

    id: str
    account_id: str
    category: str
    amount: int
    period: Literal["monthly", "weekly"]
    start_day: int
    # Sinking fund fields
    name: str | None = None
    group_id: str | None = None
    period_type: str = "monthly"
    annual_amount: int | None = None
    target_month: int | None = None
    linked_pot_id: str | None = None
    is_sinking_fund: bool = False
    monthly_contribution: int = 0


class BudgetCreate(BaseModel):
    """Request model for creating a budget."""

    account_id: str
    category: str
    amount: int
    period: Literal["monthly", "weekly"] = "monthly"
    start_day: int = Field(default=1, ge=1, le=28)
    # Sinking fund fields
    name: str | None = None
    group_id: str | None = None
    period_type: str = "monthly"
    annual_amount: int | None = None
    target_month: int | None = None
    linked_pot_id: str | None = None


class BudgetUpdate(BaseModel):
    """Request model for updating a budget."""

    category: str | None = None
    amount: int | None = None
    period: Literal["monthly", "weekly"] | None = None
    start_day: int | None = Field(default=None, ge=1, le=28)
    # Sinking fund fields
    name: str | None = None
    group_id: str | None = None
    period_type: str | None = None
    annual_amount: int | None = None
    target_month: int | None = None
    linked_pot_id: str | None = None


class BudgetStatusResponse(BaseModel):
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


@router.get("", response_model=list[BudgetResponse])
async def get_budgets(
    account_id: str = Query(..., description="Account ID to filter budgets"),
) -> list[dict[str, Any]]:
    """Get all budgets for a specific account."""
    async with get_session() as session:
        service = BudgetService(session)
        budgets = await service.get_all_budgets(account_id)
        return [
            {
                "id": str(b.id),
                "account_id": str(b.account_id),
                "category": b.category,
                "amount": b.amount,
                "period": b.period,
                "start_day": b.start_day,
                "name": b.name,
                "group_id": str(b.group_id) if b.group_id else None,
                "period_type": b.period_type or "monthly",
                "annual_amount": b.annual_amount,
                "target_month": b.target_month,
                "linked_pot_id": b.linked_pot_id,
                "is_sinking_fund": b.is_sinking_fund,
                "monthly_contribution": b.monthly_contribution,
            }
            for b in budgets
        ]


@router.post("", response_model=BudgetResponse, status_code=201)
async def create_budget(data: BudgetCreate) -> dict[str, Any]:
    """Create a new budget for a specific account."""
    async with get_session() as session:
        service = BudgetService(session)
        budget = await service.create_budget(
            account_id=data.account_id,
            category=data.category,
            amount=data.amount,
            period=data.period,
            start_day=data.start_day,
            name=data.name,
            group_id=data.group_id,
            period_type=data.period_type,
            annual_amount=data.annual_amount,
            target_month=data.target_month,
            linked_pot_id=data.linked_pot_id,
        )
        return {
            "id": str(budget.id),
            "account_id": str(budget.account_id),
            "category": budget.category,
            "amount": budget.amount,
            "period": budget.period,
            "start_day": budget.start_day,
            "name": budget.name,
            "group_id": str(budget.group_id) if budget.group_id else None,
            "period_type": budget.period_type or "monthly",
            "annual_amount": budget.annual_amount,
            "target_month": budget.target_month,
            "linked_pot_id": budget.linked_pot_id,
            "is_sinking_fund": budget.is_sinking_fund,
            "monthly_contribution": budget.monthly_contribution,
        }


@router.patch("/{budget_id}", response_model=BudgetResponse)
async def update_budget(budget_id: str, data: BudgetUpdate) -> dict[str, Any]:
    """Update an existing budget."""
    async with get_session() as session:
        service = BudgetService(session)
        budget = await service.update_budget(
            budget_id=budget_id,
            category=data.category,
            amount=data.amount,
            period=data.period,
            start_day=data.start_day,
            name=data.name,
            group_id=data.group_id,
            period_type=data.period_type,
            annual_amount=data.annual_amount,
            target_month=data.target_month,
            linked_pot_id=data.linked_pot_id,
        )
        if not budget:
            raise HTTPException(status_code=404, detail="Budget not found")
        return {
            "id": str(budget.id),
            "account_id": str(budget.account_id),
            "category": budget.category,
            "amount": budget.amount,
            "period": budget.period,
            "start_day": budget.start_day,
            "name": budget.name,
            "group_id": str(budget.group_id) if budget.group_id else None,
            "period_type": budget.period_type or "monthly",
            "annual_amount": budget.annual_amount,
            "target_month": budget.target_month,
            "linked_pot_id": budget.linked_pot_id,
            "is_sinking_fund": budget.is_sinking_fund,
            "monthly_contribution": budget.monthly_contribution,
        }


@router.delete("/{budget_id}", status_code=204)
async def delete_budget(budget_id: str) -> None:
    """Delete a budget."""
    async with get_session() as session:
        service = BudgetService(session)
        deleted = await service.delete_budget(budget_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Budget not found")


@router.get("/status", response_model=list[BudgetStatusResponse])
async def get_budget_statuses(
    account_id: str = Query(..., description="Account ID to filter budget statuses"),
) -> list[dict[str, Any]]:
    """Get current status for all budgets for a specific account."""
    async with get_session() as session:
        service = BudgetService(session)
        statuses = await service.get_all_budget_statuses(account_id, date.today())
        return [
            {
                "budget_id": str(s.budget_id),
                "category": s.category,
                "amount": s.amount,
                "spent": s.spent,
                "remaining": s.remaining,
                "percentage": s.percentage,
                "status": s.status,
                "period_start": s.period_start.isoformat(),
                "period_end": s.period_end.isoformat(),
            }
            for s in statuses
        ]


class ImportResult(BaseModel):
    """Result of CSV import operation."""

    imported: int
    skipped: int
    errors: list[str]


@router.post("/import", response_model=ImportResult)
async def import_budgets_csv(
    account_id: str = Query(..., description="Account ID to import budgets into"),
    file: UploadFile = File(...),
) -> dict[str, Any]:
    """Import budgets from CSV file for a specific account.

    Expected CSV format:
    category,amount,period,start_day
    groceries,30000,monthly,1
    transport,15000,monthly,1

    Amount should be in pence (e.g., 30000 = £300.00).
    Period should be 'monthly' or 'weekly'.
    Start_day is optional (defaults to 1).
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded")

    reader = csv.DictReader(io.StringIO(text))

    imported = 0
    skipped = 0
    errors: list[str] = []

    async with get_session() as session:
        service = BudgetService(session)
        existing_budgets = await service.get_all_budgets(account_id)
        existing_categories = {b.category.lower() for b in existing_budgets}

        try:
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is 1)
                category = row.get("category", "").strip()
                if not category:
                    errors.append(f"Row {row_num}: Missing category")
                    continue

                # Skip if category already exists for this account
                if category.lower() in existing_categories:
                    skipped += 1
                    continue

                amount_str = row.get("amount", "").strip()
                if not amount_str:
                    errors.append(f"Row {row_num}: Missing amount")
                    continue

                try:
                    amount = int(amount_str)
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid amount '{amount_str}'")
                    continue

                period = row.get("period", "monthly").strip().lower()
                if period not in ("monthly", "weekly"):
                    period = "monthly"

                start_day_str = row.get("start_day", "1").strip()
                try:
                    start_day = int(start_day_str)
                    start_day = max(1, min(28, start_day))  # Clamp to 1-28
                except ValueError:
                    start_day = 1

                await service.create_budget(
                    account_id=account_id,
                    category=category,
                    amount=amount,
                    period=period,
                    start_day=start_day,
                )
                existing_categories.add(category.lower())
                imported += 1

            # Commit all at once — atomic import
            await session.commit()

        except Exception as e:
            await session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Import failed, all changes rolled back: {str(e)}",
            )

    return {"imported": imported, "skipped": skipped, "errors": errors}
