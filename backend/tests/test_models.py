"""Tests for database models."""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.models import (
    Account,
    Auth,
    Base,
    Budget,
    BudgetGroup,
    CategoryRule,
    Pot,
    Setting,
    SyncLog,
    Transaction,
)


@pytest.fixture
def engine():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def session(engine):
    """Create a database session for testing."""
    with Session(engine) as session:
        yield session


class TestAccountModel:
    """Tests for the Account model."""

    def test_account_creation(self, session: Session) -> None:
        """Account can be created with required fields."""
        account = Account(
            monzo_id="acc_12345",
            type="uk_retail",
            name="Personal Account",
        )
        session.add(account)
        session.commit()

        result = session.execute(select(Account)).scalar_one()
        assert result.monzo_id == "acc_12345"
        assert result.type == "uk_retail"
        assert result.name == "Personal Account"
        assert result.id is not None
        assert isinstance(result.created_at, datetime)

    def test_account_monzo_id_unique(self, session: Session) -> None:
        """Account monzo_id must be unique."""
        account1 = Account(monzo_id="acc_12345", type="uk_retail")
        account2 = Account(monzo_id="acc_12345", type="uk_retail_joint")
        session.add(account1)
        session.commit()
        session.add(account2)
        with pytest.raises(Exception):  # IntegrityError
            session.commit()


class TestTransactionModel:
    """Tests for the Transaction model."""

    def test_transaction_creation(self, session: Session) -> None:
        """Transaction can be created with required fields."""
        account = Account(monzo_id="acc_12345", type="uk_retail")
        session.add(account)
        session.commit()

        transaction = Transaction(
            monzo_id="tx_12345",
            account_id=account.id,
            amount=-1500,  # £15.00 spend
            merchant_name="Tesco",
            monzo_category="groceries",
            created_at=datetime.now(timezone.utc),
        )
        session.add(transaction)
        session.commit()

        result = session.execute(select(Transaction)).scalar_one()
        assert result.monzo_id == "tx_12345"
        assert result.amount == -1500
        assert result.merchant_name == "Tesco"
        assert result.monzo_category == "groceries"
        assert result.custom_category is None

    def test_transaction_with_custom_category(self, session: Session) -> None:
        """Transaction can have a custom category override."""
        account = Account(monzo_id="acc_12345", type="uk_retail")
        session.add(account)
        session.commit()

        transaction = Transaction(
            monzo_id="tx_12345",
            account_id=account.id,
            amount=-8500,
            merchant_name="Tesco",
            monzo_category="groceries",
            custom_category="groceries-big-shop",
            created_at=datetime.now(timezone.utc),
        )
        session.add(transaction)
        session.commit()

        result = session.execute(select(Transaction)).scalar_one()
        assert result.custom_category == "groceries-big-shop"

    def test_transaction_stores_raw_payload(self, session: Session) -> None:
        """Transaction can store the full Monzo API response."""
        account = Account(monzo_id="acc_12345", type="uk_retail")
        session.add(account)
        session.commit()

        raw_payload = {
            "id": "tx_12345",
            "amount": -1500,
            "merchant": {"name": "Tesco", "mcc": "5411"},
        }
        transaction = Transaction(
            monzo_id="tx_12345",
            account_id=account.id,
            amount=-1500,
            created_at=datetime.now(timezone.utc),
            raw_payload=raw_payload,
        )
        session.add(transaction)
        session.commit()

        result = session.execute(select(Transaction)).scalar_one()
        assert result.raw_payload == raw_payload
        assert result.raw_payload["merchant"]["mcc"] == "5411"


class TestPotModel:
    """Tests for the Pot model."""

    def test_pot_creation(self, session: Session) -> None:
        """Pot can be created with required fields."""
        account = Account(monzo_id="acc_12345", type="uk_retail")
        session.add(account)
        session.commit()

        pot = Pot(
            monzo_id="pot_12345",
            account_id=account.id,
            name="Holiday Fund",
            balance=50000,  # £500.00
        )
        session.add(pot)
        session.commit()

        result = session.execute(select(Pot)).scalar_one()
        assert result.monzo_id == "pot_12345"
        assert result.name == "Holiday Fund"
        assert result.balance == 50000
        assert result.deleted is False


class TestBudgetModel:
    """Tests for the Budget model."""

    def test_budget_creation(self, session: Session) -> None:
        """Budget can be created with required fields."""
        account = Account(monzo_id="acc_12345", type="uk_retail")
        session.add(account)
        session.commit()

        budget = Budget(
            account_id=account.id,
            category="groceries",
            amount=40000,  # £400.00
            period="monthly",
            start_day=1,
        )
        session.add(budget)
        session.commit()

        result = session.execute(select(Budget)).scalar_one()
        assert result.category == "groceries"
        assert result.amount == 40000
        assert result.period == "monthly"
        assert result.start_day == 1
        assert result.account_id == account.id

    def test_budget_weekly_period(self, session: Session) -> None:
        """Budget can have weekly period."""
        account = Account(monzo_id="acc_12345", type="uk_retail")
        session.add(account)
        session.commit()

        budget = Budget(
            account_id=account.id,
            category="eating_out",
            amount=5000,  # £50.00
            period="weekly",
        )
        session.add(budget)
        session.commit()

        result = session.execute(select(Budget)).scalar_one()
        assert result.period == "weekly"

    def test_budget_with_sinking_fund_fields(self, session: Session) -> None:
        """Budget can have sinking fund configuration."""
        account = Account(monzo_id="acc_12345", type="uk_retail")
        session.add(account)
        session.commit()

        budget = Budget(
            account_id=account.id,
            name="Car Tax",
            category="car",
            amount=5625,  # £56.25 monthly contribution
            period="monthly",
            period_type="annual",
            annual_amount=67500,  # £675 annual
            target_month=10,  # October
        )
        session.add(budget)
        session.commit()

        result = session.execute(select(Budget)).scalar_one()
        assert result.name == "Car Tax"
        assert result.period_type == "annual"
        assert result.annual_amount == 67500
        assert result.target_month == 10
        assert result.is_sinking_fund is True
        assert result.monthly_contribution == 5625  # 67500 // 12


class TestBudgetGroupModel:
    """Tests for the BudgetGroup model."""

    def test_budget_group_creation(self, session: Session) -> None:
        """BudgetGroup can be created with required fields."""
        account = Account(monzo_id="acc_12345", type="uk_retail")
        session.add(account)
        session.commit()

        group = BudgetGroup(
            account_id=account.id,
            name="Kids",
            icon="child",
            display_order=1,
        )
        session.add(group)
        session.commit()

        result = session.execute(select(BudgetGroup)).scalar_one()
        assert result.name == "Kids"
        assert result.icon == "child"
        assert result.display_order == 1
        assert result.account_id == account.id

    def test_budget_group_with_budgets(self, session: Session) -> None:
        """BudgetGroup can contain multiple budgets."""
        account = Account(monzo_id="acc_12345", type="uk_retail")
        session.add(account)
        session.commit()

        group = BudgetGroup(
            account_id=account.id,
            name="Kids",
        )
        session.add(group)
        session.commit()

        budget1 = Budget(
            account_id=account.id,
            group_id=group.id,
            name="Piano Lessons",
            category="kids",
            amount=8000,
            period="monthly",
        )
        budget2 = Budget(
            account_id=account.id,
            group_id=group.id,
            name="Swimming",
            category="kids",
            amount=5000,
            period="monthly",
        )
        session.add_all([budget1, budget2])
        session.commit()

        result = session.execute(select(BudgetGroup)).scalar_one()
        assert len(result.budgets) == 2


class TestCategoryRuleModel:
    """Tests for the CategoryRule model."""

    def test_rule_creation(self, session: Session) -> None:
        """CategoryRule can be created with conditions."""
        account = Account(monzo_id="acc_12345", type="uk_retail")
        session.add(account)
        session.commit()

        rule = CategoryRule(
            account_id=account.id,
            name="Big Shop",
            conditions={"merchant_contains": "Tesco", "amount_gt": 8000},
            target_category="groceries-big-shop",
            priority=10,
        )
        session.add(rule)
        session.commit()

        result = session.execute(select(CategoryRule)).scalar_one()
        assert result.name == "Big Shop"
        assert result.conditions["merchant_contains"] == "Tesco"
        assert result.conditions["amount_gt"] == 8000
        assert result.target_category == "groceries-big-shop"
        assert result.priority == 10
        assert result.enabled is True
        assert result.account_id == account.id

    def test_rule_can_be_disabled(self, session: Session) -> None:
        """CategoryRule can be disabled."""
        account = Account(monzo_id="acc_12345", type="uk_retail")
        session.add(account)
        session.commit()

        rule = CategoryRule(
            account_id=account.id,
            name="Test Rule",
            conditions={},
            target_category="test",
            enabled=False,
        )
        session.add(rule)
        session.commit()

        result = session.execute(select(CategoryRule)).scalar_one()
        assert result.enabled is False


class TestSyncLogModel:
    """Tests for the SyncLog model."""

    def test_sync_log_creation(self, session: Session) -> None:
        """SyncLog can be created to track sync operations."""
        sync_log = SyncLog(
            started_at=datetime.now(timezone.utc),
            status="running",
        )
        session.add(sync_log)
        session.commit()

        result = session.execute(select(SyncLog)).scalar_one()
        assert result.status == "running"
        assert result.transactions_synced == 0
        assert result.completed_at is None

    def test_sync_log_completion(self, session: Session) -> None:
        """SyncLog can be updated on completion."""
        sync_log = SyncLog(
            started_at=datetime.now(timezone.utc),
            status="running",
        )
        session.add(sync_log)
        session.commit()

        sync_log.status = "success"
        sync_log.completed_at = datetime.now(timezone.utc)
        sync_log.transactions_synced = 25
        session.commit()

        result = session.execute(select(SyncLog)).scalar_one()
        assert result.status == "success"
        assert result.transactions_synced == 25
        assert result.completed_at is not None


class TestAuthModel:
    """Tests for the Auth model (OAuth tokens)."""

    def test_auth_creation(self, session: Session) -> None:
        """Auth can store OAuth tokens."""
        auth = Auth(
            access_token="access_12345",
            refresh_token="refresh_12345",
            expires_at=datetime.now(timezone.utc),
        )
        session.add(auth)
        session.commit()

        result = session.execute(select(Auth)).scalar_one()
        assert result.access_token == "access_12345"
        assert result.refresh_token == "refresh_12345"
        assert result.expires_at is not None


class TestSettingModel:
    """Tests for the Setting model (key-value store)."""

    def test_setting_creation(self, session: Session) -> None:
        """Setting can store key-value pairs."""
        setting = Setting(
            key="slack_webhook_url",
            value={"url": "https://hooks.slack.com/..."},
        )
        session.add(setting)
        session.commit()

        result = session.execute(select(Setting)).scalar_one()
        assert result.key == "slack_webhook_url"
        assert result.value["url"] == "https://hooks.slack.com/..."

    def test_setting_key_unique(self, session: Session) -> None:
        """Setting key must be unique."""
        setting1 = Setting(key="test_key", value={"v": 1})
        setting2 = Setting(key="test_key", value={"v": 2})
        session.add(setting1)
        session.commit()
        session.add(setting2)
        with pytest.raises(Exception):  # IntegrityError
            session.commit()
