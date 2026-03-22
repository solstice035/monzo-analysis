"""Tests for operational health check service."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models import Account, BudgetPeriod, SyncLog, Transaction
from app.services.health_checks import (
    check_active_periods,
    check_pending_reviews,
    check_sync_health,
    run_health_checks,
)


def _mock_execute_result(scalar_one_or_none=None, scalars_all=None):
    result = MagicMock()
    result.scalar_one_or_none.return_value = scalar_one_or_none
    if scalars_all is not None:
        result.scalars.return_value.all.return_value = scalars_all
    return result


class TestCheckSyncHealth:
    """Tests for sync health monitoring."""

    @pytest.mark.asyncio
    async def test_no_recent_sync_alerts(self):
        session = AsyncMock()
        session.execute.return_value = _mock_execute_result(scalar_one_or_none=None)

        alerts = await check_sync_health(session)
        assert len(alerts) == 1
        assert "No sync" in alerts[0]

    @pytest.mark.asyncio
    async def test_failed_sync_alerts(self):
        session = AsyncMock()
        sync_log = MagicMock(spec=SyncLog)
        sync_log.status = "failed"
        sync_log.error = "Token expired"
        sync_log.started_at = datetime.now(timezone.utc) - timedelta(hours=1)
        session.execute.return_value = _mock_execute_result(scalar_one_or_none=sync_log)

        alerts = await check_sync_health(session)
        assert len(alerts) == 1
        assert "failed" in alerts[0]
        assert "Token expired" in alerts[0]

    @pytest.mark.asyncio
    async def test_successful_sync_no_alerts(self):
        session = AsyncMock()
        sync_log = MagicMock(spec=SyncLog)
        sync_log.status = "success"
        sync_log.started_at = datetime.now(timezone.utc) - timedelta(hours=1)
        session.execute.return_value = _mock_execute_result(scalar_one_or_none=sync_log)

        alerts = await check_sync_health(session)
        assert len(alerts) == 0

    @pytest.mark.asyncio
    async def test_stuck_sync_alerts(self):
        session = AsyncMock()
        sync_log = MagicMock(spec=SyncLog)
        sync_log.status = "running"
        sync_log.started_at = datetime.now(timezone.utc) - timedelta(hours=30)
        session.execute.return_value = _mock_execute_result(scalar_one_or_none=sync_log)

        alerts = await check_sync_health(session)
        assert len(alerts) == 1
        assert "stuck" in alerts[0]


class TestCheckActivePeriods:
    """Tests for active period monitoring."""

    @pytest.mark.asyncio
    async def test_no_active_period_alerts(self):
        session = AsyncMock()
        account = MagicMock(spec=Account)
        account.id = uuid.uuid4()
        account.name = "Joint"
        account.type = "uk_retail_joint"

        session.execute.side_effect = [
            _mock_execute_result(scalars_all=[account]),  # Accounts
            _mock_execute_result(scalar_one_or_none=None),  # No active period
        ]

        alerts = await check_active_periods(session)
        assert len(alerts) == 1
        assert "Joint" in alerts[0]

    @pytest.mark.asyncio
    async def test_active_period_no_alerts(self):
        session = AsyncMock()
        account = MagicMock(spec=Account)
        account.id = uuid.uuid4()
        account.name = "Joint"

        period = MagicMock(spec=BudgetPeriod)
        period.status = "active"

        session.execute.side_effect = [
            _mock_execute_result(scalars_all=[account]),
            _mock_execute_result(scalar_one_or_none=period),
        ]

        alerts = await check_active_periods(session)
        assert len(alerts) == 0


class TestCheckPendingReviews:
    """Tests for pending review monitoring."""

    @pytest.mark.asyncio
    async def test_old_pending_reviews_alert(self):
        session = AsyncMock()
        account = MagicMock(spec=Account)
        account.id = uuid.uuid4()
        account.name = "Joint"

        old_tx = MagicMock(spec=Transaction)
        old_tx.review_status = "pending"

        session.execute.side_effect = [
            _mock_execute_result(scalars_all=[account]),
            _mock_execute_result(scalar_one_or_none=old_tx),
        ]

        alerts = await check_pending_reviews(session, max_age_hours=48)
        assert len(alerts) == 1
        assert "pending review" in alerts[0]

    @pytest.mark.asyncio
    async def test_no_old_pending_reviews_no_alert(self):
        session = AsyncMock()
        account = MagicMock(spec=Account)
        account.id = uuid.uuid4()
        account.name = "Joint"

        session.execute.side_effect = [
            _mock_execute_result(scalars_all=[account]),
            _mock_execute_result(scalar_one_or_none=None),
        ]

        alerts = await check_pending_reviews(session, max_age_hours=48)
        assert len(alerts) == 0


class TestRunHealthChecks:
    """Tests for the combined health check runner."""

    @pytest.mark.asyncio
    async def test_all_healthy_returns_empty(self):
        session = AsyncMock()
        # All checks return empty: no recent sync issues, active periods exist, no pending reviews

        # check_sync_health: recent successful sync
        sync_log = MagicMock(spec=SyncLog)
        sync_log.status = "success"
        sync_log.started_at = datetime.now(timezone.utc) - timedelta(hours=1)

        # check_active_periods: no accounts (so no alerts)
        # check_pending_reviews: no accounts (so no alerts)

        session.execute.side_effect = [
            _mock_execute_result(scalar_one_or_none=sync_log),  # sync health
            _mock_execute_result(scalars_all=[]),  # active periods (no accounts)
            _mock_execute_result(scalars_all=[]),  # pending reviews (no accounts)
        ]

        alerts = await run_health_checks(session)
        assert len(alerts) == 0

    @pytest.mark.asyncio
    async def test_multiple_issues_reported(self):
        session = AsyncMock()

        # No recent sync
        account = MagicMock(spec=Account)
        account.id = uuid.uuid4()
        account.name = "Joint"

        session.execute.side_effect = [
            _mock_execute_result(scalar_one_or_none=None),  # No sync
            _mock_execute_result(scalars_all=[account]),  # One account
            _mock_execute_result(scalar_one_or_none=None),  # No active period
            _mock_execute_result(scalars_all=[account]),  # Pending reviews check
            _mock_execute_result(scalar_one_or_none=None),  # No old pending reviews
        ]

        alerts = await run_health_checks(session)
        assert len(alerts) >= 2  # At least sync + period alerts
