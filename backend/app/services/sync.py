"""Transaction sync service for fetching and storing Monzo data."""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Account, Auth, Pot, SyncLog, Transaction


class SyncError(Exception):
    """Error during sync operation."""

    pass


async def upsert_transaction(
    session: AsyncSession,
    account_id: str,
    tx_data: dict[str, Any],
) -> bool:
    """Insert or update a transaction.

    Args:
        session: Database session
        account_id: Internal account UUID
        tx_data: Transaction data from Monzo API

    Returns:
        True if new transaction created, False if updated
    """
    monzo_id = tx_data["id"]

    # Check if transaction exists
    result = await session.execute(
        select(Transaction).where(Transaction.monzo_id == monzo_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Update existing transaction (e.g., settled status)
        if "settled" in tx_data and tx_data["settled"]:
            existing.settled_at = datetime.fromisoformat(
                tx_data["settled"].replace("Z", "+00:00")
            )
        return False

    # Create new transaction
    merchant = tx_data.get("merchant") or {}
    transaction = Transaction(
        monzo_id=monzo_id,
        account_id=account_id,
        amount=tx_data["amount"],
        merchant_name=merchant.get("name") if isinstance(merchant, dict) else None,
        monzo_category=tx_data.get("category"),
        created_at=datetime.fromisoformat(tx_data["created"].replace("Z", "+00:00")),
        settled_at=(
            datetime.fromisoformat(tx_data["settled"].replace("Z", "+00:00"))
            if tx_data.get("settled")
            else None
        ),
        raw_payload=tx_data,
    )
    session.add(transaction)
    return True


class SyncService:
    """Orchestrates sync operations."""

    async def run_sync(self) -> int:
        """Run a full sync operation.

        Returns:
            Number of transactions synced

        Raises:
            SyncError: If not authenticated or sync fails
        """
        # Get current auth
        auth = await self._get_auth()
        if not auth:
            raise SyncError("Not authenticated")

        # Create sync log
        sync_log = await self._create_sync_log()
        transactions_synced = 0

        try:
            # Sync accounts
            await self._sync_accounts(auth.access_token)

            # Sync transactions for each account
            transactions_synced = await self._sync_transactions(auth.access_token)

            # Update sync log with success
            await self._update_sync_log(
                sync_log_id=sync_log.id,
                status="success",
                transactions_synced=transactions_synced,
            )

        except Exception as e:
            # Update sync log with failure
            await self._update_sync_log(
                sync_log_id=sync_log.id,
                status="failed",
                error=str(e),
            )
            raise

        return transactions_synced

    async def _get_auth(self) -> Auth | None:
        """Get current authentication."""
        # TODO: Implement database lookup
        return None

    async def _sync_accounts(self, access_token: str) -> None:
        """Sync accounts from Monzo."""
        # TODO: Implement account sync
        pass

    async def _sync_transactions(self, access_token: str) -> int:
        """Sync transactions for all accounts."""
        # TODO: Implement transaction sync
        return 0

    async def _create_sync_log(self) -> SyncLog:
        """Create a new sync log entry."""
        sync_log = SyncLog(
            id=uuid.uuid4(),
            started_at=datetime.now(timezone.utc),
            status="running",
        )
        # TODO: Save to database
        return sync_log

    async def _update_sync_log(
        self,
        sync_log_id: uuid.UUID,
        status: str,
        transactions_synced: int = 0,
        error: str | None = None,
    ) -> None:
        """Update sync log with result."""
        # TODO: Update in database
        pass
