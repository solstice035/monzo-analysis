"""Tests for transactions API — GET filters/pagination, PATCH category override."""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


def _mock_get_session(mock_session):
    """Create a mock get_session context manager."""
    @asynccontextmanager
    async def _get_session():
        yield mock_session

    return _get_session


def _make_mock_transaction(**overrides):
    """Create a mock Transaction model."""
    tx = MagicMock()
    tx.id = overrides.get("id", uuid4())
    tx.monzo_id = overrides.get("monzo_id", "tx_mock_123")
    tx.amount = overrides.get("amount", -1500)
    tx.merchant_name = overrides.get("merchant_name", "Tesco")
    tx.monzo_category = overrides.get("monzo_category", "groceries")
    tx.custom_category = overrides.get("custom_category", None)
    tx.created_at = overrides.get("created_at", datetime(2026, 2, 1, tzinfo=timezone.utc))
    tx.settled_at = overrides.get("settled_at", None)
    tx.raw_payload = overrides.get("raw_payload", {"notes": "test"})
    return tx


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def client(mock_session):
    with patch("app.api.transactions.get_session", _mock_get_session(mock_session)):
        from app.main import create_app

        app = create_app()
        with TestClient(app) as client:
            yield client


class TestGetTransactions:
    """Tests for GET /api/v1/transactions."""

    def test_requires_account_id(self, client: TestClient) -> None:
        """Should return 422 without account_id."""
        response = client.get("/api/v1/transactions")
        assert response.status_code == 422

    def test_returns_items_and_total(
        self, client: TestClient, mock_session: AsyncMock
    ) -> None:
        """Should return paginated transaction list."""
        tx = _make_mock_transaction()

        # First execute: count query
        mock_count = MagicMock()
        mock_count.scalar.return_value = 1

        # Second execute: transaction query
        mock_txs = MagicMock()
        mock_txs.scalars.return_value.all.return_value = [tx]

        mock_session.execute.side_effect = [mock_count, mock_txs]

        response = client.get("/api/v1/transactions?account_id=acc_123")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["monzo_id"] == "tx_mock_123"
        assert data["items"][0]["amount"] == -1500

    def test_pagination_params(
        self, client: TestClient, mock_session: AsyncMock
    ) -> None:
        """Should accept limit and offset params."""
        mock_count = MagicMock()
        mock_count.scalar.return_value = 0
        mock_txs = MagicMock()
        mock_txs.scalars.return_value.all.return_value = []
        mock_session.execute.side_effect = [mock_count, mock_txs]

        response = client.get(
            "/api/v1/transactions?account_id=acc_123&limit=10&offset=20"
        )
        assert response.status_code == 200

    def test_limit_validation(self, client: TestClient) -> None:
        """Limit should be between 1 and 500."""
        response = client.get(
            "/api/v1/transactions?account_id=acc_123&limit=0"
        )
        assert response.status_code == 422

        response = client.get(
            "/api/v1/transactions?account_id=acc_123&limit=501"
        )
        assert response.status_code == 422

    def test_category_filter(
        self, client: TestClient, mock_session: AsyncMock
    ) -> None:
        """Should filter by category when provided."""
        mock_count = MagicMock()
        mock_count.scalar.return_value = 0
        mock_txs = MagicMock()
        mock_txs.scalars.return_value.all.return_value = []
        mock_session.execute.side_effect = [mock_count, mock_txs]

        response = client.get(
            "/api/v1/transactions?account_id=acc_123&category=groceries"
        )
        assert response.status_code == 200

    def test_search_filter(
        self, client: TestClient, mock_session: AsyncMock
    ) -> None:
        """Should accept search parameter for merchant name."""
        mock_count = MagicMock()
        mock_count.scalar.return_value = 0
        mock_txs = MagicMock()
        mock_txs.scalars.return_value.all.return_value = []
        mock_session.execute.side_effect = [mock_count, mock_txs]

        response = client.get(
            "/api/v1/transactions?account_id=acc_123&search=tesco"
        )
        assert response.status_code == 200

    def test_date_range_filter(
        self, client: TestClient, mock_session: AsyncMock
    ) -> None:
        """Should accept since and until date params."""
        mock_count = MagicMock()
        mock_count.scalar.return_value = 0
        mock_txs = MagicMock()
        mock_txs.scalars.return_value.all.return_value = []
        mock_session.execute.side_effect = [mock_count, mock_txs]

        response = client.get(
            "/api/v1/transactions?account_id=acc_123"
            "&since=2026-01-01T00:00:00Z&until=2026-01-31T23:59:59Z"
        )
        assert response.status_code == 200


class TestUpdateTransaction:
    """Tests for PATCH /api/v1/transactions/{id}."""

    def test_returns_404_for_missing_transaction(
        self, client: TestClient, mock_session: AsyncMock
    ) -> None:
        """Should return 404 when transaction not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        response = client.patch(
            "/api/v1/transactions/nonexistent",
            json={"custom_category": "Groceries"},
        )
        assert response.status_code == 404

    def test_updates_custom_category(
        self, client: TestClient, mock_session: AsyncMock
    ) -> None:
        """Should update custom_category and return updated transaction."""
        tx = _make_mock_transaction()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = tx
        mock_session.execute.return_value = mock_result

        # Mock the refresh to be a no-op
        mock_session.refresh = AsyncMock()

        response = client.patch(
            f"/api/v1/transactions/{tx.id}",
            json={"custom_category": "Weekly Shop"},
        )

        assert response.status_code == 200
        assert tx.custom_category == "Weekly Shop"

    def test_updates_notes_with_flag_modified(
        self, client: TestClient, mock_session: AsyncMock
    ) -> None:
        """Should update notes in raw_payload and call flag_modified."""
        tx = _make_mock_transaction(raw_payload={"existing": "data"})

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = tx
        mock_session.execute.return_value = mock_result
        mock_session.refresh = AsyncMock()

        with patch("app.api.transactions.flag_modified") as mock_flag:
            response = client.patch(
                f"/api/v1/transactions/{tx.id}",
                json={"notes": "Updated note"},
            )

            assert response.status_code == 200
            assert tx.raw_payload["notes"] == "Updated note"
            mock_flag.assert_called_once_with(tx, "raw_payload")

    def test_creates_raw_payload_if_none(
        self, client: TestClient, mock_session: AsyncMock
    ) -> None:
        """Should create raw_payload dict if it's None when setting notes."""
        tx = _make_mock_transaction(raw_payload=None)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = tx
        mock_session.execute.return_value = mock_result
        mock_session.refresh = AsyncMock()

        response = client.patch(
            f"/api/v1/transactions/{tx.id}",
            json={"notes": "New note"},
        )

        assert response.status_code == 200
        assert tx.raw_payload == {"notes": "New note"}
