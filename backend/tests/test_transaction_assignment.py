"""Tests for transaction assignment service."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models import Budget, CategoryRule, Transaction
from app.services.transaction_assignment import TransactionAssignmentService


def _mock_execute_result(scalar_one_or_none=None, scalars_all=None):
    result = MagicMock()
    result.scalar_one_or_none.return_value = scalar_one_or_none
    if scalars_all is not None:
        result.scalars.return_value.all.return_value = scalars_all
    return result


def _make_rule(
    target_category="groceries",
    priority=50,
    merchant_exact=None,
    merchant_pattern=None,
    is_income=False,
    is_transfer=False,
):
    rule = MagicMock(spec=CategoryRule)
    rule.priority = priority
    rule.enabled = True
    rule.is_income = is_income
    rule.is_transfer = is_transfer
    rule.target_category = target_category
    conditions = {}
    if merchant_exact:
        conditions["merchant_exact"] = merchant_exact
    if merchant_pattern:
        conditions["merchant_pattern"] = merchant_pattern
    rule.conditions = conditions
    return rule


def _make_tx_data(merchant_name="Tesco", amount=-5000):
    return {
        "id": f"tx_{uuid.uuid4().hex[:8]}",
        "amount": amount,
        "merchant": {"name": merchant_name},
        "category": "groceries",
        "created": "2026-03-15T10:30:00Z",
    }


class TestAssignTransaction:
    """Tests for transaction → envelope assignment."""

    @pytest.fixture
    def mock_session(self):
        session = AsyncMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def service(self, mock_session):
        return TransactionAssignmentService(mock_session)

    @pytest.mark.asyncio
    async def test_no_matching_rule_returns_pending(self, service):
        """No matching rule → pending review."""
        tx_data = _make_tx_data(merchant_name="Unknown Shop")
        budget_id, review_status = await service.assign_transaction(
            tx_data, uuid.uuid4(), uuid.uuid4(), rules=[]
        )
        assert budget_id is None
        assert review_status == "pending"

    @pytest.mark.asyncio
    async def test_income_rule_skips_assignment(self, service):
        """Income rules skip envelope assignment entirely."""
        rule = _make_rule(
            target_category="income",
            merchant_pattern="Sophie",
            is_income=True,
        )
        tx_data = _make_tx_data(merchant_name="Sophie Solly")
        budget_id, review_status = await service.assign_transaction(
            tx_data, uuid.uuid4(), uuid.uuid4(), rules=[rule]
        )
        assert budget_id is None
        assert review_status is None

    @pytest.mark.asyncio
    async def test_transfer_rule_skips_assignment(self, service):
        """Transfer rules skip envelope assignment entirely."""
        rule = _make_rule(
            target_category="transfer",
            merchant_pattern="Transfer",
            is_transfer=True,
        )
        tx_data = _make_tx_data(merchant_name="Transfer to Joint")
        budget_id, review_status = await service.assign_transaction(
            tx_data, uuid.uuid4(), uuid.uuid4(), rules=[rule]
        )
        assert budget_id is None
        assert review_status is None

    @pytest.mark.asyncio
    async def test_high_confidence_auto_assigns(self, service, mock_session):
        """Exact merchant match → auto-assign with no review needed."""
        rule = _make_rule(
            target_category="groceries",
            merchant_exact="Tesco",
        )
        budget = MagicMock(spec=Budget)
        budget.id = uuid.uuid4()

        mock_session.execute.return_value = _mock_execute_result(
            scalar_one_or_none=budget
        )

        tx_data = _make_tx_data(merchant_name="Tesco")
        budget_id, review_status = await service.assign_transaction(
            tx_data, uuid.uuid4(), uuid.uuid4(), rules=[rule]
        )
        assert budget_id == budget.id
        assert review_status is None

    @pytest.mark.asyncio
    async def test_low_confidence_marks_pending(self, service, mock_session):
        """Pattern match with non-exact name → pending review."""
        rule = _make_rule(
            target_category="groceries",
            merchant_pattern="Tesco",
        )
        budget = MagicMock(spec=Budget)
        budget.id = uuid.uuid4()

        mock_session.execute.return_value = _mock_execute_result(
            scalar_one_or_none=budget
        )

        # Merchant name contains pattern but isn't exactly "Tesco"
        tx_data = _make_tx_data(merchant_name="Tesco Express")
        budget_id, review_status = await service.assign_transaction(
            tx_data, uuid.uuid4(), uuid.uuid4(), rules=[rule]
        )
        assert budget_id == budget.id
        assert review_status == "pending"

    @pytest.mark.asyncio
    async def test_pattern_exact_match_is_high_confidence(self, service, mock_session):
        """Pattern that exactly matches merchant name → high confidence."""
        rule = _make_rule(
            target_category="groceries",
            merchant_pattern="Tesco",
        )
        budget = MagicMock(spec=Budget)
        budget.id = uuid.uuid4()

        mock_session.execute.return_value = _mock_execute_result(
            scalar_one_or_none=budget
        )

        tx_data = _make_tx_data(merchant_name="Tesco")
        budget_id, review_status = await service.assign_transaction(
            tx_data, uuid.uuid4(), uuid.uuid4(), rules=[rule]
        )
        assert budget_id == budget.id
        assert review_status is None  # High confidence

    @pytest.mark.asyncio
    async def test_no_budget_for_category_marks_pending(self, service, mock_session):
        """Rule matches but no budget exists for that category."""
        rule = _make_rule(target_category="groceries", merchant_exact="Tesco")

        mock_session.execute.return_value = _mock_execute_result(
            scalar_one_or_none=None  # No budget found
        )

        tx_data = _make_tx_data(merchant_name="Tesco")
        budget_id, review_status = await service.assign_transaction(
            tx_data, uuid.uuid4(), uuid.uuid4(), rules=[rule]
        )
        assert budget_id is None
        assert review_status == "pending"

    @pytest.mark.asyncio
    async def test_highest_priority_rule_wins(self, service, mock_session):
        """When multiple rules match, highest priority wins."""
        rule_low = _make_rule(
            target_category="general_shopping",
            merchant_pattern="Tesco",
            priority=10,
        )
        rule_high = _make_rule(
            target_category="groceries",
            merchant_exact="Tesco",
            priority=100,
        )
        budget = MagicMock(spec=Budget)
        budget.id = uuid.uuid4()
        mock_session.execute.return_value = _mock_execute_result(
            scalar_one_or_none=budget
        )

        tx_data = _make_tx_data(merchant_name="Tesco")
        budget_id, review_status = await service.assign_transaction(
            tx_data, uuid.uuid4(), uuid.uuid4(), rules=[rule_low, rule_high]
        )
        assert budget_id == budget.id
        assert review_status is None  # High confidence (merchant_exact)


class TestBackfillExistingTransactions:
    """Tests for historical transaction backfill."""

    @pytest.fixture
    def mock_session(self):
        session = AsyncMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def service(self, mock_session):
        return TransactionAssignmentService(mock_session)

    @pytest.mark.asyncio
    async def test_backfill_no_budgets(self, service, mock_session):
        """No budgets → nothing to assign."""
        mock_session.execute.return_value = _mock_execute_result(scalars_all=[])
        result = await service.backfill_existing_transactions(uuid.uuid4())
        assert result == {"assigned": 0, "unmatched": 0, "skipped": 0}

    @pytest.mark.asyncio
    async def test_backfill_assigns_matching(self, service, mock_session):
        """Transactions with matching custom_category get budget_id assigned."""
        budget = MagicMock(spec=Budget)
        budget.id = uuid.uuid4()
        budget.category = "groceries"

        tx = MagicMock(spec=Transaction)
        tx.custom_category = "groceries"
        tx.budget_id = None

        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[budget]),  # Budgets
            _mock_execute_result(scalars_all=[tx]),  # Transactions
        ]

        result = await service.backfill_existing_transactions(uuid.uuid4())
        assert result["assigned"] == 1
        assert tx.budget_id == budget.id

    @pytest.mark.asyncio
    async def test_backfill_unmatched_set_to_pending(self, service, mock_session):
        """Transactions with unrecognised custom_category get review_status=pending."""
        budget = MagicMock(spec=Budget)
        budget.id = uuid.uuid4()
        budget.category = "groceries"

        tx = MagicMock(spec=Transaction)
        tx.custom_category = "unknown_category"
        tx.budget_id = None

        mock_session.execute.side_effect = [
            _mock_execute_result(scalars_all=[budget]),
            _mock_execute_result(scalars_all=[tx]),
        ]

        result = await service.backfill_existing_transactions(uuid.uuid4())
        assert result["unmatched"] == 1
        assert tx.review_status == "pending"


class TestConfidenceAssessment:
    """Tests for confidence assessment logic."""

    @pytest.fixture
    def service(self):
        return TransactionAssignmentService(AsyncMock())

    def test_merchant_exact_is_high_confidence(self, service):
        rule = _make_rule(merchant_exact="Tesco")
        tx_data = _make_tx_data(merchant_name="Tesco")
        assert service._assess_confidence(tx_data, rule) == "high"

    def test_merchant_pattern_exact_name_is_high(self, service):
        rule = _make_rule(merchant_pattern="Tesco")
        tx_data = _make_tx_data(merchant_name="Tesco")
        assert service._assess_confidence(tx_data, rule) == "high"

    def test_merchant_pattern_partial_is_low(self, service):
        rule = _make_rule(merchant_pattern="Tesco")
        tx_data = _make_tx_data(merchant_name="Tesco Express")
        assert service._assess_confidence(tx_data, rule) == "low"

    def test_no_merchant_conditions_is_low(self, service):
        rule = _make_rule()
        rule.conditions = {"monzo_category": "groceries"}
        tx_data = _make_tx_data()
        assert service._assess_confidence(tx_data, rule) == "low"
