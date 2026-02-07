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
    async def test_fetch_transactions_paginates(self) -> None:
        """Fetch transactions should paginate when a full page is returned."""
        from app.services.monzo import fetch_transactions

        # Page 1: full page of 3 (limit=3), page 2: partial page of 1
        page1 = [
            {"id": f"tx_{i}", "amount": -100, "created": "2025-01-18T10:00:00Z"}
            for i in range(3)
        ]
        page2 = [
            {"id": "tx_3", "amount": -100, "created": "2025-01-18T11:00:00Z"}
        ]

        mock_response_1 = MagicMock()
        mock_response_1.json.return_value = {"transactions": page1}
        mock_response_1.raise_for_status = MagicMock()

        mock_response_2 = MagicMock()
        mock_response_2.json.return_value = {"transactions": page2}
        mock_response_2.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.side_effect = [mock_response_1, mock_response_2]

        with patch("httpx.AsyncClient") as MockAsyncClient:
            MockAsyncClient.return_value.__aenter__.return_value = mock_client
            MockAsyncClient.return_value.__aexit__.return_value = None

            result = await fetch_transactions("test_token", "acc_123", limit=3)

            assert len(result) == 4  # 3 + 1
            assert mock_client.get.call_count == 2

            # Second call should use last tx ID as cursor
            second_call_params = mock_client.get.call_args_list[1].kwargs["params"]
            assert second_call_params["since"] == "tx_2"

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


class TestApiTimeout:
    """Tests for API timeout configuration."""

    @pytest.mark.asyncio
    async def test_monzo_api_uses_timeout(self) -> None:
        """All Monzo API calls should use a 30-second timeout."""
        import httpx
        from app.services.monzo import API_TIMEOUT

        assert isinstance(API_TIMEOUT, httpx.Timeout)
        assert API_TIMEOUT.connect == 30.0

    @pytest.mark.asyncio
    async def test_fetch_accounts_passes_timeout(self) -> None:
        """fetch_accounts should create client with timeout."""
        from app.services.monzo import fetch_accounts

        mock_response = MagicMock()
        mock_response.json.return_value = {"accounts": []}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch("httpx.AsyncClient") as MockAsyncClient:
            MockAsyncClient.return_value.__aenter__.return_value = mock_client
            MockAsyncClient.return_value.__aexit__.return_value = None

            await fetch_accounts("test_token")

            # Verify timeout was passed to AsyncClient constructor
            call_kwargs = MockAsyncClient.call_args.kwargs
            assert "timeout" in call_kwargs


class TestSyncService:
    """Tests for the sync orchestration service."""

    @pytest.mark.asyncio
    async def test_sync_creates_sync_log(self) -> None:
        """Sync should create a sync log entry."""
        from app.services.sync import SyncService

        mock_session = AsyncMock()
        service = SyncService(mock_session)

        # Create mock auth with valid (non-expired) token
        mock_auth_obj = MagicMock(
            access_token="test_token",
            expires_at=datetime(2030, 1, 1, tzinfo=timezone.utc),
        )

        with patch.object(service, "_get_auth", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = mock_auth_obj

            with patch.object(service, "_sync_accounts", new_callable=AsyncMock) as mock_sync_acc:
                mock_sync_acc.return_value = [MagicMock(id="acc_123", monzo_id="acc_123")]

                with patch.object(service, "_sync_account_transactions", new_callable=AsyncMock) as mock_sync_tx:
                    mock_sync_tx.return_value = 5

                    with patch.object(service, "_sync_pots", new_callable=AsyncMock):
                        with patch.object(service, "_create_sync_log", new_callable=AsyncMock) as mock_log:
                            with patch.object(service, "_update_sync_log", new_callable=AsyncMock):
                                await service.run_sync()

                                mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_updates_log_on_completion(self) -> None:
        """Sync should update log with transaction count on success."""
        from app.services.sync import SyncService

        mock_session = AsyncMock()
        service = SyncService(mock_session)

        # Create mock auth with valid (non-expired) token
        mock_auth_obj = MagicMock(
            access_token="test_token",
            expires_at=datetime(2030, 1, 1, tzinfo=timezone.utc),
        )

        with patch.object(service, "_get_auth", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = mock_auth_obj

            with patch.object(service, "_sync_accounts", new_callable=AsyncMock) as mock_sync_acc:
                mock_sync_acc.return_value = [MagicMock(id="acc_123", monzo_id="acc_123")]

                with patch.object(service, "_sync_account_transactions", new_callable=AsyncMock) as mock_sync_tx:
                    mock_sync_tx.return_value = 10

                    with patch.object(service, "_sync_pots", new_callable=AsyncMock):
                        with patch.object(service, "_create_sync_log", new_callable=AsyncMock) as mock_create:
                            mock_create.return_value = MagicMock(id="log_123")

                            with patch.object(service, "_update_sync_log", new_callable=AsyncMock) as mock_update:
                                await service.run_sync()

                                # Verify update was called with success status
                                mock_update.assert_called()
                                call_args = mock_update.call_args
                                assert call_args.args[1] == "success"
                                assert call_args.args[2] == 10

    @pytest.mark.asyncio
    async def test_sync_handles_no_auth(self) -> None:
        """Sync should raise error when not authenticated."""
        from app.services.sync import SyncService, SyncError

        mock_session = AsyncMock()
        service = SyncService(mock_session)

        with patch.object(service, "_get_auth", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = None

            with pytest.raises(SyncError, match="Not authenticated"):
                await service.run_sync()

    @pytest.mark.asyncio
    async def test_sync_refreshes_expired_token(self) -> None:
        """Sync should refresh token when expired instead of raising error."""
        from app.services.sync import SyncService

        mock_session = AsyncMock()
        service = SyncService(mock_session)

        # Create mock auth with EXPIRED token
        mock_auth_obj = MagicMock(
            access_token="old_token",
            refresh_token="refresh_token_123",
            expires_at=datetime(2020, 1, 1, tzinfo=timezone.utc),  # expired
        )

        with patch.object(service, "_get_auth", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = mock_auth_obj

            with patch.object(service, "_refresh_token", new_callable=AsyncMock) as mock_refresh:
                refreshed_auth = MagicMock(
                    access_token="new_token",
                    expires_at=datetime(2030, 1, 1, tzinfo=timezone.utc),
                )
                mock_refresh.return_value = refreshed_auth

                with patch.object(service, "_sync_accounts", new_callable=AsyncMock) as mock_sync_acc:
                    mock_sync_acc.return_value = []

                    with patch.object(service, "_create_sync_log", new_callable=AsyncMock) as mock_log:
                        mock_log.return_value = MagicMock()
                        with patch.object(service, "_update_sync_log", new_callable=AsyncMock):
                            await service.run_sync()

                            # Verify refresh was called with the expired auth
                            mock_refresh.assert_called_once_with(mock_auth_obj)
                            # Verify sync used the refreshed token
                            mock_sync_acc.assert_called_once_with("new_token")

    @pytest.mark.asyncio
    async def test_sync_raises_on_refresh_failure(self) -> None:
        """Sync should raise SyncError when token refresh fails."""
        from app.services.sync import SyncService, SyncError

        mock_session = AsyncMock()
        service = SyncService(mock_session)

        mock_auth_obj = MagicMock(
            access_token="old_token",
            refresh_token="bad_refresh",
            expires_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
        )

        with patch.object(service, "_get_auth", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = mock_auth_obj

            with patch(
                "app.services.sync.refresh_access_token",
                new_callable=AsyncMock,
                side_effect=Exception("Invalid refresh token"),
            ):
                with pytest.raises(SyncError, match="Token refresh failed"):
                    await service.run_sync()

    @pytest.mark.asyncio
    async def test_refresh_token_updates_auth_record(self) -> None:
        """_refresh_token should update the auth record in the database."""
        from app.services.sync import SyncService

        mock_session = AsyncMock()
        service = SyncService(mock_session)

        mock_auth = MagicMock(
            access_token="old_token",
            refresh_token="old_refresh",
            expires_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
        )

        token_response = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600,
        }

        with patch(
            "app.services.sync.refresh_access_token",
            new_callable=AsyncMock,
            return_value=token_response,
        ):
            with patch("app.services.sync.calculate_token_expiry") as mock_expiry:
                mock_expiry.return_value = datetime(2030, 1, 1, tzinfo=timezone.utc)

                result = await service._refresh_token(mock_auth)

                assert result.access_token == "new_access_token"
                assert result.refresh_token == "new_refresh_token"
                mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_updates_log_on_error(self) -> None:
        """Sync should update log with error on failure."""
        from app.services.sync import SyncService

        mock_session = AsyncMock()
        service = SyncService(mock_session)

        # Create mock auth with valid (non-expired) token
        mock_auth_obj = MagicMock(
            access_token="test_token",
            expires_at=datetime(2030, 1, 1, tzinfo=timezone.utc),
        )

        with patch.object(service, "_get_auth", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = mock_auth_obj

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
                        assert call_args.args[1] == "failed"


class TestTransactionUpsert:
    """Tests for transaction upsert logic."""

    @pytest.mark.asyncio
    async def test_upsert_creates_new_transaction(self) -> None:
        """Upsert should create new transaction via ON CONFLICT DO NOTHING."""
        from app.services.sync import upsert_transaction

        tx_data = {
            "id": "tx_new_123",
            "amount": -1500,
            "merchant": {"name": "Tesco"},
            "category": "groceries",
            "created": "2025-01-18T10:00:00Z",
        }

        # Mock session.execute to return rowcount=1 (inserted)
        mock_result = MagicMock()
        mock_result.rowcount = 1

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        account_id = "acc_123"
        result = await upsert_transaction(mock_session, account_id, tx_data)

        assert result is True
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_updates_existing_transaction(self) -> None:
        """Upsert should update settled_at on existing transaction."""
        from app.services.sync import upsert_transaction

        tx_data = {
            "id": "tx_existing_123",
            "amount": -1500,
            "merchant": {"name": "Tesco"},
            "category": "groceries",
            "created": "2025-01-18T10:00:00Z",
            "settled": "2025-01-18T12:00:00Z",
        }

        # First execute (ON CONFLICT DO NOTHING) returns rowcount=0 (conflict)
        mock_insert_result = MagicMock()
        mock_insert_result.rowcount = 0

        # Second execute (UPDATE settled_at) returns rowcount=1
        mock_update_result = MagicMock()
        mock_update_result.rowcount = 1

        mock_session = AsyncMock()
        mock_session.execute.side_effect = [mock_insert_result, mock_update_result]

        account_id = "acc_123"
        result = await upsert_transaction(mock_session, account_id, tx_data)

        assert result is False  # Existing transaction
        assert mock_session.execute.call_count == 2  # INSERT + UPDATE

    @pytest.mark.asyncio
    async def test_upsert_handles_iso_datetime_with_z_suffix(self) -> None:
        """Upsert should handle ISO datetimes with Z suffix (Python 3.12+)."""
        from app.services.sync import upsert_transaction

        tx_data = {
            "id": "tx_z_test",
            "amount": -500,
            "merchant": None,
            "category": "general",
            "created": "2025-01-18T10:00:00Z",
            "settled": "2025-01-18T12:00:00Z",
        }

        mock_result = MagicMock()
        mock_result.rowcount = 1

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        # Should not raise — Python 3.12 handles Z natively
        result = await upsert_transaction(mock_session, "acc_123", tx_data)
        assert result is True


class TestSyncRulesIntegration:
    """Tests for rules engine integration with sync."""

    @pytest.mark.asyncio
    async def test_sync_applies_rules_to_new_transactions(self) -> None:
        """Sync should apply matching rules to new transactions."""
        from app.services.sync import SyncService

        mock_session = AsyncMock()
        service = SyncService(mock_session)

        mock_account = MagicMock(id="acc_123", monzo_id="monzo_acc_123")

        # Mock the latest transaction query (no existing transactions)
        mock_latest_result = MagicMock()
        mock_latest_result.scalar_one_or_none.return_value = None

        # Mock the rules query
        mock_rule = MagicMock()
        mock_rule.enabled = True
        mock_rule.priority = 50
        mock_rule.target_category = "Weekly Shop"
        mock_rule.conditions = {"merchant_pattern": "tesco"}

        mock_rules_result = MagicMock()
        mock_rules_result.scalars.return_value.all.return_value = [mock_rule]

        mock_session.execute.side_effect = [
            mock_latest_result,   # latest transaction query
            mock_rules_result,    # rules query
            MagicMock(rowcount=1),  # upsert INSERT (new tx)
            MagicMock(),            # UPDATE custom_category
        ]

        tx_data = [{
            "id": "tx_tesco_1",
            "amount": -4500,
            "merchant": {"name": "Tesco Express"},
            "category": "groceries",
            "created": "2025-01-20T10:00:00Z",
        }]

        with patch("app.services.sync.fetch_transactions", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = tx_data

            with patch("app.services.rules.categorise_transaction") as mock_categorise:
                mock_categorise.return_value = "Weekly Shop"

                count = await service._sync_account_transactions(
                    "test_token", mock_account
                )

                assert count == 1
                mock_categorise.assert_called_once_with(tx_data[0], [mock_rule])

    @pytest.mark.asyncio
    async def test_sync_preserves_existing_custom_category(self) -> None:
        """Sync should not overwrite user-set custom categories."""
        from app.services.sync import SyncService

        mock_session = AsyncMock()
        service = SyncService(mock_session)

        mock_account = MagicMock(id="acc_123", monzo_id="monzo_acc_123")

        mock_latest_result = MagicMock()
        mock_latest_result.scalar_one_or_none.return_value = None

        mock_rules_result = MagicMock()
        mock_rules_result.scalars.return_value.all.return_value = []  # No rules

        mock_session.execute.side_effect = [
            mock_latest_result,
            mock_rules_result,
            MagicMock(rowcount=1),  # upsert INSERT
        ]

        tx_data = [{
            "id": "tx_123",
            "amount": -500,
            "merchant": {"name": "Shop"},
            "category": "general",
            "created": "2025-01-20T10:00:00Z",
        }]

        with patch("app.services.sync.fetch_transactions", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = tx_data

            count = await service._sync_account_transactions(
                "test_token", mock_account
            )

            assert count == 1
            # No categorise_transaction call since no rules
            # And the UPDATE for custom_category should NOT have been called


class TestSyncBalance:
    """Tests for the _sync_balance method."""

    @pytest.mark.asyncio
    async def test_sync_balance_updates_account(self) -> None:
        """_sync_balance should store balance and spend_today on the account."""
        from app.services.sync import SyncService

        mock_session = AsyncMock()
        service = SyncService(mock_session)

        mock_account = MagicMock()
        mock_account.monzo_id = "acc_123"
        mock_account.balance = 0
        mock_account.spend_today = 0

        with patch(
            "app.services.sync.fetch_balance",
            new_callable=AsyncMock,
            return_value={"balance": 150000, "spend_today": -2500},
        ):
            await service._sync_balance("test_token", mock_account)

        assert mock_account.balance == 150000
        assert mock_account.spend_today == -2500

    @pytest.mark.asyncio
    async def test_sync_balance_handles_api_error(self) -> None:
        """_sync_balance should log warning and not crash on API error."""
        from app.services.sync import SyncService

        mock_session = AsyncMock()
        service = SyncService(mock_session)

        mock_account = MagicMock()
        mock_account.monzo_id = "acc_123"
        mock_account.balance = 99999

        with patch(
            "app.services.sync.fetch_balance",
            new_callable=AsyncMock,
            side_effect=Exception("API timeout"),
        ):
            # Should not raise
            await service._sync_balance("test_token", mock_account)

        # Balance should remain unchanged
        assert mock_account.balance == 99999

    @pytest.mark.asyncio
    async def test_sync_balance_defaults_missing_fields(self) -> None:
        """_sync_balance should default to 0 for missing fields."""
        from app.services.sync import SyncService

        mock_session = AsyncMock()
        service = SyncService(mock_session)

        mock_account = MagicMock()
        mock_account.monzo_id = "acc_123"

        with patch(
            "app.services.sync.fetch_balance",
            new_callable=AsyncMock,
            return_value={},  # Empty response
        ):
            await service._sync_balance("test_token", mock_account)

        assert mock_account.balance == 0
        assert mock_account.spend_today == 0
