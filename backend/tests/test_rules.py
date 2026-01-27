"""Tests for category rules engine."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest


class TestRuleMatching:
    """Tests for matching transactions against rules."""

    @pytest.mark.asyncio
    async def test_match_merchant_name_exact(self) -> None:
        """Rule should match transaction by exact merchant name."""
        from app.services.rules import matches_rule

        rule = MagicMock()
        rule.conditions = {"merchant_pattern": "Tesco"}
        rule.enabled = True

        transaction = {
            "merchant": {"name": "Tesco"},
            "amount": -1500,
            "category": "groceries",
        }

        assert matches_rule(transaction, rule) is True

    @pytest.mark.asyncio
    async def test_match_merchant_name_case_insensitive(self) -> None:
        """Rule should match merchant name case-insensitively."""
        from app.services.rules import matches_rule

        rule = MagicMock()
        rule.conditions = {"merchant_pattern": "tesco"}
        rule.enabled = True

        transaction = {
            "merchant": {"name": "TESCO"},
            "amount": -1500,
            "category": "groceries",
        }

        assert matches_rule(transaction, rule) is True

    @pytest.mark.asyncio
    async def test_match_merchant_pattern_contains(self) -> None:
        """Rule should match when merchant name contains pattern."""
        from app.services.rules import matches_rule

        rule = MagicMock()
        rule.conditions = {"merchant_pattern": "Tesco"}
        rule.enabled = True

        transaction = {
            "merchant": {"name": "Tesco Express"},
            "amount": -1500,
            "category": "groceries",
        }

        assert matches_rule(transaction, rule) is True

    @pytest.mark.asyncio
    async def test_no_match_different_merchant(self) -> None:
        """Rule should not match different merchant."""
        from app.services.rules import matches_rule

        rule = MagicMock()
        rule.conditions = {"merchant_pattern": "Tesco"}
        rule.enabled = True

        transaction = {
            "merchant": {"name": "Sainsburys"},
            "amount": -1500,
            "category": "groceries",
        }

        assert matches_rule(transaction, rule) is False

    @pytest.mark.asyncio
    async def test_match_amount_minimum(self) -> None:
        """Rule should match when amount exceeds minimum spend."""
        from app.services.rules import matches_rule

        # amount_min = -10000 means "at least £100 spend"
        # -15000 (£150 spend) is more negative, so it's a larger spend
        rule = MagicMock()
        rule.conditions = {
            "amount_min": -10000,  # £100 minimum spend
            "monzo_category": "groceries",
        }
        rule.enabled = True

        transaction = {
            "merchant": {"name": "Tesco"},
            "amount": -15000,  # £150 spend
            "category": "groceries",
        }

        assert matches_rule(transaction, rule) is True

    @pytest.mark.asyncio
    async def test_no_match_below_minimum(self) -> None:
        """Rule should not match when amount is below minimum spend."""
        from app.services.rules import matches_rule

        rule = MagicMock()
        rule.conditions = {
            "amount_min": -10000,  # £100 minimum spend
            "monzo_category": "groceries",
        }
        rule.enabled = True

        transaction = {
            "merchant": {"name": "Tesco"},
            "amount": -5000,  # £50 spend (below minimum)
            "category": "groceries",
        }

        assert matches_rule(transaction, rule) is False

    @pytest.mark.asyncio
    async def test_match_amount_range(self) -> None:
        """Rule should match when amount is within range."""
        from app.services.rules import matches_rule

        # Range: spend between £50 and £100
        # For spending (negative amounts):
        # - amount_min = -5000: fail if spend < £50 (amount > -5000)
        # - amount_max = -10000: fail if spend > £100 (amount < -10000)
        rule = MagicMock()
        rule.conditions = {
            "amount_min": -5000,   # Minimum spend of £50 (fail if > -5000)
            "amount_max": -10000,  # Maximum spend of £100 (fail if < -10000)
            "monzo_category": "groceries",
        }
        rule.enabled = True

        transaction = {
            "merchant": {"name": "Tesco"},
            "amount": -7500,  # £75 (between £50 and £100)
            "category": "groceries",
        }

        assert matches_rule(transaction, rule) is True

    @pytest.mark.asyncio
    async def test_match_monzo_category(self) -> None:
        """Rule should match by Monzo category."""
        from app.services.rules import matches_rule

        rule = MagicMock()
        rule.conditions = {"monzo_category": "eating_out"}
        rule.enabled = True

        transaction = {
            "merchant": {"name": "Pret"},
            "amount": -500,
            "category": "eating_out",
        }

        assert matches_rule(transaction, rule) is True

    @pytest.mark.asyncio
    async def test_disabled_rule_never_matches(self) -> None:
        """Disabled rules should never match."""
        from app.services.rules import matches_rule

        rule = MagicMock()
        rule.conditions = {"merchant_pattern": "Tesco"}
        rule.enabled = False

        transaction = {
            "merchant": {"name": "Tesco"},
            "amount": -1500,
            "category": "groceries",
        }

        assert matches_rule(transaction, rule) is False

    @pytest.mark.asyncio
    async def test_match_with_combined_conditions(self) -> None:
        """Rule should match when all conditions are satisfied."""
        from app.services.rules import matches_rule

        rule = MagicMock()
        rule.conditions = {
            "merchant_pattern": "Tesco",
            "amount_min": -10000,  # £100 minimum spend
            "monzo_category": "groceries",
        }
        rule.enabled = True

        transaction = {
            "merchant": {"name": "Tesco Express"},
            "amount": -15000,  # £150
            "category": "groceries",
        }

        assert matches_rule(transaction, rule) is True

    @pytest.mark.asyncio
    async def test_no_match_partial_conditions(self) -> None:
        """Rule should not match when any condition fails."""
        from app.services.rules import matches_rule

        rule = MagicMock()
        rule.conditions = {
            "merchant_pattern": "Tesco",
            "amount_min": -10000,  # £100 minimum spend
            "monzo_category": "groceries",
        }
        rule.enabled = True

        # Right merchant and category, but amount too low
        transaction = {
            "merchant": {"name": "Tesco"},
            "amount": -5000,  # £50 (below minimum)
            "category": "groceries",
        }

        assert matches_rule(transaction, rule) is False


class TestCategoryAssignment:
    """Tests for assigning categories to transactions."""

    @pytest.mark.asyncio
    async def test_apply_first_matching_rule_by_priority(self) -> None:
        """Should apply the highest priority matching rule."""
        from app.services.rules import categorise_transaction

        high_priority_rule = MagicMock()
        high_priority_rule.conditions = {"merchant_pattern": "Tesco"}
        high_priority_rule.enabled = True
        high_priority_rule.priority = 100
        high_priority_rule.target_category = "Weekly Shop"

        low_priority_rule = MagicMock()
        low_priority_rule.conditions = {"merchant_pattern": "Tesco"}
        low_priority_rule.enabled = True
        low_priority_rule.priority = 10
        low_priority_rule.target_category = "Groceries"

        rules = [low_priority_rule, high_priority_rule]

        transaction = {
            "merchant": {"name": "Tesco"},
            "amount": -1500,
            "category": "groceries",
        }

        result = categorise_transaction(transaction, rules)

        assert result == "Weekly Shop"

    @pytest.mark.asyncio
    async def test_return_none_when_no_rules_match(self) -> None:
        """Should return None when no rules match."""
        from app.services.rules import categorise_transaction

        rule = MagicMock()
        rule.conditions = {"merchant_pattern": "Waitrose"}
        rule.enabled = True
        rule.priority = 50
        rule.target_category = "Posh Groceries"

        rules = [rule]

        transaction = {
            "merchant": {"name": "Tesco"},
            "amount": -1500,
            "category": "groceries",
        }

        result = categorise_transaction(transaction, rules)

        assert result is None

    @pytest.mark.asyncio
    async def test_skip_disabled_rules(self) -> None:
        """Should skip disabled rules even with high priority."""
        from app.services.rules import categorise_transaction

        disabled_rule = MagicMock()
        disabled_rule.conditions = {"merchant_pattern": "Tesco"}
        disabled_rule.enabled = False
        disabled_rule.priority = 100
        disabled_rule.target_category = "Disabled Category"

        enabled_rule = MagicMock()
        enabled_rule.conditions = {"merchant_pattern": "Tesco"}
        enabled_rule.enabled = True
        enabled_rule.priority = 10
        enabled_rule.target_category = "Active Category"

        rules = [disabled_rule, enabled_rule]

        transaction = {
            "merchant": {"name": "Tesco"},
            "amount": -1500,
            "category": "groceries",
        }

        result = categorise_transaction(transaction, rules)

        assert result == "Active Category"


class TestRulesService:
    """Tests for the rules service database operations."""

    @pytest.mark.asyncio
    async def test_get_all_enabled_rules(self) -> None:
        """Should fetch all enabled rules ordered by priority for an account."""
        from app.services.rules import RulesService
        from uuid import uuid4

        account_id = str(uuid4())

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            MagicMock(priority=100, account_id=account_id),
            MagicMock(priority=50, account_id=account_id),
        ]
        mock_session.execute.return_value = mock_result

        service = RulesService(mock_session)
        rules = await service.get_enabled_rules(account_id)

        assert len(rules) == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_rule(self) -> None:
        """Should create a new category rule for an account."""
        from app.services.rules import RulesService
        from uuid import uuid4

        account_id = str(uuid4())
        mock_session = AsyncMock()

        service = RulesService(mock_session)
        rule = await service.create_rule(
            account_id=account_id,
            name="Tesco Rule",
            merchant_pattern="Tesco",
            target_category="Groceries",
            priority=50,
        )

        mock_session.add.assert_called_once()
        assert rule.name == "Tesco Rule"
        assert rule.target_category == "Groceries"
        assert rule.priority == 50
        assert rule.conditions["merchant_pattern"] == "Tesco"
        assert rule.account_id == account_id

    @pytest.mark.asyncio
    async def test_update_rule(self) -> None:
        """Should update an existing rule."""
        from app.services.rules import RulesService

        existing_rule = MagicMock()
        existing_rule.id = "rule_123"
        existing_rule.conditions = {"merchant_pattern": "Old"}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_rule

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        service = RulesService(mock_session)
        updated = await service.update_rule(
            rule_id="rule_123",
            target_category="New Category",
        )

        assert updated.target_category == "New Category"

    @pytest.mark.asyncio
    async def test_delete_rule(self) -> None:
        """Should delete a rule."""
        from app.services.rules import RulesService

        existing_rule = MagicMock()
        existing_rule.id = "rule_123"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_rule

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        service = RulesService(mock_session)
        result = await service.delete_rule("rule_123")

        assert result is True
        mock_session.delete.assert_called_once_with(existing_rule)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_rule(self) -> None:
        """Should return False when deleting nonexistent rule."""
        from app.services.rules import RulesService

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        service = RulesService(mock_session)
        result = await service.delete_rule("nonexistent")

        assert result is False
        mock_session.delete.assert_not_called()
