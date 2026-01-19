"""Recurring transaction detection service."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from statistics import mean, stdev

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Transaction


@dataclass
class RecurringTransaction:
    """Represents a detected recurring transaction pattern."""

    merchant_name: str
    category: str
    average_amount: int
    frequency_days: int
    frequency_label: str
    transaction_count: int
    monthly_cost: int
    last_transaction: date
    next_expected: date | None
    confidence: float


async def detect_recurring_transactions(
    session: AsyncSession,
    min_occurrences: int = 3,
    max_interval_variance: float = 0.3,
) -> list[RecurringTransaction]:
    """Detect recurring transactions based on merchant and timing patterns.

    Args:
        session: Database session
        min_occurrences: Minimum number of transactions to consider as recurring
        max_interval_variance: Maximum allowed coefficient of variation for intervals

    Returns:
        List of detected recurring transaction patterns
    """
    # Get transactions grouped by merchant with amounts and dates
    result = await session.execute(
        select(
            Transaction.merchant_name,
            func.coalesce(
                Transaction.custom_category, Transaction.monzo_category
            ).label("category"),
            Transaction.amount,
            Transaction.created_at,
        )
        .where(Transaction.merchant_name.isnot(None))
        .where(Transaction.amount < 0)  # Only spending
        .order_by(Transaction.merchant_name, Transaction.created_at)
    )

    # Group by merchant
    merchant_transactions: dict[str, list[tuple[int, date, str]]] = defaultdict(list)
    for row in result.all():
        if row.merchant_name:
            tx_date = row.created_at.date() if hasattr(row.created_at, "date") else row.created_at
            merchant_transactions[row.merchant_name].append(
                (abs(row.amount), tx_date, row.category or "general")
            )

    recurring = []

    for merchant, transactions in merchant_transactions.items():
        if len(transactions) < min_occurrences:
            continue

        # Analyze timing patterns
        pattern = _analyze_timing_pattern(
            merchant, transactions, min_occurrences, max_interval_variance
        )
        if pattern:
            recurring.append(pattern)

    # Sort by monthly cost (highest first)
    recurring.sort(key=lambda r: r.monthly_cost, reverse=True)
    return recurring


def _analyze_timing_pattern(
    merchant_name: str,
    transactions: list[tuple[int, date, str]],
    min_occurrences: int,
    max_variance: float,
) -> RecurringTransaction | None:
    """Analyze a list of transactions for recurring patterns.

    Args:
        merchant_name: Name of the merchant
        transactions: List of (amount, date, category) tuples
        min_occurrences: Minimum occurrences required
        max_variance: Maximum coefficient of variation for intervals

    Returns:
        RecurringTransaction if pattern detected, None otherwise
    """
    if len(transactions) < min_occurrences:
        return None

    # Sort by date
    sorted_txs = sorted(transactions, key=lambda x: x[1])

    # Calculate intervals between transactions
    intervals = []
    for i in range(1, len(sorted_txs)):
        days = (sorted_txs[i][1] - sorted_txs[i - 1][1]).days
        if days > 0:
            intervals.append(days)

    if len(intervals) < min_occurrences - 1:
        return None

    # Calculate mean and variance of intervals
    avg_interval = mean(intervals)
    if avg_interval < 5:  # Too frequent, likely not subscription
        return None

    # Calculate coefficient of variation
    if len(intervals) > 1:
        std_interval = stdev(intervals)
        cv = std_interval / avg_interval if avg_interval > 0 else float("inf")
    else:
        cv = 0

    if cv > max_variance:
        return None  # Too much variance, not recurring

    # Determine frequency label
    frequency_label, frequency_days = _get_frequency_label(avg_interval)

    # Calculate average amount
    amounts = [t[0] for t in sorted_txs]
    avg_amount = int(mean(amounts))

    # Get category (use most common)
    categories = [t[2] for t in sorted_txs]
    category = max(set(categories), key=categories.count)

    # Calculate monthly cost estimate
    if frequency_days > 0:
        monthly_cost = int(avg_amount * (30 / frequency_days))
    else:
        monthly_cost = avg_amount

    # Calculate confidence based on variance and occurrence count
    confidence = min(1.0, (1 - cv) * min(len(transactions) / 6, 1.0))

    # Get last transaction and predict next
    last_tx_date = sorted_txs[-1][1]
    next_expected = last_tx_date + timedelta(days=int(avg_interval))

    return RecurringTransaction(
        merchant_name=merchant_name,
        category=category,
        average_amount=avg_amount,
        frequency_days=int(avg_interval),
        frequency_label=frequency_label,
        transaction_count=len(transactions),
        monthly_cost=monthly_cost,
        last_transaction=last_tx_date,
        next_expected=next_expected if next_expected > date.today() else None,
        confidence=confidence,
    )


def _get_frequency_label(avg_days: float) -> tuple[str, int]:
    """Determine frequency label based on average interval.

    Args:
        avg_days: Average days between transactions

    Returns:
        Tuple of (label, normalized_days)
    """
    if avg_days < 10:
        return ("weekly", 7)
    elif avg_days < 20:
        return ("fortnightly", 14)
    elif avg_days < 45:
        return ("monthly", 30)
    elif avg_days < 100:
        return ("quarterly", 90)
    else:
        return ("yearly", 365)
