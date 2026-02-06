"""Category rules engine for transaction categorisation."""

from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CategoryRule


def matches_rule(transaction: dict[str, Any], rule: CategoryRule) -> bool:
    """Check if a transaction matches a rule's conditions.

    Conditions are stored as JSON with keys:
    - merchant_pattern: Pattern to match in merchant name
    - amount_min: Minimum amount (pence, negative for spend)
    - amount_max: Maximum amount (pence, negative for spend)
    - monzo_category: Monzo category to match

    All conditions must be satisfied (AND logic).

    Args:
        transaction: Transaction data from Monzo API
        rule: Category rule to check against

    Returns:
        True if all rule conditions are satisfied
    """
    # Disabled rules never match
    if not rule.enabled:
        return False

    conditions = rule.conditions or {}

    # Check merchant pattern (substring, case-insensitive)
    merchant_pattern = conditions.get("merchant_pattern")
    if merchant_pattern:
        merchant = transaction.get("merchant") or {}
        merchant_name = merchant.get("name") if isinstance(merchant, dict) else None
        if not merchant_name:
            return False
        if merchant_pattern.lower() not in merchant_name.lower():
            return False

    # Check exact merchant name match (case-insensitive)
    merchant_exact = conditions.get("merchant_exact")
    if merchant_exact:
        merchant = transaction.get("merchant") or {}
        merchant_name = merchant.get("name") if isinstance(merchant, dict) else None
        if not merchant_name:
            return False
        if merchant_name.lower() != merchant_exact.lower():
            return False

    # Check amount minimum (amounts are negative for spending)
    # amount_min is the minimum spend threshold (more negative = larger spend)
    # -15000 < -10000 means £150 > £100 (larger spend)
    amount_min = conditions.get("amount_min")
    if amount_min is not None:
        amount = transaction.get("amount", 0)
        # For spending: we want amount <= amount_min (more negative = larger spend)
        if amount > amount_min:  # Less negative = smaller spend
            return False

    # Check amount maximum (upper bound on spend)
    # amount_max is the maximum spend threshold (less negative = smaller spend)
    amount_max = conditions.get("amount_max")
    if amount_max is not None:
        amount = transaction.get("amount", 0)
        # For spending: we want amount >= amount_max (less negative = smaller spend)
        if amount < amount_max:  # More negative = larger spend, fails max
            return False

    # Check Monzo category
    monzo_category = conditions.get("monzo_category")
    if monzo_category:
        tx_category = transaction.get("category")
        if tx_category != monzo_category:
            return False

    # Check day of week (0=Monday, 6=Sunday)
    day_of_week = conditions.get("day_of_week")
    if day_of_week is not None:
        created = transaction.get("created")
        if not created:
            return False
        from datetime import datetime
        try:
            tx_date = datetime.fromisoformat(created)
            if tx_date.weekday() != day_of_week:
                return False
        except (ValueError, TypeError):
            return False

    return True


def categorise_transaction(
    transaction: dict[str, Any],
    rules: list[CategoryRule],
) -> str | None:
    """Assign a custom category to a transaction based on rules.

    Rules are applied in priority order (highest first).
    First matching rule wins.

    Args:
        transaction: Transaction data from Monzo API
        rules: List of category rules to apply

    Returns:
        Custom category name if a rule matches, None otherwise
    """
    # Sort by priority descending (highest priority first)
    sorted_rules = sorted(rules, key=lambda r: r.priority, reverse=True)

    for rule in sorted_rules:
        if matches_rule(transaction, rule):
            return rule.target_category

    return None


class RulesService:
    """Service for managing category rules."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session

    async def get_enabled_rules(self, account_id: str) -> list[CategoryRule]:
        """Get all enabled rules for an account ordered by priority.

        Args:
            account_id: Account ID to filter rules

        Returns:
            List of enabled category rules for the account
        """
        result = await self._session.execute(
            select(CategoryRule)
            .where(CategoryRule.account_id == account_id)
            .where(CategoryRule.enabled.is_(True))
            .order_by(CategoryRule.priority.desc())
        )
        return list(result.scalars().all())

    async def get_all_rules(self, account_id: str) -> list[CategoryRule]:
        """Get all rules for an account ordered by priority.

        Args:
            account_id: Account ID to filter rules

        Returns:
            List of all category rules for the account
        """
        result = await self._session.execute(
            select(CategoryRule)
            .where(CategoryRule.account_id == account_id)
            .order_by(CategoryRule.priority.desc())
        )
        return list(result.scalars().all())

    async def create_rule(
        self,
        account_id: str,
        name: str,
        target_category: str,
        priority: int = 50,
        merchant_pattern: str | None = None,
        amount_min: int | None = None,
        amount_max: int | None = None,
        monzo_category: str | None = None,
        enabled: bool = True,
    ) -> CategoryRule:
        """Create a new category rule for an account.

        Args:
            account_id: Account ID to associate the rule with
            name: Rule name
            target_category: Custom category to assign
            priority: Rule priority (higher = checked first)
            merchant_pattern: Pattern to match in merchant name
            amount_min: Minimum amount (pence, negative for spend)
            amount_max: Maximum amount (pence, negative for spend)
            monzo_category: Monzo category to match
            enabled: Whether rule is active

        Returns:
            Created category rule
        """
        conditions: dict[str, Any] = {}
        if merchant_pattern:
            conditions["merchant_pattern"] = merchant_pattern
        if amount_min is not None:
            conditions["amount_min"] = amount_min
        if amount_max is not None:
            conditions["amount_max"] = amount_max
        if monzo_category:
            conditions["monzo_category"] = monzo_category

        rule = CategoryRule(
            id=uuid4(),
            account_id=account_id,
            name=name,
            conditions=conditions,
            target_category=target_category,
            priority=priority,
            enabled=enabled,
        )
        self._session.add(rule)
        return rule

    async def update_rule(
        self,
        rule_id: str,
        name: str | None = None,
        merchant_pattern: str | None = None,
        amount_min: int | None = None,
        amount_max: int | None = None,
        monzo_category: str | None = None,
        target_category: str | None = None,
        priority: int | None = None,
        enabled: bool | None = None,
    ) -> CategoryRule | None:
        """Update an existing category rule.

        Args:
            rule_id: ID of rule to update
            **kwargs: Fields to update

        Returns:
            Updated rule or None if not found
        """
        result = await self._session.execute(
            select(CategoryRule).where(CategoryRule.id == rule_id)
        )
        rule = result.scalar_one_or_none()

        if not rule:
            return None

        if name is not None:
            rule.name = name
        if target_category is not None:
            rule.target_category = target_category
        if priority is not None:
            rule.priority = priority
        if enabled is not None:
            rule.enabled = enabled

        # Update conditions if any condition fields provided
        # Empty string clears a string condition; None means "don't change"
        conditions = dict(rule.conditions)
        for key, value in [
            ("merchant_pattern", merchant_pattern),
            ("monzo_category", monzo_category),
        ]:
            if value is None:
                continue
            if value == "":
                conditions.pop(key, None)
            else:
                conditions[key] = value
        if amount_min is not None:
            conditions["amount_min"] = amount_min
        if amount_max is not None:
            conditions["amount_max"] = amount_max
        rule.conditions = conditions

        return rule

    async def delete_rule(self, rule_id: str) -> bool:
        """Delete a category rule.

        Args:
            rule_id: ID of rule to delete

        Returns:
            True if deleted, False if not found
        """
        result = await self._session.execute(
            select(CategoryRule).where(CategoryRule.id == rule_id)
        )
        rule = result.scalar_one_or_none()

        if not rule:
            return False

        await self._session.delete(rule)
        return True
