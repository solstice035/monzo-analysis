"""Tests for new envelope budgeting models: BudgetPeriod, EnvelopeBalance,
and extensions to Budget, Transaction, and CategoryRule."""

import uuid
from datetime import date, datetime, timezone

import pytest

from app.models.budget import Budget
from app.models.budget_period import BudgetPeriod
from app.models.envelope_balance import EnvelopeBalance
from app.models.category_rule import CategoryRule
from app.models.transaction import Transaction


class TestBudgetPeriodModel:
    """Tests for the BudgetPeriod model."""

    def test_budget_period_creation(self):
        """BudgetPeriod can be created with required fields."""
        account_id = uuid.uuid4()
        period = BudgetPeriod(
            id=uuid.uuid4(),
            account_id=account_id,
            period_start=date(2026, 2, 28),
            period_end=date(2026, 3, 27),
            status="active",
        )
        assert period.account_id == account_id
        assert period.period_start == date(2026, 2, 28)
        assert period.period_end == date(2026, 3, 27)
        assert period.status == "active"

    def test_budget_period_default_status(self):
        """BudgetPeriod column has 'active' as default."""
        # SQLAlchemy defaults apply on DB flush, not in-memory construction.
        # Verify the column default is configured correctly.
        col = BudgetPeriod.__table__.columns["status"]
        assert col.default.arg == "active"

    def test_budget_period_status_transitions(self):
        """BudgetPeriod status can be set to closing and closed."""
        period = BudgetPeriod(
            id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            period_start=date(2026, 2, 28),
            period_end=date(2026, 3, 27),
            status="active",
        )
        assert period.status == "active"

        period.status = "closing"
        assert period.status == "closing"

        period.status = "closed"
        assert period.status == "closed"

    def test_budget_period_tablename(self):
        """BudgetPeriod uses correct table name."""
        assert BudgetPeriod.__tablename__ == "budget_periods"

    def test_budget_period_unique_constraint(self):
        """BudgetPeriod has unique constraint on (account_id, period_start)."""
        constraints = [
            c.name for c in BudgetPeriod.__table__.constraints
            if hasattr(c, "name") and c.name
        ]
        assert "uq_budget_periods_account_start" in constraints


class TestEnvelopeBalanceModel:
    """Tests for the EnvelopeBalance model."""

    def test_envelope_balance_creation(self):
        """EnvelopeBalance can be created with required fields."""
        budget_id = uuid.uuid4()
        period_id = uuid.uuid4()
        eb = EnvelopeBalance(
            id=uuid.uuid4(),
            budget_id=budget_id,
            period_id=period_id,
            allocated=50000,
            original_allocated=50000,
            rollover=-5000,
        )
        assert eb.budget_id == budget_id
        assert eb.period_id == period_id
        assert eb.allocated == 50000
        assert eb.original_allocated == 50000
        assert eb.rollover == -5000

    def test_envelope_balance_defaults(self):
        """EnvelopeBalance columns default to 0 for allocated, original_allocated, rollover."""
        # SQLAlchemy defaults apply on DB flush, not in-memory.
        # Verify column defaults are configured.
        for col_name in ("allocated", "original_allocated", "rollover"):
            col = EnvelopeBalance.__table__.columns[col_name]
            assert col.default.arg == 0, f"{col_name} should default to 0"

    def test_envelope_balance_negative_rollover(self):
        """EnvelopeBalance supports negative rollover (overspend carry-forward)."""
        eb = EnvelopeBalance(
            id=uuid.uuid4(),
            budget_id=uuid.uuid4(),
            period_id=uuid.uuid4(),
            allocated=40000,
            original_allocated=40000,
            rollover=-12000,
        )
        assert eb.rollover == -12000
        # available would be computed as: 40000 + (-12000) - spent = 28000 - spent

    def test_envelope_balance_tablename(self):
        """EnvelopeBalance uses correct table name."""
        assert EnvelopeBalance.__tablename__ == "envelope_balances"

    def test_envelope_balance_unique_constraint(self):
        """EnvelopeBalance has unique constraint on (budget_id, period_id)."""
        constraints = [
            c.name for c in EnvelopeBalance.__table__.constraints
            if hasattr(c, "name") and c.name
        ]
        assert "uq_envelope_balances_budget_period" in constraints

    def test_envelope_balance_no_account_id_column(self):
        """EnvelopeBalance intentionally has no account_id column."""
        column_names = [c.name for c in EnvelopeBalance.__table__.columns]
        assert "account_id" not in column_names

    def test_envelope_balance_no_spent_column(self):
        """EnvelopeBalance intentionally has no spent column (computed on read)."""
        column_names = [c.name for c in EnvelopeBalance.__table__.columns]
        assert "spent" not in column_names


class TestBudgetSoftDelete:
    """Tests for the Budget soft-delete extension."""

    def test_budget_has_deleted_at_field(self):
        """Budget model has deleted_at field."""
        budget = Budget(
            id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            category="groceries",
            amount=50000,
            period="monthly",
            period_type="monthly",
        )
        assert budget.deleted_at is None

    def test_budget_soft_delete(self):
        """Budget can be soft-deleted by setting deleted_at."""
        budget = Budget(
            id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            category="groceries",
            amount=50000,
            period="monthly",
            period_type="monthly",
        )
        now = datetime.now(timezone.utc)
        budget.deleted_at = now
        assert budget.deleted_at == now

    def test_budget_deleted_at_column_exists(self):
        """Budget table has deleted_at column."""
        column_names = [c.name for c in Budget.__table__.columns]
        assert "deleted_at" in column_names


class TestTransactionEnvelopeExtensions:
    """Tests for Transaction model envelope extensions."""

    def test_transaction_has_budget_id_field(self):
        """Transaction model has budget_id field."""
        tx = Transaction(
            id=uuid.uuid4(),
            monzo_id="tx_123",
            account_id=uuid.uuid4(),
            amount=-5000,
            created_at=datetime.now(timezone.utc),
        )
        assert tx.budget_id is None

    def test_transaction_budget_id_can_be_set(self):
        """Transaction budget_id can be assigned."""
        budget_id = uuid.uuid4()
        tx = Transaction(
            id=uuid.uuid4(),
            monzo_id="tx_123",
            account_id=uuid.uuid4(),
            amount=-5000,
            budget_id=budget_id,
            created_at=datetime.now(timezone.utc),
        )
        assert tx.budget_id == budget_id

    def test_transaction_has_review_status_field(self):
        """Transaction model has review_status field."""
        tx = Transaction(
            id=uuid.uuid4(),
            monzo_id="tx_123",
            account_id=uuid.uuid4(),
            amount=-5000,
            created_at=datetime.now(timezone.utc),
        )
        assert tx.review_status is None

    def test_transaction_review_status_values(self):
        """Transaction review_status can be set to pending or confirmed."""
        tx = Transaction(
            id=uuid.uuid4(),
            monzo_id="tx_123",
            account_id=uuid.uuid4(),
            amount=-5000,
            created_at=datetime.now(timezone.utc),
        )
        tx.review_status = "pending"
        assert tx.review_status == "pending"

        tx.review_status = "confirmed"
        assert tx.review_status == "confirmed"

    def test_transaction_budget_id_column_exists(self):
        """Transaction table has budget_id column."""
        column_names = [c.name for c in Transaction.__table__.columns]
        assert "budget_id" in column_names

    def test_transaction_review_status_column_exists(self):
        """Transaction table has review_status column."""
        column_names = [c.name for c in Transaction.__table__.columns]
        assert "review_status" in column_names


class TestCategoryRuleExtensions:
    """Tests for CategoryRule model income/transfer extensions."""

    def test_category_rule_has_is_income_field(self):
        """CategoryRule has is_income column defaulting to False."""
        col = CategoryRule.__table__.columns["is_income"]
        assert col.default.arg is False

    def test_category_rule_has_is_transfer_field(self):
        """CategoryRule has is_transfer column defaulting to False."""
        col = CategoryRule.__table__.columns["is_transfer"]
        assert col.default.arg is False

    def test_category_rule_income_flag(self):
        """CategoryRule can be flagged as income."""
        rule = CategoryRule(
            id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            name="Sophie's contribution",
            conditions={"merchant_exact": "Sophie Solly"},
            target_category="income",
            is_income=True,
            is_transfer=False,
        )
        assert rule.is_income is True
        assert rule.is_transfer is False

    def test_category_rule_transfer_flag(self):
        """CategoryRule can be flagged as transfer."""
        rule = CategoryRule(
            id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            name="Joint transfer",
            conditions={"merchant_pattern": "Transfer"},
            target_category="transfer",
            is_transfer=True,
            is_income=False,
        )
        assert rule.is_transfer is True
        assert rule.is_income is False

    def test_category_rule_is_income_column_exists(self):
        """CategoryRule table has is_income column."""
        column_names = [c.name for c in CategoryRule.__table__.columns]
        assert "is_income" in column_names

    def test_category_rule_is_transfer_column_exists(self):
        """CategoryRule table has is_transfer column."""
        column_names = [c.name for c in CategoryRule.__table__.columns]
        assert "is_transfer" in column_names


class TestBudgetStartDayNormalisation:
    """Tests for the start_day normalisation requirement."""

    def test_budget_start_day_default(self):
        """Budget start_day column has default value of 1."""
        col = Budget.__table__.columns["start_day"]
        assert col.default.arg == 1

    def test_budget_start_day_can_be_28(self):
        """Budget start_day can be set to 28."""
        budget = Budget(
            id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            category="test",
            amount=10000,
            period="monthly",
            period_type="monthly",
            start_day=28,
        )
        assert budget.start_day == 28


class TestModelRelationships:
    """Tests for relationships between models."""

    def test_budget_has_envelope_balances_relationship(self):
        """Budget model has envelope_balances relationship."""
        assert hasattr(Budget, "envelope_balances")

    def test_budget_period_has_envelope_balances_relationship(self):
        """BudgetPeriod model has envelope_balances relationship."""
        assert hasattr(BudgetPeriod, "envelope_balances")

    def test_envelope_balance_has_budget_relationship(self):
        """EnvelopeBalance model has budget relationship."""
        assert hasattr(EnvelopeBalance, "budget")

    def test_envelope_balance_has_period_relationship(self):
        """EnvelopeBalance model has period relationship."""
        assert hasattr(EnvelopeBalance, "period")

    def test_transaction_has_budget_relationship(self):
        """Transaction model has budget relationship."""
        assert hasattr(Transaction, "budget")
