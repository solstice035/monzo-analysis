"""Transaction assignment service for linking transactions to budget envelopes.

Extends the rules engine to assign budget_id after categorisation:
- High confidence (exact merchant match): auto-assign, review_status = NULL
- Low confidence / no match: best-guess, review_status = 'pending'
- Income/transfer rules: skip envelope assignment entirely
"""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select, and_, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Budget, CategoryRule, Transaction
from app.services.rules import categorise_transaction, matches_rule

logger = logging.getLogger(__name__)


class TransactionAssignmentService:
    """Service for assigning transactions to budget envelopes."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def assign_transaction(
        self,
        transaction_data: dict[str, Any],
        transaction_id: UUID,
        account_id: UUID,
        rules: list[CategoryRule],
    ) -> tuple[UUID | None, str | None]:
        """Assign a transaction to a budget envelope based on rules.

        Flow:
        1. Run rules engine to get category and matching rule
        2. If rule is income/transfer → skip envelope assignment
        3. Look up Budget by category match
        4. If high confidence (exact merchant match) → auto-assign
        5. If low confidence / no match → mark pending

        Args:
            transaction_data: Raw Monzo transaction data.
            transaction_id: Database transaction ID.
            account_id: Account ID for budget lookup.
            rules: Pre-loaded enabled rules for the account.

        Returns:
            Tuple of (budget_id, review_status).
        """
        # Find matching rule
        matched_rule = self._find_matching_rule(transaction_data, rules)

        if not matched_rule:
            # No rule matches — set as pending review
            return None, "pending"

        # Check if income or transfer — skip envelope assignment
        if getattr(matched_rule, "is_income", False) or getattr(matched_rule, "is_transfer", False):
            return None, None

        # Look up budget by target category
        budget = await self._find_budget_by_category(
            account_id, matched_rule.target_category
        )

        if not budget:
            # Category exists in rules but no matching budget — pending review
            return None, "pending"

        # Determine confidence
        confidence = self._assess_confidence(transaction_data, matched_rule)

        if confidence == "high":
            return budget.id, None  # Auto-assigned, no review needed
        else:
            return budget.id, "pending"  # Best guess, needs review

    async def backfill_existing_transactions(
        self,
        account_id: UUID,
    ) -> dict[str, int]:
        """One-time backfill: match existing transactions' custom_category → budget_id.

        For transactions that already have a custom_category but no budget_id,
        find the matching Budget and assign.

        Returns:
            Dict with counts: assigned, unmatched, skipped.
        """
        # Load all active budgets for the account
        budgets = await self._get_budgets_by_category(account_id)
        if not budgets:
            return {"assigned": 0, "unmatched": 0, "skipped": 0}

        # Find transactions with custom_category but no budget_id
        result = await self._session.execute(
            select(Transaction).where(
                and_(
                    Transaction.account_id == account_id,
                    Transaction.custom_category.isnot(None),
                    Transaction.budget_id.is_(None),
                )
            )
        )
        transactions = list(result.scalars().all())

        assigned = 0
        unmatched = 0
        skipped = 0

        for tx in transactions:
            category_key = tx.custom_category.lower().strip() if tx.custom_category else None
            if not category_key:
                skipped += 1
                continue

            budget = budgets.get(category_key)
            if budget:
                tx.budget_id = budget.id
                assigned += 1
            else:
                tx.review_status = "pending"
                unmatched += 1

        await self._session.flush()
        return {"assigned": assigned, "unmatched": unmatched, "skipped": skipped}

    def _find_matching_rule(
        self,
        transaction_data: dict[str, Any],
        rules: list[CategoryRule],
    ) -> CategoryRule | None:
        """Find the first matching rule for a transaction (by priority)."""
        sorted_rules = sorted(rules, key=lambda r: r.priority, reverse=True)
        for rule in sorted_rules:
            if matches_rule(transaction_data, rule):
                return rule
        return None

    def _assess_confidence(
        self,
        transaction_data: dict[str, Any],
        rule: CategoryRule,
    ) -> str:
        """Assess confidence of a rule match.

        'high' = exact merchant match (merchant_exact condition).
        'low' = fuzzy/pattern match or other conditions only.
        """
        conditions = rule.conditions or {}
        if "merchant_exact" in conditions:
            return "high"
        if "merchant_pattern" in conditions:
            # Pattern match is still decent confidence
            merchant = transaction_data.get("merchant") or {}
            merchant_name = merchant.get("name") if isinstance(merchant, dict) else None
            pattern = conditions["merchant_pattern"]
            if merchant_name and merchant_name.lower() == pattern.lower():
                # Pattern matches exactly — treat as high confidence
                return "high"
        return "low"

    async def _find_budget_by_category(
        self,
        account_id: UUID,
        category: str,
    ) -> Budget | None:
        """Find a budget matching a category name (case-insensitive)."""
        result = await self._session.execute(
            select(Budget).where(
                and_(
                    Budget.account_id == account_id,
                    func.lower(Budget.category) == category.lower().strip(),
                    Budget.deleted_at.is_(None),
                )
            )
        )
        return result.scalar_one_or_none()

    async def _get_budgets_by_category(
        self,
        account_id: UUID,
    ) -> dict[str, Budget]:
        """Load all active budgets indexed by lowercase category."""
        result = await self._session.execute(
            select(Budget).where(
                and_(
                    Budget.account_id == account_id,
                    Budget.deleted_at.is_(None),
                )
            )
        )
        return {
            b.category.lower().strip(): b
            for b in result.scalars().all()
        }
