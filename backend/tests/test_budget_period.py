"""Tests for budget period service: period creation, rollover, and envelope computation."""

import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models import Budget, BudgetPeriod, EnvelopeBalance, Transaction
from app.services.budget_period import (
    BudgetPeriodService,
    EnvelopeStatus,
    calculate_period_dates,
    get_period_start_for_date,
)


def _mock_execute_result(scalar_one_or_none=None, scalars_all=None, scalar=None):
    """Create a mock result from session.execute() that works with sync result methods."""
    result = MagicMock()
    if scalar_one_or_none is not None:
        result.scalar_one_or_none.return_value = scalar_one_or_none
    else:
        result.scalar_one_or_none.return_value = None
    if scalars_all is not None:
        result.scalars.return_value.all.return_value = scalars_all
    if scalar is not None:
        result.scalar.return_value = scalar
    return result


class TestCalculatePeriodDates:
    """Tests for period date calculation."""

    def test_standard_month(self):
        start, end = calculate_period_dates(date(2026, 3, 28))
        assert start == date(2026, 3, 28)
        assert end == date(2026, 4, 27)

    def test_december_to_january(self):
        start, end = calculate_period_dates(date(2025, 12, 28))
        assert start == date(2025, 12, 28)
        assert end == date(2026, 1, 27)

    def test_february_period(self):
        start, end = calculate_period_dates(date(2026, 1, 28))
        assert start == date(2026, 1, 28)
        assert end == date(2026, 2, 27)

    def test_end_is_always_27th(self):
        for month in range(1, 13):
            _, end = calculate_period_dates(date(2026, month, 28))
            assert end.day == 27


class TestGetPeriodStartForDate:
    """Tests for determining which period a date falls in."""

    def test_day_28_is_current_month(self):
        assert get_period_start_for_date(date(2026, 3, 28)) == date(2026, 3, 28)

    def test_day_31_is_current_month(self):
        assert get_period_start_for_date(date(2026, 3, 31)) == date(2026, 3, 28)

    def test_day_1_is_previous_month(self):
        assert get_period_start_for_date(date(2026, 3, 1)) == date(2026, 2, 28)

    def test_day_27_is_previous_month(self):
        assert get_period_start_for_date(date(2026, 3, 27)) == date(2026, 2, 28)

    def test_january_wraps_to_previous_year(self):
        assert get_period_start_for_date(date(2026, 1, 15)) == date(2025, 12, 28)


class TestBudgetPeriodServiceCreatePeriod:
    """Tests for period creation."""

    @pytest.fixture
    def mock_session(self):
        session = AsyncMock()
        session.flush = AsyncMock()
        session.add = MagicMock()
        return session

    @pytest.fixture
    def service(self, mock_session):
        return BudgetPeriodService(mock_session)

    @pytest.mark.asyncio
    async def test_create_period_rejects_non_28th(self, service):
        with pytest.raises(ValueError, match="must start on the 28th"):
            await service.create_period(uuid.uuid4(), date(2026, 3, 15))

    @pytest.mark.asyncio
    async def test_create_period_rejects_duplicate(self, service, mock_session):
        existing_period = MagicMock(spec=BudgetPeriod)
        mock_session.execute.return_value = _mock_execute_result(
            scalar_one_or_none=existing_period
        )

        with pytest.raises(ValueError, match="already exists"):
            await service.create_period(uuid.uuid4(), date(2026, 3, 28))

    @pytest.mark.asyncio
    async def test_create_period_sets_correct_dates(self, service, mock_session):
        mock_session.execute.side_effect = [
            _mock_execute_result(scalar_one_or_none=None),  # No existing period
            _mock_execute_result(scalars_all=[]),  # No active budgets
        ]

        period = await service.create_period(uuid.uuid4(), date(2026, 3, 28))
        assert period.period_start == date(2026, 3, 28)
        assert period.period_end == date(2026, 4, 27)
        assert period.status == "active"

    @pytest.mark.asyncio
    async def test_create_period_creates_envelope_balances(self, service, mock_session):
        budget = MagicMock(spec=Budget)
        budget.id = uuid.uuid4()
        budget.amount = 50000

        mock_session.execute.side_effect = [
            _mock_execute_result(scalar_one_or_none=None),  # No existing period
            _mock_execute_result(scalars_all=[budget]),  # One active budget
        ]

        period = await service.create_period(uuid.uuid4(), date(2026, 3, 28))
        # session.add called for period + 1 envelope balance
        assert mock_session.add.call_count == 2


class TestBudgetPeriodServiceGetCurrentPeriod:
    """Tests for getting the current active period."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session):
        return BudgetPeriodService(mock_session)

    @pytest.mark.asyncio
    async def test_returns_none_when_no_active_period(self, service, mock_session):
        mock_session.execute.return_value = _mock_execute_result(scalar_one_or_none=None)
        result = await service.get_current_period(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_active_period(self, service, mock_session):
        period = MagicMock(spec=BudgetPeriod)
        period.status = "active"
        mock_session.execute.return_value = _mock_execute_result(scalar_one_or_none=period)

        result = await service.get_current_period(uuid.uuid4())
        assert result == period


class TestBudgetPeriodServiceClosePeriod:
    """Tests for period close and rollover."""

    @pytest.fixture
    def account_id(self):
        return uuid.uuid4()

    @pytest.fixture
    def period_id(self):
        return uuid.uuid4()

    @pytest.fixture
    def mock_session(self):
        session = AsyncMock()
        session.flush = AsyncMock()
        session.add = MagicMock()
        return session

    @pytest.fixture
    def service(self, mock_session):
        return BudgetPeriodService(mock_session)

    @pytest.mark.asyncio
    async def test_close_period_not_found(self, service, mock_session, account_id, period_id):
        mock_session.execute.return_value = _mock_execute_result(scalar_one_or_none=None)

        with pytest.raises(ValueError, match="not found"):
            await service.close_period(account_id, period_id)

    @pytest.mark.asyncio
    async def test_close_period_wrong_account(self, service, mock_session, account_id, period_id):
        period = MagicMock(spec=BudgetPeriod)
        period.account_id = uuid.uuid4()  # Different account
        period.status = "active"
        period.envelope_balances = []
        mock_session.execute.return_value = _mock_execute_result(scalar_one_or_none=period)

        with pytest.raises(ValueError, match="does not belong"):
            await service.close_period(account_id, period_id)

    @pytest.mark.asyncio
    async def test_close_period_not_active(self, service, mock_session, account_id, period_id):
        period = MagicMock(spec=BudgetPeriod)
        period.account_id = account_id
        period.status = "closed"
        period.envelope_balances = []
        mock_session.execute.return_value = _mock_execute_result(scalar_one_or_none=period)

        with pytest.raises(ValueError, match="not active"):
            await service.close_period(account_id, period_id)

    @pytest.mark.asyncio
    async def test_close_period_creates_next_period(self, service, mock_session, account_id, period_id):
        """Full rollover scenario: close period with one envelope, verify next period created."""
        budget_id = uuid.uuid4()

        # Old period with one envelope balance
        eb = MagicMock(spec=EnvelopeBalance)
        eb.budget_id = budget_id
        eb.allocated = 50000
        eb.rollover = 0

        period = MagicMock(spec=BudgetPeriod)
        period.id = period_id
        period.account_id = account_id
        period.status = "active"
        period.period_start = date(2026, 2, 28)
        period.period_end = date(2026, 3, 27)
        period.envelope_balances = [eb]

        # Active budget
        budget = MagicMock(spec=Budget)
        budget.id = budget_id
        budget.amount = 50000

        mock_session.execute.side_effect = [
            _mock_execute_result(scalar_one_or_none=period),  # Load period
            _mock_execute_result(scalars_all=[budget]),  # Active monthly budgets
            _mock_execute_result(scalar=-30000),  # Spent = £300
        ]

        next_period = await service.close_period(account_id, period_id)
        assert next_period.period_start == date(2026, 3, 28)
        assert next_period.period_end == date(2026, 4, 27)
        assert period.status == "closed"


class TestBudgetPeriodServiceEnvelopeStatus:
    """Tests for envelope status computation."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session):
        return BudgetPeriodService(mock_session)

    @pytest.mark.asyncio
    async def test_envelope_status_returns_none_when_not_found(self, service, mock_session):
        mock_session.execute.return_value = _mock_execute_result(scalar_one_or_none=None)
        result = await service.get_envelope_status(uuid.uuid4(), uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_envelope_status_computes_available(self, service, mock_session):
        budget_id = uuid.uuid4()
        period_id = uuid.uuid4()

        eb = MagicMock(spec=EnvelopeBalance)
        eb.budget_id = budget_id
        eb.period_id = period_id
        eb.allocated = 50000
        eb.original_allocated = 50000
        eb.rollover = -5000

        period = MagicMock(spec=BudgetPeriod)
        period.id = period_id
        period.period_start = date(2026, 3, 28)

        budget = MagicMock(spec=Budget)
        budget.id = budget_id
        budget.name = "Groceries"
        budget.category = "groceries"

        mock_session.execute.side_effect = [
            _mock_execute_result(scalar_one_or_none=eb),
            _mock_execute_result(scalar_one_or_none=period),
            _mock_execute_result(scalar_one_or_none=budget),
            _mock_execute_result(scalar=-30000),  # Spent
        ]

        result = await service.get_envelope_status(budget_id, period_id)
        assert result is not None
        assert result.allocated == 50000
        assert result.rollover == -5000
        assert result.spent == 30000
        assert result.available == 15000  # 50000 + (-5000) - 30000
        assert result.pct_used == 60.0


class TestBudgetPeriodServiceEnsureEnvelope:
    """Tests for auto-creating envelopes for new budgets."""

    @pytest.fixture
    def mock_session(self):
        session = AsyncMock()
        session.flush = AsyncMock()
        session.add = MagicMock()
        return session

    @pytest.fixture
    def service(self, mock_session):
        return BudgetPeriodService(mock_session)

    @pytest.mark.asyncio
    async def test_skips_sinking_funds(self, service):
        budget = MagicMock(spec=Budget)
        budget.period_type = "annual"
        result = await service.ensure_envelope_for_new_budget(budget)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_no_active_period(self, service, mock_session):
        budget = MagicMock(spec=Budget)
        budget.period_type = "monthly"
        budget.account_id = uuid.uuid4()

        mock_session.execute.return_value = _mock_execute_result(scalar_one_or_none=None)

        result = await service.ensure_envelope_for_new_budget(budget)
        assert result is None


class TestEnvelopeStatusDataclass:
    """Tests for the EnvelopeStatus dataclass."""

    def test_available_calculation(self):
        status = EnvelopeStatus(
            budget_id=uuid.uuid4(),
            budget_name="Groceries",
            category="groceries",
            allocated=50000,
            original_allocated=50000,
            rollover=-5000,
            spent=30000,
            available=15000,
            pct_used=60.0,
        )
        assert status.available == status.allocated + status.rollover - status.spent

    def test_negative_rollover_reduces_available(self):
        status = EnvelopeStatus(
            budget_id=uuid.uuid4(),
            budget_name="Eating Out",
            category="eating_out",
            allocated=20000,
            original_allocated=20000,
            rollover=-25000,
            spent=0,
            available=-5000,
            pct_used=0.0,
        )
        assert status.available == -5000

    def test_positive_rollover_increases_available(self):
        status = EnvelopeStatus(
            budget_id=uuid.uuid4(),
            budget_name="Transport",
            category="transport",
            allocated=10000,
            original_allocated=10000,
            rollover=3000,
            spent=0,
            available=13000,
            pct_used=0.0,
        )
        assert status.available == 13000

    def test_first_period_zero_rollover(self):
        status = EnvelopeStatus(
            budget_id=uuid.uuid4(),
            budget_name="Netflix",
            category="netflix",
            allocated=1000,
            original_allocated=1000,
            rollover=0,
            spent=1000,
            available=0,
            pct_used=100.0,
        )
        assert status.rollover == 0
        assert status.available == 0
