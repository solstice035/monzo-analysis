"""Merchants API endpoint — distinct merchants with rule/budget assignment.

Phase 2.5a: Provides the data layer for the merchant directory UI.
"""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import String, case, cast, func, select, text, type_coerce
from sqlalchemy.dialects.postgresql import JSONB

from app.database import get_session
from app.models import Budget, BudgetGroup, CategoryRule, Transaction

router = APIRouter(tags=["merchants"])


class MerchantResponse(BaseModel):
    """Merchant summary with rule/budget assignment."""

    name: str
    transaction_count: int
    last_seen: str  # ISO date string
    rule_id: str | None
    assigned_budget_id: str | None
    assigned_budget_name: str | None
    assigned_group_name: str | None


@router.get(
    "/accounts/{account_id}/merchants",
    response_model=list[MerchantResponse],
)
async def get_merchants(account_id: str) -> list[dict[str, Any]]:
    """Get all distinct merchants for an account with rule/budget info.

    Returns merchants ordered: uncategorised first (rule_id IS NULL),
    then by transaction_count DESC within each group.
    """
    async with get_session() as session:
        # Subquery: aggregate merchant stats from transactions
        merchant_stats = (
            select(
                Transaction.merchant_name.label("merchant_name"),
                func.count().label("transaction_count"),
                func.max(Transaction.created_at).label("last_seen"),
            )
            .where(
                Transaction.account_id == account_id,
                Transaction.merchant_name.isnot(None),
                Transaction.merchant_name != "",
            )
            .group_by(Transaction.merchant_name)
        ).subquery("merchant_stats")

        # Extract merchant_exact from JSON conditions using PostgreSQL ->> operator
        merchant_exact_expr = CategoryRule.conditions.op("->>")("merchant_exact")

        # Main query: join with rules (on merchant_exact condition) and budgets
        query = (
            select(
                merchant_stats.c.merchant_name.label("name"),
                merchant_stats.c.transaction_count,
                merchant_stats.c.last_seen,
                CategoryRule.id.label("rule_id"),
                Budget.id.label("assigned_budget_id"),
                Budget.name.label("assigned_budget_name"),
                BudgetGroup.name.label("assigned_group_name"),
            )
            .outerjoin(
                CategoryRule,
                (
                    func.lower(cast(merchant_exact_expr, String))
                    == func.lower(merchant_stats.c.merchant_name)
                )
                & (CategoryRule.account_id == account_id)
                & (CategoryRule.enabled.is_(True)),
            )
            .outerjoin(
                Budget,
                (Budget.id == CategoryRule.target_budget_id)
                & (Budget.deleted_at.is_(None)),
            )
            .outerjoin(
                BudgetGroup,
                BudgetGroup.id == Budget.group_id,
            )
            .order_by(
                # Uncategorised first (rule_id IS NULL → 0, else 1)
                case((CategoryRule.id.is_(None), 0), else_=1),
                # Then by transaction count descending
                merchant_stats.c.transaction_count.desc(),
            )
        )

        result = await session.execute(query)
        rows = result.all()

        return [
            {
                "name": row.name,
                "transaction_count": row.transaction_count,
                "last_seen": (
                    row.last_seen.strftime("%Y-%m-%d")
                    if isinstance(row.last_seen, (datetime, date))
                    else str(row.last_seen) if row.last_seen else None
                ),
                "rule_id": str(row.rule_id) if row.rule_id else None,
                "assigned_budget_id": (
                    str(row.assigned_budget_id) if row.assigned_budget_id else None
                ),
                "assigned_budget_name": row.assigned_budget_name,
                "assigned_group_name": row.assigned_group_name,
            }
            for row in rows
        ]
