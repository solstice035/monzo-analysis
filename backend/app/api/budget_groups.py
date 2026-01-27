"""Budget Groups API endpoints."""

from datetime import date
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database import get_session
from app.services.budget_group import BudgetGroupService

router = APIRouter(prefix="/budget-groups", tags=["budget-groups"])


class BudgetGroupResponse(BaseModel):
    """Budget group response model."""

    id: str
    account_id: str
    name: str
    icon: str | None
    display_order: int


class BudgetGroupCreate(BaseModel):
    """Request model for creating a budget group."""

    account_id: str
    name: str
    icon: str | None = None
    display_order: int = 0


class BudgetGroupUpdate(BaseModel):
    """Request model for updating a budget group."""

    name: str | None = None
    icon: str | None = None
    display_order: int | None = None


class BudgetStatusInGroup(BaseModel):
    """Budget status within a group."""

    budget_id: str
    name: str | None
    category: str
    amount: int
    spent: int
    remaining: int
    percentage: float
    status: Literal["under", "warning", "over"]
    period_start: str
    period_end: str


class BudgetGroupStatusResponse(BaseModel):
    """Budget group status with roll-up totals."""

    group_id: str
    name: str
    icon: str | None
    display_order: int
    total_amount: int
    total_spent: int
    total_remaining: int
    percentage: float
    status: Literal["under", "warning", "over"]
    budget_count: int
    budgets: list[BudgetStatusInGroup]
    period_start: str
    period_end: str


class DashboardSummaryResponse(BaseModel):
    """Dashboard summary with all group statuses."""

    groups: list[BudgetGroupStatusResponse]
    total_budget: int
    total_spent: int
    total_remaining: int
    overall_percentage: float
    overall_status: Literal["under", "warning", "over"]
    period_start: str
    period_end: str
    days_in_period: int
    days_elapsed: int


@router.get("", response_model=list[BudgetGroupResponse])
async def get_budget_groups(
    account_id: str = Query(..., description="Account ID to filter groups"),
) -> list[dict[str, Any]]:
    """Get all budget groups for a specific account."""
    async with get_session() as session:
        service = BudgetGroupService(session)
        groups = await service.get_all_groups(account_id)
        return [
            {
                "id": str(g.id),
                "account_id": str(g.account_id),
                "name": g.name,
                "icon": g.icon,
                "display_order": g.display_order,
            }
            for g in groups
        ]


@router.get("/status", response_model=list[BudgetGroupStatusResponse])
async def get_budget_group_statuses(
    account_id: str = Query(..., description="Account ID to filter group statuses"),
) -> list[dict[str, Any]]:
    """Get current status for all budget groups for a specific account."""
    async with get_session() as session:
        service = BudgetGroupService(session)
        statuses = await service.get_all_group_statuses(account_id, date.today())
        return [
            {
                "group_id": str(s.group_id),
                "name": s.name,
                "icon": s.icon,
                "display_order": s.display_order,
                "total_amount": s.total_amount,
                "total_spent": s.total_spent,
                "total_remaining": s.total_remaining,
                "percentage": s.percentage,
                "status": s.status,
                "budget_count": s.budget_count,
                "budgets": [
                    {
                        "budget_id": str(b.budget_id),
                        "name": getattr(b, "name", None),
                        "category": b.category,
                        "amount": b.amount,
                        "spent": b.spent,
                        "remaining": b.remaining,
                        "percentage": b.percentage,
                        "status": b.status,
                        "period_start": b.period_start.isoformat(),
                        "period_end": b.period_end.isoformat(),
                    }
                    for b in s.budgets
                ],
                "period_start": s.period_start.isoformat(),
                "period_end": s.period_end.isoformat(),
            }
            for s in statuses
        ]


@router.get("/dashboard", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    account_id: str = Query(..., description="Account ID for dashboard"),
) -> dict[str, Any]:
    """Get dashboard summary with all budget group statuses and totals."""
    async with get_session() as session:
        service = BudgetGroupService(session)
        summary = await service.get_dashboard_summary(account_id, date.today())

        return {
            "groups": [
                {
                    "group_id": str(s.group_id),
                    "name": s.name,
                    "icon": s.icon,
                    "display_order": s.display_order,
                    "total_amount": s.total_amount,
                    "total_spent": s.total_spent,
                    "total_remaining": s.total_remaining,
                    "percentage": s.percentage,
                    "status": s.status,
                    "budget_count": s.budget_count,
                    "budgets": [
                        {
                            "budget_id": str(b.budget_id),
                            "name": getattr(b, "name", None),
                            "category": b.category,
                            "amount": b.amount,
                            "spent": b.spent,
                            "remaining": b.remaining,
                            "percentage": b.percentage,
                            "status": b.status,
                            "period_start": b.period_start.isoformat(),
                            "period_end": b.period_end.isoformat(),
                        }
                        for b in s.budgets
                    ],
                    "period_start": s.period_start.isoformat(),
                    "period_end": s.period_end.isoformat(),
                }
                for s in summary["groups"]
            ],
            "total_budget": summary["total_budget"],
            "total_spent": summary["total_spent"],
            "total_remaining": summary["total_remaining"],
            "overall_percentage": summary["overall_percentage"],
            "overall_status": summary["overall_status"],
            "period_start": summary["period_start"].isoformat(),
            "period_end": summary["period_end"].isoformat(),
            "days_in_period": summary["days_in_period"],
            "days_elapsed": summary["days_elapsed"],
        }


@router.get("/{group_id}", response_model=BudgetGroupResponse)
async def get_budget_group(group_id: str) -> dict[str, Any]:
    """Get a single budget group by ID."""
    async with get_session() as session:
        service = BudgetGroupService(session)
        group = await service.get_group(group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Budget group not found")
        return {
            "id": str(group.id),
            "account_id": str(group.account_id),
            "name": group.name,
            "icon": group.icon,
            "display_order": group.display_order,
        }


@router.get("/{group_id}/status", response_model=BudgetGroupStatusResponse)
async def get_budget_group_status(group_id: str) -> dict[str, Any]:
    """Get status for a single budget group with all child budgets."""
    async with get_session() as session:
        service = BudgetGroupService(session)
        group = await service.get_group(group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Budget group not found")

        status = await service.get_group_status(group, date.today())
        return {
            "group_id": str(status.group_id),
            "name": status.name,
            "icon": status.icon,
            "display_order": status.display_order,
            "total_amount": status.total_amount,
            "total_spent": status.total_spent,
            "total_remaining": status.total_remaining,
            "percentage": status.percentage,
            "status": status.status,
            "budget_count": status.budget_count,
            "budgets": [
                {
                    "budget_id": str(b.budget_id),
                    "name": getattr(b, "name", None),
                    "category": b.category,
                    "amount": b.amount,
                    "spent": b.spent,
                    "remaining": b.remaining,
                    "percentage": b.percentage,
                    "status": b.status,
                    "period_start": b.period_start.isoformat(),
                    "period_end": b.period_end.isoformat(),
                }
                for b in status.budgets
            ],
            "period_start": status.period_start.isoformat(),
            "period_end": status.period_end.isoformat(),
        }


@router.post("", response_model=BudgetGroupResponse, status_code=201)
async def create_budget_group(data: BudgetGroupCreate) -> dict[str, Any]:
    """Create a new budget group."""
    async with get_session() as session:
        service = BudgetGroupService(session)
        group = await service.create_group(
            account_id=data.account_id,
            name=data.name,
            icon=data.icon,
            display_order=data.display_order,
        )
        return {
            "id": str(group.id),
            "account_id": str(group.account_id),
            "name": group.name,
            "icon": group.icon,
            "display_order": group.display_order,
        }


@router.patch("/{group_id}", response_model=BudgetGroupResponse)
async def update_budget_group(
    group_id: str,
    data: BudgetGroupUpdate,
) -> dict[str, Any]:
    """Update an existing budget group."""
    async with get_session() as session:
        service = BudgetGroupService(session)
        group = await service.update_group(
            group_id=group_id,
            name=data.name,
            icon=data.icon,
            display_order=data.display_order,
        )
        if not group:
            raise HTTPException(status_code=404, detail="Budget group not found")
        return {
            "id": str(group.id),
            "account_id": str(group.account_id),
            "name": group.name,
            "icon": group.icon,
            "display_order": group.display_order,
        }


@router.delete("/{group_id}", status_code=204)
async def delete_budget_group(group_id: str) -> None:
    """Delete a budget group and all its budgets."""
    async with get_session() as session:
        service = BudgetGroupService(session)
        deleted = await service.delete_group(group_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Budget group not found")


@router.post("/migrate-orphaned", response_model=dict[str, int])
async def migrate_orphaned_budgets(
    account_id: str = Query(..., description="Account ID to migrate budgets for"),
) -> dict[str, int]:
    """Migrate budgets without groups to a 'Miscellaneous' group.

    This is a utility endpoint for migrating existing budgets after
    the budget groups feature is introduced.
    """
    async with get_session() as session:
        service = BudgetGroupService(session)
        count = await service.migrate_orphaned_budgets(account_id)
        return {"migrated": count}
