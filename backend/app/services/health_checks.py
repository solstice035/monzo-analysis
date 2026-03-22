"""Operational health checks for budget system monitoring.

Daily checks at 07:00 UTC:
- Did sync run in last 26 hours?
- Any uncaught exceptions in last sync?
- Is there a current active period for each account?

Alerts sent to Slack via webhook.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Account, BudgetPeriod, SyncLog, Transaction

logger = logging.getLogger(__name__)


async def check_sync_health(session: AsyncSession) -> list[str]:
    """Check if sync ran successfully in the last 26 hours.

    Returns list of alert messages (empty if healthy).
    """
    alerts = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=26)

    result = await session.execute(
        select(SyncLog)
        .where(SyncLog.started_at >= cutoff)
        .order_by(SyncLog.started_at.desc())
        .limit(1)
    )
    latest = result.scalar_one_or_none()

    if not latest:
        alerts.append("🚨 No sync has run in the last 26 hours")
    elif latest.status == "failed":
        error_msg = latest.error or "Unknown error"
        alerts.append(f"🚨 Last sync failed: {error_msg}")
    elif latest.status == "running":
        # Check if it's been running too long (stuck?)
        if latest.started_at < cutoff:
            alerts.append("🚨 Sync appears stuck (running for >26h)")

    return alerts


async def check_active_periods(session: AsyncSession) -> list[str]:
    """Check that every account has a current active budget period.

    Returns list of alert messages (empty if healthy).
    """
    alerts = []

    result = await session.execute(select(Account))
    accounts = list(result.scalars().all())

    for account in accounts:
        period_result = await session.execute(
            select(BudgetPeriod)
            .where(
                and_(
                    BudgetPeriod.account_id == account.id,
                    BudgetPeriod.status == "active",
                )
            )
            .limit(1)
        )
        active_period = period_result.scalar_one_or_none()

        if not active_period:
            label = account.name or account.type or str(account.id)
            alerts.append(f"🚨 No active budget period for account: {label}")

    return alerts


async def check_pending_reviews(session: AsyncSession, max_age_hours: int = 48) -> list[str]:
    """Check for pending review transactions older than max_age_hours.

    Returns list of alert messages (empty if healthy).
    """
    alerts = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)

    result = await session.execute(select(Account))
    accounts = list(result.scalars().all())

    for account in accounts:
        tx_result = await session.execute(
            select(Transaction)
            .where(
                and_(
                    Transaction.account_id == account.id,
                    Transaction.review_status == "pending",
                    Transaction.created_at < cutoff,
                )
            )
            .limit(1)
        )
        old_pending = tx_result.scalar_one_or_none()

        if old_pending:
            label = account.name or account.type or str(account.id)
            alerts.append(
                f"⚠️ Account '{label}' has pending review transactions older than {max_age_hours}h"
            )

    return alerts


async def run_health_checks(session: AsyncSession) -> list[str]:
    """Run all health checks and return combined alert messages.

    Returns empty list if everything is healthy.
    """
    all_alerts = []
    all_alerts.extend(await check_sync_health(session))
    all_alerts.extend(await check_active_periods(session))
    all_alerts.extend(await check_pending_reviews(session))
    return all_alerts
