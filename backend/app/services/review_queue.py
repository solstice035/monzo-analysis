"""Review queue service for managing pending transaction reviews.

Provides endpoints for:
- Listing pending review transactions
- Confirming, reassigning, or excluding transactions
- Auto-creating CategoryRules after review actions
"""

import logging
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Budget, CategoryRule, Transaction

logger = logging.getLogger(__name__)


class ReviewQueueService:
    """Service for managing the transaction review queue."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_pending_transactions(
        self,
        account_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Transaction], int]:
        """Get transactions with review_status='pending', sorted by date desc.

        Args:
            account_id: Account to filter by.
            limit: Max items to return.
            offset: Pagination offset.

        Returns:
            Tuple of (transactions, total_count).
        """
        base_filter = and_(
            Transaction.account_id == account_id,
            Transaction.review_status == "pending",
        )

        # Count total
        count_result = await self._session.execute(
            select(func.count()).select_from(Transaction).where(base_filter)
        )
        total = count_result.scalar() or 0

        # Fetch page
        result = await self._session.execute(
            select(Transaction)
            .where(base_filter)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        transactions = list(result.scalars().all())

        return transactions, total

    async def confirm_transaction(
        self,
        transaction_id: UUID,
        account_id: UUID,
    ) -> Transaction | None:
        """Confirm the auto-assigned budget for a transaction.

        Sets review_status='confirmed'. If no CategoryRule exists for this
        merchant, creates one automatically.

        Returns:
            Updated transaction, or None if not found.
        """
        tx = await self._get_pending_transaction(transaction_id, account_id)
        if not tx:
            return None

        tx.review_status = "confirmed"

        # Auto-create rule if merchant is known
        if tx.merchant_name and tx.budget_id:
            await self._ensure_category_rule(
                account_id=account_id,
                merchant_name=tx.merchant_name,
                budget_id=tx.budget_id,
            )

        return tx

    async def reassign_transaction(
        self,
        transaction_id: UUID,
        account_id: UUID,
        new_budget_id: UUID,
    ) -> Transaction | None:
        """Reassign a transaction to a different budget and confirm.

        Updates budget_id and sets review_status='confirmed'.
        Auto-creates/updates CategoryRule for this merchant.

        Returns:
            Updated transaction, or None if not found.
        """
        tx = await self._get_pending_transaction(transaction_id, account_id)
        if not tx:
            return None

        # Verify the target budget exists and belongs to the account
        budget_result = await self._session.execute(
            select(Budget).where(
                and_(
                    Budget.id == new_budget_id,
                    Budget.account_id == account_id,
                    Budget.deleted_at.is_(None),
                )
            )
        )
        budget = budget_result.scalar_one_or_none()
        if not budget:
            return None

        tx.budget_id = new_budget_id
        tx.review_status = "confirmed"

        # Auto-create rule for this merchant → new budget's category
        if tx.merchant_name:
            await self._ensure_category_rule(
                account_id=account_id,
                merchant_name=tx.merchant_name,
                budget_id=new_budget_id,
            )

        return tx

    async def exclude_transaction(
        self,
        transaction_id: UUID,
        account_id: UUID,
    ) -> Transaction | None:
        """Exclude a transaction from all envelopes.

        Sets budget_id=NULL and review_status='confirmed'.

        Returns:
            Updated transaction, or None if not found.
        """
        tx = await self._get_pending_transaction(transaction_id, account_id)
        if not tx:
            return None

        tx.budget_id = None
        tx.review_status = "confirmed"
        return tx

    async def _get_pending_transaction(
        self,
        transaction_id: UUID,
        account_id: UUID,
    ) -> Transaction | None:
        """Get a pending transaction by ID and account."""
        result = await self._session.execute(
            select(Transaction).where(
                and_(
                    Transaction.id == transaction_id,
                    Transaction.account_id == account_id,
                    Transaction.review_status == "pending",
                )
            )
        )
        return result.scalar_one_or_none()

    async def _ensure_category_rule(
        self,
        account_id: UUID,
        merchant_name: str,
        budget_id: UUID,
    ) -> None:
        """Create or update a CategoryRule for a merchant.

        If a rule with merchant_exact match exists, updates its target category.
        Otherwise creates a new rule with high priority.
        """
        # Find the budget's category
        budget_result = await self._session.execute(
            select(Budget).where(Budget.id == budget_id)
        )
        budget = budget_result.scalar_one_or_none()
        if not budget:
            return

        # Check for existing rule with this merchant
        existing_result = await self._session.execute(
            select(CategoryRule).where(
                and_(
                    CategoryRule.account_id == account_id,
                    CategoryRule.conditions.contains({"merchant_exact": merchant_name}),
                )
            )
        )
        existing_rule = existing_result.scalar_one_or_none()

        if existing_rule:
            # Update target category and bump priority
            existing_rule.target_category = budget.category
            existing_rule.priority = max(existing_rule.priority, 100)
            logger.info(f"Updated rule for merchant '{merchant_name}' → {budget.category}")
        else:
            # Create new rule
            new_rule = CategoryRule(
                id=uuid4(),
                account_id=account_id,
                name=f"Auto: {merchant_name}",
                conditions={"merchant_exact": merchant_name},
                target_category=budget.category,
                priority=100,  # High priority for user-confirmed rules
                enabled=True,
                is_income=False,
                is_transfer=False,
            )
            self._session.add(new_rule)
            logger.info(f"Created rule for merchant '{merchant_name}' → {budget.category}")
