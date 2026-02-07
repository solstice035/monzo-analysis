"""Tests for recurring transaction detection — merchant grouping, interval detection, confidence."""

from datetime import date, timedelta

import pytest

from app.services.recurring import (
    RecurringTransaction,
    _analyze_timing_pattern,
    _get_frequency_label,
)


class TestGetFrequencyLabel:
    """Tests for frequency label classification."""

    def test_weekly(self) -> None:
        label, days = _get_frequency_label(7.0)
        assert label == "weekly"
        assert days == 7

    def test_fortnightly(self) -> None:
        label, days = _get_frequency_label(14.0)
        assert label == "fortnightly"
        assert days == 14

    def test_monthly(self) -> None:
        label, days = _get_frequency_label(30.0)
        assert label == "monthly"
        assert days == 30

    def test_quarterly(self) -> None:
        label, days = _get_frequency_label(90.0)
        assert label == "quarterly"
        assert days == 90

    def test_yearly(self) -> None:
        label, days = _get_frequency_label(365.0)
        assert label == "yearly"
        assert days == 365

    def test_boundary_weekly_to_fortnightly(self) -> None:
        """At exactly 10 days, should switch from weekly to fortnightly."""
        label, _ = _get_frequency_label(9.9)
        assert label == "weekly"
        label, _ = _get_frequency_label(10.0)
        assert label == "fortnightly"


class TestAnalyzeTimingPattern:
    """Tests for timing pattern analysis."""

    def _make_monthly_transactions(
        self,
        merchant: str = "Netflix",
        amount: int = 1599,
        count: int = 6,
        start: date = date(2025, 7, 1),
    ) -> list[tuple[int, date, str]]:
        """Create a set of roughly monthly transactions."""
        return [
            (amount, start + timedelta(days=30 * i), "entertainment")
            for i in range(count)
        ]

    def test_detects_monthly_pattern(self) -> None:
        """Should detect a clear monthly recurring pattern."""
        txs = self._make_monthly_transactions()
        result = _analyze_timing_pattern("Netflix", txs, min_occurrences=3, max_variance=0.3)

        assert result is not None
        assert result.merchant_name == "Netflix"
        assert result.frequency_label == "monthly"
        assert result.transaction_count == 6

    def test_returns_none_for_too_few_transactions(self) -> None:
        """Should return None if fewer than min_occurrences."""
        txs = self._make_monthly_transactions(count=2)
        result = _analyze_timing_pattern("Netflix", txs, min_occurrences=3, max_variance=0.3)

        assert result is None

    def test_returns_none_for_too_frequent(self) -> None:
        """Should return None if average interval < 5 days (not a subscription)."""
        txs = [
            (500, date(2026, 1, 1) + timedelta(days=i * 2), "transport")
            for i in range(5)
        ]
        result = _analyze_timing_pattern("TfL", txs, min_occurrences=3, max_variance=0.3)

        assert result is None

    def test_returns_none_for_high_variance(self) -> None:
        """Should return None if interval variance exceeds threshold."""
        # Irregular intervals: 7, 45, 10, 60 days
        txs = [
            (1000, date(2025, 1, 1), "general"),
            (1000, date(2025, 1, 8), "general"),
            (1000, date(2025, 2, 22), "general"),
            (1000, date(2025, 3, 4), "general"),
            (1000, date(2025, 5, 3), "general"),
        ]
        result = _analyze_timing_pattern("Random Shop", txs, min_occurrences=3, max_variance=0.3)

        assert result is None

    def test_monthly_cost_calculation(self) -> None:
        """Monthly cost should scale amount by 30/frequency_days."""
        txs = self._make_monthly_transactions(amount=1599)
        result = _analyze_timing_pattern("Netflix", txs, min_occurrences=3, max_variance=0.3)

        assert result is not None
        # Monthly subscription: monthly_cost ≈ amount * (30/30) = amount
        assert result.monthly_cost == pytest.approx(1599, abs=100)

    def test_confidence_increases_with_more_transactions(self) -> None:
        """Confidence should be higher with more data points."""
        txs_few = self._make_monthly_transactions(count=3)
        txs_many = self._make_monthly_transactions(count=8)

        result_few = _analyze_timing_pattern("Netflix", txs_few, min_occurrences=3, max_variance=0.3)
        result_many = _analyze_timing_pattern("Netflix", txs_many, min_occurrences=3, max_variance=0.3)

        assert result_few is not None
        assert result_many is not None
        assert result_many.confidence >= result_few.confidence

    def test_next_expected_is_none_if_in_past(self) -> None:
        """next_expected should be None if the predicted date is in the past."""
        old_txs = [
            (1000, date(2020, 1, 1) + timedelta(days=30 * i), "bills")
            for i in range(4)
        ]
        result = _analyze_timing_pattern("Old Sub", old_txs, min_occurrences=3, max_variance=0.3)

        assert result is not None
        assert result.next_expected is None

    def test_uses_most_common_category(self) -> None:
        """Should use the most frequent category across transactions."""
        txs = [
            (1000, date(2025, 1, 1), "bills"),
            (1000, date(2025, 2, 1), "entertainment"),
            (1000, date(2025, 3, 1), "bills"),
            (1000, date(2025, 4, 1), "bills"),
        ]
        result = _analyze_timing_pattern("Spotify", txs, min_occurrences=3, max_variance=0.3)

        assert result is not None
        assert result.category == "bills"


class TestDetectRecurringTransactions:
    """Tests for the main detection function (requires DB mocking)."""

    @pytest.mark.asyncio
    async def test_groups_by_merchant(self) -> None:
        """Should group transactions by merchant name before analysis."""
        from app.services.recurring import detect_recurring_transactions
        from unittest.mock import AsyncMock, MagicMock

        mock_session = AsyncMock()

        # Simulate DB rows: 4 Netflix transactions + 2 random (below threshold)
        rows = []
        for i in range(4):
            row = MagicMock()
            row.merchant_name = "Netflix"
            row.amount = -1599
            row.created_at = date(2025, 7, 1) + timedelta(days=30 * i)
            row.category = "entertainment"
            rows.append(row)

        for i in range(2):
            row = MagicMock()
            row.merchant_name = "Random Shop"
            row.amount = -500
            row.created_at = date(2025, 9, 1) + timedelta(days=15 * i)
            row.category = "shopping"
            rows.append(row)

        mock_result = MagicMock()
        mock_result.all.return_value = rows
        mock_session.execute.return_value = mock_result

        result = await detect_recurring_transactions(
            mock_session, account_id="acc_123", min_occurrences=3
        )

        # Netflix should be detected, Random Shop should not (only 2 txns)
        assert len(result) == 1
        assert result[0].merchant_name == "Netflix"

    @pytest.mark.asyncio
    async def test_sorts_by_monthly_cost_descending(self) -> None:
        """Results should be sorted by monthly cost, highest first."""
        from app.services.recurring import detect_recurring_transactions
        from unittest.mock import AsyncMock, MagicMock

        mock_session = AsyncMock()

        rows = []
        # Cheap sub: £5/month
        for i in range(4):
            row = MagicMock()
            row.merchant_name = "Cheap Sub"
            row.amount = -500
            row.created_at = date(2025, 7, 1) + timedelta(days=30 * i)
            row.category = "bills"
            rows.append(row)

        # Expensive sub: £50/month
        for i in range(4):
            row = MagicMock()
            row.merchant_name = "Expensive Sub"
            row.amount = -5000
            row.created_at = date(2025, 7, 1) + timedelta(days=30 * i)
            row.category = "bills"
            rows.append(row)

        mock_result = MagicMock()
        mock_result.all.return_value = rows
        mock_session.execute.return_value = mock_result

        result = await detect_recurring_transactions(
            mock_session, account_id="acc_123", min_occurrences=3
        )

        assert len(result) == 2
        assert result[0].merchant_name == "Expensive Sub"
        assert result[1].merchant_name == "Cheap Sub"
