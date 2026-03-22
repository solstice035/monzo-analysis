"""Tests for review queue service."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models import Budget, CategoryRule, Transaction
from app.services.review_queue import ReviewQueueService


def _mock_execute_result(scalar_one_or_none=None, scalars_all=None, scalar=None):
    result = MagicMock()
    result.scalar_one_or_none.return_value = scalar_one_or_none
    if scalars_all is not None:
        result.scalars.return_value.all.return_value = scalars_all
    if scalar is not None:
        result.scalar.return_value = scalar
    return result


class TestGetPendingTransactions:
    """Tests for listing pending review transactions."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session):
        return ReviewQueueService(mock_session)

    @pytest.mark.asyncio
    async def test_returns_pending_transactions(self, service, mock_session):
        tx = MagicMock(spec=Transaction)
        tx.review_status = "pending"

        mock_session.execute.side_effect = [
            _mock_execute_result(scalar=5),  # Count
            _mock_execute_result(scalars_all=[tx]),  # Transactions
        ]

        transactions, total = await service.get_pending_transactions(uuid.uuid4())
        assert total == 5
        assert len(transactions) == 1

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_pending(self, service, mock_session):
        mock_session.execute.side_effect = [
            _mock_execute_result(scalar=0),
            _mock_execute_result(scalars_all=[]),
        ]

        transactions, total = await service.get_pending_transactions(uuid.uuid4())
        assert total == 0
        assert len(transactions) == 0


class TestConfirmTransaction:
    """Tests for confirming a pending transaction."""

    @pytest.fixture
    def mock_session(self):
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def service(self, mock_session):
        return ReviewQueueService(mock_session)

    @pytest.mark.asyncio
    async def test_confirm_sets_status(self, service, mock_session):
        tx = MagicMock(spec=Transaction)
        tx.id = uuid.uuid4()
        tx.review_status = "pending"
        tx.merchant_name = "Tesco"
        tx.budget_id = uuid.uuid4()

        budget = MagicMock(spec=Budget)
        budget.id = tx.budget_id
        budget.category = "groceries"

        mock_session.execute.side_effect = [
            _mock_execute_result(scalar_one_or_none=tx),  # Get pending tx
            _mock_execute_result(scalar_one_or_none=budget),  # Get budget for rule
            _mock_execute_result(scalar_one_or_none=None),  # No existing rule
        ]

        result = await service.confirm_transaction(tx.id, uuid.uuid4())
        assert result is not None
        assert result.review_status == "confirmed"

    @pytest.mark.asyncio
    async def test_confirm_not_found_returns_none(self, service, mock_session):
        mock_session.execute.return_value = _mock_execute_result(scalar_one_or_none=None)
        result = await service.confirm_transaction(uuid.uuid4(), uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_confirm_creates_auto_rule(self, service, mock_session):
        """Confirming a transaction creates a CategoryRule for the merchant."""
        tx = MagicMock(spec=Transaction)
        tx.id = uuid.uuid4()
        tx.review_status = "pending"
        tx.merchant_name = "Wagamama"
        tx.budget_id = uuid.uuid4()

        budget = MagicMock(spec=Budget)
        budget.id = tx.budget_id
        budget.category = "eating_out"

        mock_session.execute.side_effect = [
            _mock_execute_result(scalar_one_or_none=tx),
            _mock_execute_result(scalar_one_or_none=budget),
            _mock_execute_result(scalar_one_or_none=None),  # No existing rule
        ]

        await service.confirm_transaction(tx.id, uuid.uuid4())
        # Verify add was called (for the new rule)
        assert mock_session.add.called


class TestReassignTransaction:
    """Tests for reassigning a transaction to a different budget."""

    @pytest.fixture
    def mock_session(self):
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def service(self, mock_session):
        return ReviewQueueService(mock_session)

    @pytest.mark.asyncio
    async def test_reassign_updates_budget(self, service, mock_session):
        account_id = uuid.uuid4()
        new_budget_id = uuid.uuid4()

        tx = MagicMock(spec=Transaction)
        tx.id = uuid.uuid4()
        tx.review_status = "pending"
        tx.merchant_name = "Costa"
        tx.budget_id = uuid.uuid4()

        target_budget = MagicMock(spec=Budget)
        target_budget.id = new_budget_id
        target_budget.category = "eating_out"

        mock_session.execute.side_effect = [
            _mock_execute_result(scalar_one_or_none=tx),  # Get pending tx
            _mock_execute_result(scalar_one_or_none=target_budget),  # Verify target budget
            _mock_execute_result(scalar_one_or_none=target_budget),  # Get budget for rule
            _mock_execute_result(scalar_one_or_none=None),  # No existing rule
        ]

        result = await service.reassign_transaction(tx.id, account_id, new_budget_id)
        assert result is not None
        assert result.budget_id == new_budget_id
        assert result.review_status == "confirmed"

    @pytest.mark.asyncio
    async def test_reassign_to_nonexistent_budget_returns_none(self, service, mock_session):
        tx = MagicMock(spec=Transaction)
        tx.id = uuid.uuid4()
        tx.review_status = "pending"

        mock_session.execute.side_effect = [
            _mock_execute_result(scalar_one_or_none=tx),
            _mock_execute_result(scalar_one_or_none=None),  # Budget not found
        ]

        result = await service.reassign_transaction(tx.id, uuid.uuid4(), uuid.uuid4())
        assert result is None


class TestExcludeTransaction:
    """Tests for excluding a transaction from envelopes."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session):
        return ReviewQueueService(mock_session)

    @pytest.mark.asyncio
    async def test_exclude_clears_budget(self, service, mock_session):
        tx = MagicMock(spec=Transaction)
        tx.id = uuid.uuid4()
        tx.review_status = "pending"
        tx.budget_id = uuid.uuid4()

        mock_session.execute.return_value = _mock_execute_result(scalar_one_or_none=tx)

        result = await service.exclude_transaction(tx.id, uuid.uuid4())
        assert result is not None
        assert result.budget_id is None
        assert result.review_status == "confirmed"

    @pytest.mark.asyncio
    async def test_exclude_not_found_returns_none(self, service, mock_session):
        mock_session.execute.return_value = _mock_execute_result(scalar_one_or_none=None)
        result = await service.exclude_transaction(uuid.uuid4(), uuid.uuid4())
        assert result is None


class TestAutoRuleCreation:
    """Tests for automatic CategoryRule creation after review."""

    @pytest.fixture
    def mock_session(self):
        session = AsyncMock()
        session.add = MagicMock()
        return session

    @pytest.fixture
    def service(self, mock_session):
        return ReviewQueueService(mock_session)

    @pytest.mark.asyncio
    async def test_updates_existing_rule(self, service, mock_session):
        """If a rule already exists for this merchant, update it."""
        tx = MagicMock(spec=Transaction)
        tx.id = uuid.uuid4()
        tx.review_status = "pending"
        tx.merchant_name = "Tesco"
        tx.budget_id = uuid.uuid4()

        budget = MagicMock(spec=Budget)
        budget.id = tx.budget_id
        budget.category = "groceries"

        existing_rule = MagicMock(spec=CategoryRule)
        existing_rule.priority = 50
        existing_rule.target_category = "general"

        mock_session.execute.side_effect = [
            _mock_execute_result(scalar_one_or_none=tx),
            _mock_execute_result(scalar_one_or_none=budget),
            _mock_execute_result(scalar_one_or_none=existing_rule),
        ]

        await service.confirm_transaction(tx.id, uuid.uuid4())
        assert existing_rule.target_category == "groceries"
        assert existing_rule.priority == 100
