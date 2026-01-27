"""Tests for pot service."""

from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.pot import (
    PotBalance,
    PotContribution,
    PotService,
    SinkingFundPotStatus,
)


class TestPotService:
    """Tests for PotService."""

    @pytest.mark.asyncio
    async def test_get_pot_by_monzo_id_returns_pot(self) -> None:
        """Should return pot when found by Monzo ID."""
        mock_pot = MagicMock()
        mock_pot.configure_mock(
            id=uuid4(),
            monzo_id="pot_abc123",
            balance=50000,
            deleted=False,
            updated_at=datetime.now(timezone.utc),
        )
        mock_pot.name = "Holiday Fund"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_pot

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        service = PotService(mock_session)
        result = await service.get_pot_by_monzo_id("pot_abc123")

        assert result == mock_pot
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_pot_by_monzo_id_returns_none_when_not_found(self) -> None:
        """Should return None when pot not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        service = PotService(mock_session)
        result = await service.get_pot_by_monzo_id("pot_nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_pot_balance_returns_balance_info(self) -> None:
        """Should return PotBalance dataclass with pot info."""
        pot_id = uuid4()
        updated = datetime.now(timezone.utc)
        # Use configure_mock to set 'name' since it's a special MagicMock parameter
        mock_pot = MagicMock()
        mock_pot.configure_mock(
            id=pot_id,
            monzo_id="pot_xyz789",
            balance=100000,
            deleted=False,
            updated_at=updated,
        )
        mock_pot.name = "Emergency Fund"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_pot

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        service = PotService(mock_session)
        result = await service.get_pot_balance("pot_xyz789")

        assert result is not None
        assert isinstance(result, PotBalance)
        assert result.pot_id == pot_id
        assert result.monzo_id == "pot_xyz789"
        assert result.name == "Emergency Fund"
        assert result.balance == 100000
        assert result.deleted is False

    @pytest.mark.asyncio
    async def test_get_pot_balance_returns_none_when_not_found(self) -> None:
        """Should return None when pot not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        service = PotService(mock_session)
        result = await service.get_pot_balance("pot_missing")

        assert result is None


class TestPotContributions:
    """Tests for pot contribution tracking."""

    @pytest.mark.asyncio
    async def test_get_pot_contributions_identifies_pot_transfers(self) -> None:
        """Should identify transfers to pot from transaction metadata."""
        account_id = uuid4()
        tx_id = uuid4()
        tx_date = datetime(2026, 1, 15, 10, 0, tzinfo=timezone.utc)

        mock_tx = MagicMock(
            id=tx_id,
            account_id=account_id,
            amount=-5000,  # Negative = transfer out of main account
            settled_at=tx_date,
            created_at=tx_date,
            raw_payload={
                "metadata": {"pot_id": "pot_savings123"},
                "description": "Monthly savings",
            },
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_tx]

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        service = PotService(mock_session)
        contributions = await service.get_pot_contributions(
            account_id=account_id,
            pot_monzo_id="pot_savings123",
        )

        assert len(contributions) == 1
        assert contributions[0].transaction_id == tx_id
        assert contributions[0].amount == 5000  # Converted to positive
        assert contributions[0].date == date(2026, 1, 15)
        assert contributions[0].description == "Monthly savings"

    @pytest.mark.asyncio
    async def test_get_pot_contributions_filters_by_date(self) -> None:
        """Should filter contributions by date range."""
        account_id = uuid4()

        # Transaction in range
        tx_in_range = MagicMock(
            id=uuid4(),
            account_id=account_id,
            amount=-5000,
            settled_at=datetime(2026, 1, 15, tzinfo=timezone.utc),
            created_at=datetime(2026, 1, 15, tzinfo=timezone.utc),
            raw_payload={"metadata": {"pot_id": "pot_test"}, "description": "In range"},
        )

        # Transaction before range
        tx_before = MagicMock(
            id=uuid4(),
            account_id=account_id,
            amount=-3000,
            settled_at=datetime(2025, 12, 1, tzinfo=timezone.utc),
            created_at=datetime(2025, 12, 1, tzinfo=timezone.utc),
            raw_payload={"metadata": {"pot_id": "pot_test"}, "description": "Before"},
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [tx_in_range, tx_before]

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        service = PotService(mock_session)
        contributions = await service.get_pot_contributions(
            account_id=account_id,
            pot_monzo_id="pot_test",
            since=date(2026, 1, 1),
            until=date(2026, 1, 31),
        )

        assert len(contributions) == 1
        assert contributions[0].description == "In range"

    @pytest.mark.asyncio
    async def test_get_pot_contributions_excludes_other_pots(self) -> None:
        """Should only include contributions to the specified pot."""
        account_id = uuid4()

        # Transfer to target pot
        tx_target = MagicMock(
            id=uuid4(),
            account_id=account_id,
            amount=-5000,
            settled_at=datetime(2026, 1, 15, tzinfo=timezone.utc),
            created_at=datetime(2026, 1, 15, tzinfo=timezone.utc),
            raw_payload={"metadata": {"pot_id": "pot_target"}, "description": "Target"},
        )

        # Transfer to different pot
        tx_other = MagicMock(
            id=uuid4(),
            account_id=account_id,
            amount=-3000,
            settled_at=datetime(2026, 1, 15, tzinfo=timezone.utc),
            created_at=datetime(2026, 1, 15, tzinfo=timezone.utc),
            raw_payload={"metadata": {"pot_id": "pot_other"}, "description": "Other"},
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [tx_target, tx_other]

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        service = PotService(mock_session)
        contributions = await service.get_pot_contributions(
            account_id=account_id,
            pot_monzo_id="pot_target",
        )

        assert len(contributions) == 1
        assert contributions[0].description == "Target"


class TestSinkingFundPotStatus:
    """Tests for sinking fund pot status calculations."""

    @pytest.mark.asyncio
    async def test_get_sinking_fund_pot_status_on_track(self) -> None:
        """Should calculate status for on-track sinking fund."""
        budget_id = uuid4()
        account_id = uuid4()

        # Use configure_mock for 'name' since it's a special MagicMock parameter
        mock_budget = MagicMock()
        mock_budget.configure_mock(
            id=budget_id,
            account_id=account_id,
            category="car",
            is_sinking_fund=True,
            period_type="annual",
            annual_amount=67500,  # £675
            monthly_contribution=5625,  # £56.25/month
            target_month=10,  # October
            linked_pot_id="pot_car_tax",
        )
        mock_budget.name = "Car Tax"

        # Pot has expected balance for 4 months (Oct, Nov, Dec, Jan)
        mock_pot = MagicMock()
        mock_pot.configure_mock(
            id=uuid4(),
            monzo_id="pot_car_tax",
            balance=22500,  # 4 months x £56.25 = £225
            deleted=False,
            updated_at=datetime.now(timezone.utc),
        )
        mock_pot.name = "Car Tax"

        def mock_execute(query):
            result = MagicMock()
            # First call gets pot, second gets transactions
            if "pots" in str(query):
                result.scalar_one_or_none.return_value = mock_pot
            else:
                result.scalars.return_value.all.return_value = []
            return result

        mock_session = AsyncMock()
        mock_session.execute.side_effect = mock_execute

        service = PotService(mock_session)
        status = await service.get_sinking_fund_pot_status(
            budget=mock_budget,
            reference_date=date(2026, 1, 15),  # 3 months since October
        )

        assert status is not None
        assert isinstance(status, SinkingFundPotStatus)
        assert status.budget_id == budget_id
        assert status.pot_balance == 22500
        assert status.on_track is True

    @pytest.mark.asyncio
    async def test_get_sinking_fund_pot_status_returns_none_for_regular_budget(
        self,
    ) -> None:
        """Should return None for non-sinking-fund budgets."""
        mock_budget = MagicMock(
            is_sinking_fund=False,
            period_type="monthly",
        )

        mock_session = AsyncMock()
        service = PotService(mock_session)

        status = await service.get_sinking_fund_pot_status(
            budget=mock_budget,
            reference_date=date(2026, 1, 15),
        )

        assert status is None

    @pytest.mark.asyncio
    async def test_get_sinking_fund_pot_status_without_linked_pot(self) -> None:
        """Should handle sinking fund without linked pot."""
        budget_id = uuid4()
        account_id = uuid4()

        mock_budget = MagicMock(
            id=budget_id,
            account_id=account_id,
            name="Insurance",
            category="insurance",
            is_sinking_fund=True,
            period_type="annual",
            annual_amount=120000,  # £1200
            monthly_contribution=10000,  # £100/month
            target_month=6,  # June
            linked_pot_id=None,  # No linked pot
        )

        mock_session = AsyncMock()
        service = PotService(mock_session)

        status = await service.get_sinking_fund_pot_status(
            budget=mock_budget,
            reference_date=date(2026, 1, 15),
        )

        assert status is not None
        assert status.pot_id is None
        assert status.pot_balance is None
        assert status.pot_name is None


class TestUnlinkedPots:
    """Tests for unlinked pot management."""

    @pytest.mark.asyncio
    async def test_get_unlinked_pots_excludes_linked(self) -> None:
        """Should return only pots not linked to any budget."""
        account_id = uuid4()

        pot_linked = MagicMock()
        pot_linked.configure_mock(
            id=uuid4(),
            monzo_id="pot_linked",
            account_id=account_id,
            balance=10000,
            deleted=False,
        )
        pot_linked.name = "Linked Pot"

        pot_unlinked = MagicMock()
        pot_unlinked.configure_mock(
            id=uuid4(),
            monzo_id="pot_unlinked",
            account_id=account_id,
            balance=5000,
            deleted=False,
        )
        pot_unlinked.name = "Unlinked Pot"

        call_count = 0

        def mock_execute(query):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                # First call: get active pots
                result.scalars.return_value.all.return_value = [pot_linked, pot_unlinked]
            else:
                # Second call: get linked pot IDs
                result.all.return_value = [("pot_linked",)]
            return result

        mock_session = AsyncMock()
        mock_session.execute.side_effect = mock_execute

        service = PotService(mock_session)
        unlinked = await service.get_unlinked_pots(account_id)

        assert len(unlinked) == 1
        assert unlinked[0].monzo_id == "pot_unlinked"

    @pytest.mark.asyncio
    async def test_get_pot_summary_calculates_totals(self) -> None:
        """Should calculate summary totals correctly."""
        account_id = uuid4()

        pot1 = MagicMock()
        pot1.configure_mock(
            id=uuid4(),
            monzo_id="pot_1",
            account_id=account_id,
            balance=10000,
            deleted=False,
        )
        pot1.name = "Pot 1"

        pot2 = MagicMock()
        pot2.configure_mock(
            id=uuid4(),
            monzo_id="pot_2",
            account_id=account_id,
            balance=20000,
            deleted=False,
        )
        pot2.name = "Pot 2"

        call_count = 0

        def mock_execute(query):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count <= 2:
                # Active pots calls
                result.scalars.return_value.all.return_value = [pot1, pot2]
            else:
                # Linked pot IDs - pot_1 is linked
                result.all.return_value = [("pot_1",)]
            return result

        mock_session = AsyncMock()
        mock_session.execute.side_effect = mock_execute

        service = PotService(mock_session)
        summary = await service.get_pot_summary(account_id)

        assert summary["total_pots"] == 2
        assert summary["linked_pots"] == 1
        assert summary["unlinked_pots"] == 1
        assert summary["total_balance"] == 30000
        assert len(summary["unlinked_pot_list"]) == 1
