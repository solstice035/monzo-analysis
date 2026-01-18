"""Tests for transaction sync service."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestMonzoDataFetching:
    """Tests for fetching data from Monzo API."""

    @pytest.mark.asyncio
    async def test_fetch_accounts_returns_account_list(self) -> None:
        """Fetch accounts should return list of accounts."""
        from app.services.monzo import fetch_accounts

        mock_response_data = {
            "accounts": [
                {"id": "acc_123", "type": "uk_retail", "description": "Personal"},
                {"id": "acc_456", "type": "uk_retail_joint", "description": "Joint"},
            ]
        }

        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch("httpx.AsyncClient") as MockAsyncClient:
            MockAsyncClient.return_value.__aenter__.return_value = mock_client
            MockAsyncClient.return_value.__aexit__.return_value = None

            result = await fetch_accounts("test_access_token")

            assert len(result) == 2
            assert result[0]["id"] == "acc_123"
            assert result[1]["type"] == "uk_retail_joint"

    @pytest.mark.asyncio
    async def test_fetch_transactions_returns_transaction_list(self) -> None:
        """Fetch transactions should return paginated transactions."""
        from app.services.monzo import fetch_transactions

        mock_response_data = {
            "transactions": [
                {
                    "id": "tx_123",
                    "amount": -1500,
                    "merchant": {"name": "Tesco"},
                    "category": "groceries",
                    "created": "2025-01-18T10:00:00Z",
                },
            ]
        }

        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch("httpx.AsyncClient") as MockAsyncClient:
            MockAsyncClient.return_value.__aenter__.return_value = mock_client
            MockAsyncClient.return_value.__aexit__.return_value = None

            result = await fetch_transactions("test_token", "acc_123")

            assert len(result) == 1
            assert result[0]["id"] == "tx_123"
            assert result[0]["amount"] == -1500

    @pytest.mark.asyncio
    async def test_fetch_transactions_with_since_param(self) -> None:
        """Fetch transactions should support since parameter for incremental sync."""
        from app.services.monzo import fetch_transactions

        mock_response = MagicMock()
        mock_response.json.return_value = {"transactions": []}
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch("httpx.AsyncClient") as MockAsyncClient:
            MockAsyncClient.return_value.__aenter__.return_value = mock_client
            MockAsyncClient.return_value.__aexit__.return_value = None

            since = datetime(2025, 1, 1, tzinfo=timezone.utc)
            await fetch_transactions("test_token", "acc_123", since=since)

            # Verify since parameter was included in request
            call_args = mock_client.get.call_args
            assert "since" in call_args.kwargs.get("params", {})

    @pytest.mark.asyncio
    async def test_fetch_pots_returns_pot_list(self) -> None:
        """Fetch pots should return list of savings pots."""
        from app.services.monzo import fetch_pots

        mock_response_data = {
            "pots": [
                {"id": "pot_123", "name": "Holiday", "balance": 50000, "deleted": False},
                {"id": "pot_456", "name": "Emergency", "balance": 100000, "deleted": False},
            ]
        }

        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch("httpx.AsyncClient") as MockAsyncClient:
            MockAsyncClient.return_value.__aenter__.return_value = mock_client
            MockAsyncClient.return_value.__aexit__.return_value = None

            result = await fetch_pots("test_token", "acc_123")

            assert len(result) == 2
            assert result[0]["name"] == "Holiday"
            assert result[0]["balance"] == 50000

    @pytest.mark.asyncio
    async def test_fetch_balance_returns_balance_info(self) -> None:
        """Fetch balance should return current balance."""
        from app.services.monzo import fetch_balance

        mock_response_data = {
            "balance": 150000,
            "total_balance": 200000,
            "currency": "GBP",
            "spend_today": -2500,
        }

        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch("httpx.AsyncClient") as MockAsyncClient:
            MockAsyncClient.return_value.__aenter__.return_value = mock_client
            MockAsyncClient.return_value.__aexit__.return_value = None

            result = await fetch_balance("test_token", "acc_123")

            assert result["balance"] == 150000
            assert result["spend_today"] == -2500


class TestSyncService:
    """Tests for the sync orchestration service."""

    @pytest.mark.asyncio
    async def test_sync_creates_sync_log(self) -> None:
        """Sync should create a sync log entry."""
        from app.services.sync import SyncService

        service = SyncService()

        with patch.object(service, "_get_auth", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = MagicMock(access_token="test_token")

            with patch.object(service, "_sync_accounts", new_callable=AsyncMock):
                with patch.object(service, "_sync_transactions", new_callable=AsyncMock) as mock_sync_tx:
                    mock_sync_tx.return_value = 5

                    with patch.object(service, "_create_sync_log", new_callable=AsyncMock) as mock_log:
                        with patch.object(service, "_update_sync_log", new_callable=AsyncMock):
                            await service.run_sync()

                            mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_updates_log_on_completion(self) -> None:
        """Sync should update log with transaction count on success."""
        from app.services.sync import SyncService

        service = SyncService()

        with patch.object(service, "_get_auth", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = MagicMock(access_token="test_token")

            with patch.object(service, "_sync_accounts", new_callable=AsyncMock):
                with patch.object(service, "_sync_transactions", new_callable=AsyncMock) as mock_sync_tx:
                    mock_sync_tx.return_value = 10

                    with patch.object(service, "_create_sync_log", new_callable=AsyncMock) as mock_create:
                        mock_create.return_value = MagicMock(id="log_123")

                        with patch.object(service, "_update_sync_log", new_callable=AsyncMock) as mock_update:
                            await service.run_sync()

                            # Verify update was called with success status
                            mock_update.assert_called()
                            call_args = mock_update.call_args
                            assert call_args.kwargs.get("status") == "success"
                            assert call_args.kwargs.get("transactions_synced") == 10

    @pytest.mark.asyncio
    async def test_sync_handles_no_auth(self) -> None:
        """Sync should raise error when not authenticated."""
        from app.services.sync import SyncService, SyncError

        service = SyncService()

        with patch.object(service, "_get_auth", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = None

            with pytest.raises(SyncError, match="Not authenticated"):
                await service.run_sync()

    @pytest.mark.asyncio
    async def test_sync_updates_log_on_error(self) -> None:
        """Sync should update log with error on failure."""
        from app.services.sync import SyncService

        service = SyncService()

        with patch.object(service, "_get_auth", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = MagicMock(access_token="test_token")

            with patch.object(service, "_sync_accounts", new_callable=AsyncMock) as mock_sync_acc:
                mock_sync_acc.side_effect = Exception("API Error")

                with patch.object(service, "_create_sync_log", new_callable=AsyncMock) as mock_create:
                    mock_create.return_value = MagicMock(id="log_123")

                    with patch.object(service, "_update_sync_log", new_callable=AsyncMock) as mock_update:
                        try:
                            await service.run_sync()
                        except Exception:
                            pass

                        # Verify update was called with failed status
                        mock_update.assert_called()
                        call_args = mock_update.call_args
                        assert call_args.kwargs.get("status") == "failed"


class TestTransactionUpsert:
    """Tests for transaction upsert logic."""

    @pytest.mark.asyncio
    async def test_upsert_creates_new_transaction(self) -> None:
        """Upsert should create new transaction if not exists."""
        from app.services.sync import upsert_transaction

        tx_data = {
            "id": "tx_new_123",
            "amount": -1500,
            "merchant": {"name": "Tesco"},
            "category": "groceries",
            "created": "2025-01-18T10:00:00Z",
        }

        # Properly mock async session with result object
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        account_id = "acc_123"
        result = await upsert_transaction(mock_session, account_id, tx_data)

        assert result is True  # New transaction created
        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_updates_existing_transaction(self) -> None:
        """Upsert should update existing transaction."""
        from app.models import Transaction
        from app.services.sync import upsert_transaction

        tx_data = {
            "id": "tx_existing_123",
            "amount": -1500,
            "merchant": {"name": "Tesco"},
            "category": "groceries",
            "created": "2025-01-18T10:00:00Z",
            "settled": "2025-01-18T12:00:00Z",
        }

        # Mock existing transaction
        existing_tx = MagicMock(spec=Transaction)
        existing_tx.settled_at = None

        # Properly mock async session with result object
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_tx

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        account_id = "acc_123"
        result = await upsert_transaction(mock_session, account_id, tx_data)

        assert result is False  # Existing transaction updated
        # Verify settled_at was updated
        assert existing_tx.settled_at is not None
