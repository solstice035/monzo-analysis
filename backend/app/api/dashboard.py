"""Dashboard API endpoints."""

from datetime import date, datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import and_, func, select

from app.database import get_session
from app.models import Account, Transaction
from app.services.recurring import detect_recurring_transactions

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


class DailySpend(BaseModel):
    """Daily spending data point."""

    date: str
    amount: int


class TrendData(BaseModel):
    """Spending trend response model."""

    daily_spend: list[DailySpend]
    average_daily: int
    total: int


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary() -> dict[str, Any]:
    """Get dashboard summary data."""
    async with get_session() as session:
        # Get today and start of month
        today = date.today()
        start_of_today = datetime.combine(today, datetime.min.time()).replace(
            tzinfo=timezone.utc
        )
        start_of_month = datetime(today.year, today.month, 1, tzinfo=timezone.utc)

        # Get total transaction count
        count_result = await session.execute(
            select(func.count(Transaction.id))
        )
        transaction_count = count_result.scalar() or 0

        # Get today's spend (negative amounts = spending)
        today_result = await session.execute(
            select(func.sum(Transaction.amount)).where(
                and_(
                    Transaction.created_at >= start_of_today,
                    Transaction.amount < 0,
                )
            )
        )
        spend_today = abs(today_result.scalar() or 0)

        # Get this month's spend
        month_result = await session.execute(
            select(func.sum(Transaction.amount)).where(
                and_(
                    Transaction.created_at >= start_of_month,
                    Transaction.amount < 0,
                )
            )
        )
        spend_this_month = abs(month_result.scalar() or 0)

        # Get top categories
        cat_query = (
            select(
                func.coalesce(
                    Transaction.custom_category, Transaction.monzo_category
                ).label("category"),
                func.sum(Transaction.amount).label("total"),
            )
            .where(Transaction.amount < 0)
            .group_by(
                func.coalesce(
                    Transaction.custom_category, Transaction.monzo_category
                )
            )
            .order_by(func.sum(Transaction.amount))
            .limit(5)
        )
        cat_result = await session.execute(cat_query)
        top_categories = [
            {"category": row.category or "general", "amount": abs(row.total)}
            for row in cat_result.all()
        ]

        # Balance is sum of all transactions (could also fetch from Monzo API)
        balance_result = await session.execute(
            select(func.sum(Transaction.amount))
        )
        balance = balance_result.scalar() or 0

        return {
            "balance": balance,
            "spend_today": spend_today,
            "spend_this_month": spend_this_month,
            "transaction_count": transaction_count,
            "top_categories": top_categories,
        }


@router.get("/trends", response_model=TrendData)
async def get_spending_trends(
    days: int = Query(30, ge=7, le=90),
) -> dict[str, Any]:
    """Get daily spending trend data."""
    async with get_session() as session:
        today = date.today()
        start_date = today - timedelta(days=days - 1)
        start_datetime = datetime.combine(start_date, datetime.min.time()).replace(
            tzinfo=timezone.utc
        )

        # Get daily spend aggregation
        daily_query = (
            select(
                func.date(Transaction.created_at).label("day"),
                func.sum(Transaction.amount).label("total"),
            )
            .where(
                and_(
                    Transaction.created_at >= start_datetime,
                    Transaction.amount < 0,
                )
            )
            .group_by(func.date(Transaction.created_at))
            .order_by(func.date(Transaction.created_at))
        )
        result = await session.execute(daily_query)

        # Build a dict of existing data
        spend_by_date = {str(row.day): abs(row.total) for row in result.all()}

        # Fill in all dates
        daily_spend = []
        total = 0
        for i in range(days):
            d = start_date + timedelta(days=i)
            d_str = d.isoformat()
            amount = spend_by_date.get(d_str, 0)
            daily_spend.append({"date": d_str, "amount": amount})
            total += amount

        average_daily = total // days if days > 0 else 0

        return {
            "daily_spend": daily_spend,
            "average_daily": average_daily,
            "total": total,
        }


class RecurringItem(BaseModel):
    """Recurring transaction response model."""

    merchant_name: str
    category: str
    average_amount: int
    frequency_days: int
    frequency_label: str
    transaction_count: int
    monthly_cost: int
    last_transaction: str
    next_expected: str | None
    confidence: float


class RecurringResponse(BaseModel):
    """Recurring transactions response model."""

    items: list[RecurringItem]
    total_monthly_cost: int


@router.get("/recurring", response_model=RecurringResponse)
async def get_recurring_transactions(
    min_occurrences: int = Query(3, ge=2, le=10),
) -> dict[str, Any]:
    """Get detected recurring/subscription transactions."""
    async with get_session() as session:
        recurring = await detect_recurring_transactions(
            session, min_occurrences=min_occurrences
        )

        items = []
        total_monthly = 0

        for r in recurring:
            items.append({
                "merchant_name": r.merchant_name,
                "category": r.category,
                "average_amount": r.average_amount,
                "frequency_days": r.frequency_days,
                "frequency_label": r.frequency_label,
                "transaction_count": r.transaction_count,
                "monthly_cost": r.monthly_cost,
                "last_transaction": r.last_transaction.isoformat(),
                "next_expected": r.next_expected.isoformat() if r.next_expected else None,
                "confidence": r.confidence,
            })
            total_monthly += r.monthly_cost

        return {
            "items": items,
            "total_monthly_cost": total_monthly,
        }
