"""Tests for scheduler service."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestSchedulerConfiguration:
    """Tests for scheduler configuration."""

    def test_create_scheduler_with_default_interval(self) -> None:
        """Scheduler should use default sync interval from settings."""
        from app.services.scheduler import create_scheduler

        with patch("app.services.scheduler.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(sync_interval_hours=24)

            scheduler = create_scheduler()

            assert scheduler is not None

    def test_scheduler_has_sync_job(self) -> None:
        """Scheduler should have a configured sync job."""
        from app.services.scheduler import create_scheduler, get_sync_job_id

        with patch("app.services.scheduler.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(sync_interval_hours=24)

            scheduler = create_scheduler()
            job_id = get_sync_job_id()

            # Job ID should be consistent
            assert job_id == "monzo_sync"


class TestSyncJobExecution:
    """Tests for sync job execution."""

    @pytest.mark.asyncio
    async def test_sync_job_calls_sync_service(self) -> None:
        """Sync job should invoke the sync service."""
        from app.services.scheduler import run_scheduled_sync

        with patch("app.services.scheduler.SyncService") as MockSyncService:
            mock_service = AsyncMock()
            mock_service.run_sync.return_value = 10
            MockSyncService.return_value = mock_service

            with patch("app.services.scheduler.SlackService") as MockSlackService:
                mock_slack = AsyncMock()
                MockSlackService.return_value = mock_slack

                result = await run_scheduled_sync()

                mock_service.run_sync.assert_called_once()
                assert result == 10

    @pytest.mark.asyncio
    async def test_sync_job_sends_slack_notification(self) -> None:
        """Sync job should notify Slack on completion."""
        from app.services.scheduler import run_scheduled_sync

        with patch("app.services.scheduler.SyncService") as MockSyncService:
            mock_service = AsyncMock()
            mock_service.run_sync.return_value = 15
            MockSyncService.return_value = mock_service

            with patch("app.services.scheduler.SlackService") as MockSlackService:
                mock_slack = AsyncMock()
                MockSlackService.return_value = mock_slack

                with patch("app.services.scheduler.get_settings") as mock_settings:
                    mock_settings.return_value = MagicMock(slack_webhook_url="https://test")

                    await run_scheduled_sync()

                    mock_slack.notify_sync_complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_job_handles_errors(self) -> None:
        """Sync job should handle and log errors gracefully."""
        from app.services.scheduler import run_scheduled_sync

        with patch("app.services.scheduler.SyncService") as MockSyncService:
            mock_service = AsyncMock()
            mock_service.run_sync.side_effect = Exception("Sync failed")
            MockSyncService.return_value = mock_service

            with patch("app.services.scheduler.SlackService"):
                with patch("app.services.scheduler.logger") as mock_logger:
                    result = await run_scheduled_sync()

                    assert result is None
                    mock_logger.error.assert_called()


class TestManualTrigger:
    """Tests for manual sync trigger."""

    @pytest.mark.asyncio
    async def test_trigger_sync_runs_immediately(self) -> None:
        """Manual trigger should run sync immediately."""
        from app.services.scheduler import trigger_sync_now

        with patch("app.services.scheduler.run_scheduled_sync") as mock_run:
            mock_run.return_value = 5

            result = await trigger_sync_now()

            mock_run.assert_called_once()
            assert result == 5


class TestSchedulerLifecycle:
    """Tests for scheduler start/stop lifecycle."""

    def test_start_scheduler(self) -> None:
        """Should start the scheduler."""
        from app.services.scheduler import start_scheduler, create_scheduler

        with patch("app.services.scheduler.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(sync_interval_hours=24)

            scheduler = create_scheduler()

            with patch.object(scheduler, "start") as mock_start:
                start_scheduler(scheduler)
                mock_start.assert_called_once()

    def test_stop_scheduler(self) -> None:
        """Should stop the scheduler gracefully."""
        from app.services.scheduler import stop_scheduler, create_scheduler

        with patch("app.services.scheduler.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(sync_interval_hours=24)

            scheduler = create_scheduler()

            with patch.object(scheduler, "shutdown") as mock_shutdown:
                stop_scheduler(scheduler)
                mock_shutdown.assert_called_once()


class TestNextSyncTime:
    """Tests for next sync time calculation."""

    def test_get_next_sync_time(self) -> None:
        """Should return the next scheduled sync time."""
        from app.services.scheduler import get_next_sync_time, create_scheduler

        with patch("app.services.scheduler.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(sync_interval_hours=24)

            scheduler = create_scheduler()

            # The scheduler should have a next run time
            next_time = get_next_sync_time(scheduler)

            # Could be None if scheduler not started, otherwise datetime
            assert next_time is None or isinstance(next_time, datetime)


class TestBudgetCheckIntegration:
    """Tests for budget check integration with sync."""

    @pytest.mark.asyncio
    async def test_sync_checks_budget_thresholds(self) -> None:
        """Sync should check budget thresholds after completion."""
        from app.services.scheduler import run_scheduled_sync

        with patch("app.services.scheduler.SyncService") as MockSyncService:
            mock_service = AsyncMock()
            mock_service.run_sync.return_value = 10
            MockSyncService.return_value = mock_service

            with patch("app.services.scheduler.SlackService") as MockSlackService:
                mock_slack = AsyncMock()
                MockSlackService.return_value = mock_slack

                with patch("app.services.scheduler.check_budget_alerts") as mock_check:
                    mock_check.return_value = None

                    await run_scheduled_sync()

                    mock_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_budget_alert_sends_slack_warning(self) -> None:
        """Budget check should send Slack warning for 80%+ usage."""
        from app.services.scheduler import check_budget_alerts
        from app.services.budget import BudgetStatus
        from datetime import date

        mock_status = MagicMock(spec=BudgetStatus)
        mock_status.category = "Eating Out"
        mock_status.amount = 20000
        mock_status.spent = 18000
        mock_status.percentage = 90.0
        mock_status.status = "warning"

        with patch("app.services.scheduler.BudgetService") as MockBudgetService:
            mock_service = AsyncMock()
            mock_service.get_all_budget_statuses.return_value = [mock_status]
            MockBudgetService.return_value = mock_service

            with patch("app.services.scheduler.SlackService") as MockSlackService:
                mock_slack = AsyncMock()
                MockSlackService.return_value = mock_slack

                with patch("app.services.scheduler.get_settings") as mock_settings:
                    mock_settings.return_value = MagicMock(slack_webhook_url="https://test")

                    await check_budget_alerts()

                    mock_slack.notify_budget_warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_budget_alert_sends_slack_exceeded(self) -> None:
        """Budget check should send Slack alert for 100%+ usage."""
        from app.services.scheduler import check_budget_alerts
        from app.services.budget import BudgetStatus
        from datetime import date

        mock_status = MagicMock(spec=BudgetStatus)
        mock_status.category = "Entertainment"
        mock_status.amount = 10000
        mock_status.spent = 12500
        mock_status.percentage = 125.0
        mock_status.status = "over"

        with patch("app.services.scheduler.BudgetService") as MockBudgetService:
            mock_service = AsyncMock()
            mock_service.get_all_budget_statuses.return_value = [mock_status]
            MockBudgetService.return_value = mock_service

            with patch("app.services.scheduler.SlackService") as MockSlackService:
                mock_slack = AsyncMock()
                MockSlackService.return_value = mock_slack

                with patch("app.services.scheduler.get_settings") as mock_settings:
                    mock_settings.return_value = MagicMock(slack_webhook_url="https://test")

                    await check_budget_alerts()

                    mock_slack.notify_budget_exceeded.assert_called_once()
