"""Pot service for Monzo pot integration with sinking fund budgets."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Budget, Pot, Transaction
from app.services.budget import calculate_sinking_fund_months


@dataclass
class PotBalance:
    """Current state of a Monzo pot."""

    pot_id: UUID
    monzo_id: str
    name: str
    balance: int  # Current balance in pence
    deleted: bool
    updated_at: datetime


@dataclass
class PotContribution:
    """A contribution (transfer) to a pot."""

    transaction_id: UUID
    amount: int  # Positive value in pence
    date: date
    description: str | None


@dataclass
class SinkingFundPotStatus:
    """Combined sinking fund status with pot balance and contributions."""

    budget_id: UUID
    budget_name: str | None
    category: str
    pot_id: str | None
    pot_name: str | None
    pot_balance: int | None
    target_amount: int
    monthly_contribution: int
    contributions_this_period: int
    expected_contributions: int
    variance: int
    on_track: bool
    target_month: int | None
    months_remaining: int
    projected_balance: int
    contribution_history: list[PotContribution]


class PotService:
    """Service for managing pots and pot-backed sinking funds."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session

    async def get_all_pots(self, account_id: str | UUID) -> list[Pot]:
        """Get all pots for an account.

        Args:
            account_id: Account ID to filter pots

        Returns:
            List of pots (including deleted for history)
        """
        result = await self._session.execute(
            select(Pot)
            .where(Pot.account_id == account_id)
            .order_by(Pot.name)
        )
        return list(result.scalars().all())

    async def get_active_pots(self, account_id: str | UUID) -> list[Pot]:
        """Get only active (non-deleted) pots for an account.

        Args:
            account_id: Account ID to filter pots

        Returns:
            List of active pots
        """
        result = await self._session.execute(
            select(Pot)
            .where(
                and_(
                    Pot.account_id == account_id,
                    Pot.deleted.is_(False),
                )
            )
            .order_by(Pot.name)
        )
        return list(result.scalars().all())

    async def get_pot_by_monzo_id(self, monzo_id: str) -> Pot | None:
        """Get a pot by its Monzo ID.

        Args:
            monzo_id: Monzo pot ID (e.g., "pot_xxx")

        Returns:
            Pot or None if not found
        """
        result = await self._session.execute(
            select(Pot).where(Pot.monzo_id == monzo_id)
        )
        return result.scalar_one_or_none()

    async def get_pot_balance(self, monzo_pot_id: str) -> PotBalance | None:
        """Get the current balance of a pot.

        Args:
            monzo_pot_id: Monzo pot ID

        Returns:
            PotBalance or None if pot not found
        """
        pot = await self.get_pot_by_monzo_id(monzo_pot_id)
        if not pot:
            return None

        return PotBalance(
            pot_id=pot.id,
            monzo_id=pot.monzo_id,
            name=pot.name,
            balance=pot.balance,
            deleted=pot.deleted,
            updated_at=pot.updated_at,
        )

    async def get_pot_contributions(
        self,
        account_id: str | UUID,
        pot_monzo_id: str,
        since: date | None = None,
        until: date | None = None,
    ) -> list[PotContribution]:
        """Get contributions (transfers) to a pot.

        Pot transfers in Monzo have metadata.pot_id set to the destination pot.
        Positive amounts going to the pot are contributions.

        Args:
            account_id: Account ID
            pot_monzo_id: Monzo pot ID to get contributions for
            since: Start date filter (inclusive)
            until: End date filter (inclusive)

        Returns:
            List of contributions to the pot
        """
        # Query transactions that are pot transfers
        # Pot transfers have scheme: "pot" in the metadata or
        # counterparty info indicating pot transfer
        query = select(Transaction).where(
            Transaction.account_id == account_id
        )

        result = await self._session.execute(query)
        transactions = result.scalars().all()

        contributions = []
        for tx in transactions:
            # Check if this is a pot transfer to the target pot
            if not tx.raw_payload:
                continue

            metadata = tx.raw_payload.get("metadata", {})
            pot_id = metadata.get("pot_id")

            # Check if this transfer is TO the pot (positive contribution)
            # Monzo shows pot deposits as negative from main account perspective
            if pot_id == pot_monzo_id and tx.amount < 0:
                tx_date = tx.settled_at.date() if tx.settled_at else tx.created_at.date()

                # Apply date filters
                if since and tx_date < since:
                    continue
                if until and tx_date > until:
                    continue

                contributions.append(
                    PotContribution(
                        transaction_id=tx.id,
                        amount=abs(tx.amount),  # Convert to positive
                        date=tx_date,
                        description=tx.raw_payload.get("description"),
                    )
                )

        # Sort by date descending (most recent first)
        contributions.sort(key=lambda c: c.date, reverse=True)
        return contributions

    async def get_sinking_fund_pot_status(
        self,
        budget: Budget,
        reference_date: date,
    ) -> SinkingFundPotStatus | None:
        """Get comprehensive sinking fund status with pot integration.

        Combines budget targets with actual pot balance and contribution history.

        Args:
            budget: Budget (must be a sinking fund with linked_pot_id)
            reference_date: Reference date for calculations

        Returns:
            SinkingFundPotStatus or None if not a pot-backed sinking fund
        """
        if not budget.is_sinking_fund:
            return None

        # Get pot balance if linked
        pot_balance_info = None
        pot_balance = None
        pot_name = None
        if budget.linked_pot_id:
            pot_balance_info = await self.get_pot_balance(budget.linked_pot_id)
            if pot_balance_info:
                pot_balance = pot_balance_info.balance
                pot_name = pot_balance_info.name

        # Calculate contribution period
        target_month = budget.target_month or 12
        months_elapsed, months_remaining = calculate_sinking_fund_months(
            target_month, reference_date
        )

        # Build period_start for querying contribution history
        if reference_date.month >= target_month:
            period_start = date(reference_date.year, target_month, 1)
        else:
            period_start = date(reference_date.year - 1, target_month, 1)

        # Get contribution history for this period
        contributions = []
        if budget.linked_pot_id:
            contributions = await self.get_pot_contributions(
                account_id=budget.account_id,
                pot_monzo_id=budget.linked_pot_id,
                since=period_start,
                until=reference_date,
            )

        contributions_this_period = sum(c.amount for c in contributions)

        # Expected contributions to date
        monthly_contribution = budget.monthly_contribution
        expected_contributions = monthly_contribution * months_elapsed

        # Use pot balance if available, otherwise use tracked contributions
        actual_balance = pot_balance if pot_balance is not None else contributions_this_period

        # Variance
        variance = actual_balance - expected_contributions
        on_track = actual_balance >= expected_contributions

        # Projected balance at target
        if months_remaining > 0 and months_elapsed > 0:
            monthly_rate = actual_balance / months_elapsed
            projected_balance = actual_balance + int(monthly_rate * months_remaining)
        else:
            projected_balance = actual_balance

        return SinkingFundPotStatus(
            budget_id=budget.id,
            budget_name=budget.name,
            category=budget.category,
            pot_id=budget.linked_pot_id,
            pot_name=pot_name,
            pot_balance=pot_balance,
            target_amount=budget.annual_amount or 0,
            monthly_contribution=monthly_contribution,
            contributions_this_period=contributions_this_period,
            expected_contributions=expected_contributions,
            variance=variance,
            on_track=on_track,
            target_month=target_month,
            months_remaining=months_remaining,
            projected_balance=projected_balance,
            contribution_history=contributions,
        )

    async def get_unlinked_pots(self, account_id: str | UUID) -> list[Pot]:
        """Get pots that are not linked to any budget.

        Useful for showing "Unbudgeted Pots" section.

        Args:
            account_id: Account ID

        Returns:
            List of pots not linked to any budget
        """
        # Get all active pots
        pots = await self.get_active_pots(account_id)

        # Get all budgets with linked pots
        result = await self._session.execute(
            select(Budget.linked_pot_id)
            .where(
                and_(
                    Budget.account_id == account_id,
                    Budget.linked_pot_id.isnot(None),
                )
            )
        )
        linked_pot_ids = {row[0] for row in result.all()}

        # Filter to unlinked pots
        return [pot for pot in pots if pot.monzo_id not in linked_pot_ids]

    async def get_pot_summary(self, account_id: str | UUID) -> dict[str, Any]:
        """Get summary of all pots for an account.

        Args:
            account_id: Account ID

        Returns:
            Summary with total balance, pot count, linked vs unlinked
        """
        all_pots = await self.get_active_pots(account_id)
        unlinked = await self.get_unlinked_pots(account_id)

        total_balance = sum(pot.balance for pot in all_pots)
        linked_balance = sum(
            pot.balance for pot in all_pots if pot not in unlinked
        )
        unlinked_balance = sum(pot.balance for pot in unlinked)

        return {
            "total_pots": len(all_pots),
            "linked_pots": len(all_pots) - len(unlinked),
            "unlinked_pots": len(unlinked),
            "total_balance": total_balance,
            "linked_balance": linked_balance,
            "unlinked_balance": unlinked_balance,
            "unlinked_pot_list": [
                {
                    "id": str(pot.id),
                    "monzo_id": pot.monzo_id,
                    "name": pot.name,
                    "balance": pot.balance,
                }
                for pot in unlinked
            ],
        }
