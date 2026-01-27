"""Budget group service for hierarchical budget management."""

from dataclasses import dataclass
from datetime import date
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Budget, BudgetGroup
from app.services.budget import BudgetService, BudgetStatus


@dataclass
class BudgetGroupStatus:
    """Aggregated status of a budget group with roll-up totals."""

    group_id: UUID
    name: str
    icon: str | None
    display_order: int
    total_amount: int
    total_spent: int
    total_remaining: int
    percentage: float
    status: str  # "under", "warning", "over"
    budget_count: int
    budgets: list[BudgetStatus]
    period_start: date
    period_end: date


class BudgetGroupService:
    """Service for managing budget groups and roll-up calculations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session
        self._budget_service = BudgetService(session)

    async def get_all_groups(self, account_id: str | UUID) -> list[BudgetGroup]:
        """Get all budget groups for an account.

        Args:
            account_id: Account ID to filter groups

        Returns:
            List of budget groups ordered by display_order
        """
        result = await self._session.execute(
            select(BudgetGroup)
            .where(BudgetGroup.account_id == account_id)
            .options(selectinload(BudgetGroup.budgets))
            .order_by(BudgetGroup.display_order)
        )
        return list(result.scalars().all())

    async def get_group(self, group_id: str | UUID) -> BudgetGroup | None:
        """Get a single budget group by ID.

        Args:
            group_id: Group ID to fetch

        Returns:
            BudgetGroup or None if not found
        """
        result = await self._session.execute(
            select(BudgetGroup)
            .where(BudgetGroup.id == group_id)
            .options(selectinload(BudgetGroup.budgets))
        )
        return result.scalar_one_or_none()

    async def create_group(
        self,
        account_id: str | UUID,
        name: str,
        icon: str | None = None,
        display_order: int = 0,
    ) -> BudgetGroup:
        """Create a new budget group.

        Args:
            account_id: Account ID to associate the group with
            name: Group name (e.g., "Kids", "Fixed Bills")
            icon: Optional emoji icon
            display_order: Display order (lower = first)

        Returns:
            Created budget group
        """
        group = BudgetGroup(
            id=uuid4(),
            account_id=account_id,
            name=name,
            icon=icon,
            display_order=display_order,
        )
        self._session.add(group)
        return group

    async def update_group(
        self,
        group_id: str | UUID,
        name: str | None = None,
        icon: str | None = None,
        display_order: int | None = None,
    ) -> BudgetGroup | None:
        """Update an existing budget group.

        Args:
            group_id: ID of group to update
            name: New name (optional)
            icon: New icon (optional)
            display_order: New display order (optional)

        Returns:
            Updated group or None if not found
        """
        group = await self.get_group(group_id)
        if not group:
            return None

        if name is not None:
            group.name = name
        if icon is not None:
            group.icon = icon
        if display_order is not None:
            group.display_order = display_order

        return group

    async def delete_group(self, group_id: str | UUID) -> bool:
        """Delete a budget group and all its budgets.

        Args:
            group_id: ID of group to delete

        Returns:
            True if deleted, False if not found
        """
        group = await self.get_group(group_id)
        if not group:
            return False

        await self._session.delete(group)
        return True

    async def get_group_status(
        self,
        group: BudgetGroup,
        reference_date: date,
    ) -> BudgetGroupStatus:
        """Get the aggregated status of a budget group.

        Calculates roll-up totals from all child budgets.

        Args:
            group: Budget group to check
            reference_date: Reference date for period calculation

        Returns:
            BudgetGroupStatus with aggregated spend details
        """
        budget_statuses: list[BudgetStatus] = []

        # Get status for each budget in the group
        for budget in group.budgets:
            status = await self._budget_service.get_budget_status(
                budget, reference_date
            )
            budget_statuses.append(status)

        # Aggregate totals
        total_amount = sum(s.amount for s in budget_statuses)
        total_spent = sum(s.spent for s in budget_statuses)
        total_remaining = total_amount - total_spent
        percentage = (total_spent / total_amount) * 100 if total_amount > 0 else 0

        # Determine group status based on aggregated percentage
        if percentage >= 100:
            status = "over"
        elif percentage >= 80:
            status = "warning"
        else:
            status = "under"

        # Period: use the earliest start and latest end from all budgets
        period_start = min(s.period_start for s in budget_statuses) if budget_statuses else reference_date
        period_end = max(s.period_end for s in budget_statuses) if budget_statuses else reference_date

        return BudgetGroupStatus(
            group_id=group.id,
            name=group.name,
            icon=group.icon,
            display_order=group.display_order,
            total_amount=total_amount,
            total_spent=total_spent,
            total_remaining=total_remaining,
            percentage=round(percentage, 2),
            status=status,
            budget_count=len(budget_statuses),
            budgets=budget_statuses,
            period_start=period_start,
            period_end=period_end,
        )

    async def get_all_group_statuses(
        self,
        account_id: str | UUID,
        reference_date: date,
    ) -> list[BudgetGroupStatus]:
        """Get status for all budget groups for an account.

        Args:
            account_id: Account ID to filter groups
            reference_date: Reference date for period calculation

        Returns:
            List of BudgetGroupStatus for all groups
        """
        groups = await self.get_all_groups(account_id)
        statuses = []

        for group in groups:
            status = await self.get_group_status(group, reference_date)
            statuses.append(status)

        return statuses

    async def get_dashboard_summary(
        self,
        account_id: str | UUID,
        reference_date: date,
    ) -> dict[str, Any]:
        """Get dashboard summary with all group statuses and totals.

        Args:
            account_id: Account ID
            reference_date: Reference date for calculations

        Returns:
            Dictionary with dashboard data
        """
        group_statuses = await self.get_all_group_statuses(account_id, reference_date)

        total_budget = sum(g.total_amount for g in group_statuses)
        total_spent = sum(g.total_spent for g in group_statuses)
        total_remaining = total_budget - total_spent
        overall_percentage = (total_spent / total_budget) * 100 if total_budget > 0 else 0

        if overall_percentage >= 100:
            overall_status = "over"
        elif overall_percentage >= 80:
            overall_status = "warning"
        else:
            overall_status = "under"

        # Period progress
        if group_statuses:
            period_start = min(g.period_start for g in group_statuses)
            period_end = max(g.period_end for g in group_statuses)
            days_in_period = (period_end - period_start).days + 1
            days_elapsed = (reference_date - period_start).days + 1
        else:
            period_start = reference_date
            period_end = reference_date
            days_in_period = 1
            days_elapsed = 1

        return {
            "groups": group_statuses,
            "total_budget": total_budget,
            "total_spent": total_spent,
            "total_remaining": total_remaining,
            "overall_percentage": round(overall_percentage, 2),
            "overall_status": overall_status,
            "period_start": period_start,
            "period_end": period_end,
            "days_in_period": days_in_period,
            "days_elapsed": days_elapsed,
        }

    async def ensure_miscellaneous_group(
        self,
        account_id: str | UUID,
    ) -> BudgetGroup:
        """Ensure a 'Miscellaneous' group exists for orphaned budgets.

        Used during migration to assign existing budgets without groups.

        Args:
            account_id: Account ID

        Returns:
            The Miscellaneous group (created if needed)
        """
        result = await self._session.execute(
            select(BudgetGroup).where(
                and_(
                    BudgetGroup.account_id == account_id,
                    BudgetGroup.name == "Miscellaneous",
                )
            )
        )
        group = result.scalar_one_or_none()

        if not group:
            group = await self.create_group(
                account_id=account_id,
                name="Miscellaneous",
                icon="📦",
                display_order=999,  # Show last
            )

        return group

    async def migrate_orphaned_budgets(
        self,
        account_id: str | UUID,
    ) -> int:
        """Assign budgets without groups to the Miscellaneous group.

        Args:
            account_id: Account ID

        Returns:
            Number of budgets migrated
        """
        misc_group = await self.ensure_miscellaneous_group(account_id)

        # Find orphaned budgets (no group_id)
        result = await self._session.execute(
            select(Budget).where(
                and_(
                    Budget.account_id == account_id,
                    Budget.group_id.is_(None),
                )
            )
        )
        orphaned = list(result.scalars().all())

        for budget in orphaned:
            budget.group_id = misc_group.id
            # Use category as name if name is not set
            if not budget.name:
                budget.name = budget.category.replace("_", " ").title()

        return len(orphaned)
