"""Scheduler service for automated sync operations."""

import logging
from datetime import datetime, timezone
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.services.budget import BudgetService
from app.services.slack import SlackService
from app.services.sync import SyncService


logger = logging.getLogger(__name__)

SYNC_JOB_ID = "monzo_sync"


def get_sync_job_id() -> str:
    """Get the sync job ID.

    Returns:
        The job ID string
    """
    return SYNC_JOB_ID


def create_scheduler() -> AsyncIOScheduler:
    """Create and configure the async scheduler.

    Returns:
        Configured AsyncIOScheduler instance
    """
    settings = get_settings()
    scheduler = AsyncIOScheduler()

    # Add the sync job with configurable interval
    scheduler.add_job(
        run_scheduled_sync,
        trigger=IntervalTrigger(hours=settings.sync_interval_hours),
        id=SYNC_JOB_ID,
        name="Monzo Transaction Sync",
        replace_existing=True,
    )

    return scheduler


def start_scheduler(scheduler: AsyncIOScheduler) -> None:
    """Start the scheduler.

    Args:
        scheduler: The scheduler instance to start
    """
    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler(scheduler: AsyncIOScheduler) -> None:
    """Stop the scheduler gracefully.

    Args:
        scheduler: The scheduler instance to stop
    """
    scheduler.shutdown()
    logger.info("Scheduler stopped")


def get_next_sync_time(scheduler: AsyncIOScheduler) -> datetime | None:
    """Get the next scheduled sync time.

    Args:
        scheduler: The scheduler instance

    Returns:
        Next run time or None if not scheduled
    """
    job = scheduler.get_job(SYNC_JOB_ID)
    if job:
        # APScheduler 4.x uses next_fire_time, earlier versions use next_run_time
        next_time = getattr(job, "next_fire_time", None) or getattr(
            job, "next_run_time", None
        )
        return next_time
    return None


async def run_scheduled_sync() -> int | None:
    """Execute the scheduled sync operation.

    Returns:
        Number of transactions synced, or None on error
    """
    from app.database import get_session

    logger.info("Starting scheduled sync")
    start_time = datetime.now(timezone.utc)

    try:
        # Run the sync with database session
        async with get_session() as session:
            sync_service = SyncService(session)
            transactions_synced = await sync_service.run_sync()

        # Calculate duration
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()

        # Send Slack notification
        settings = get_settings()
        if settings.slack_webhook_url:
            slack_service = SlackService(webhook_url=settings.slack_webhook_url)
            await slack_service.notify_sync_complete(
                transactions_synced=transactions_synced,
                new_transactions=transactions_synced,
                duration_seconds=duration,
            )

        # Check budget alerts
        await check_budget_alerts()

        logger.info(f"Scheduled sync complete: {transactions_synced} transactions")
        return transactions_synced

    except Exception as e:
        logger.error(f"Scheduled sync failed: {e}")
        return None


async def trigger_sync_now() -> int | None:
    """Manually trigger a sync operation.

    Returns:
        Number of transactions synced, or None on error
    """
    logger.info("Manual sync triggered")
    return await run_scheduled_sync()


async def check_budget_alerts() -> None:
    """Check all budgets and send alerts for warnings/exceeded.

    Sends Slack notifications for:
    - Budgets at 80-99% usage (warning)
    - Budgets at 100%+ usage (exceeded)
    """
    from datetime import date

    from app.database import get_session

    settings = get_settings()
    if not settings.slack_webhook_url:
        logger.debug("Slack webhook not configured, skipping budget alerts")
        return

    slack_service = SlackService(webhook_url=settings.slack_webhook_url)

    try:
        async with get_session() as session:
            budget_service = BudgetService(session=session)
            statuses = await budget_service.get_all_budget_statuses(date.today())

            for status in statuses:
                if status.status == "over":
                    await slack_service.notify_budget_exceeded(
                        category=status.category,
                        amount=status.amount,
                        spent=status.spent,
                        percentage=status.percentage,
                    )
                elif status.status == "warning":
                    await slack_service.notify_budget_warning(
                        category=status.category,
                        amount=status.amount,
                        spent=status.spent,
                        percentage=status.percentage,
                    )

    except Exception as e:
        logger.error(f"Budget alert check failed: {e}")
