"""Transaction sync service for fetching and storing Monzo data."""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import Account, Auth, Pot, SyncLog, Transaction
from app.services.monzo import (
    fetch_accounts,
    fetch_pots,
    fetch_transactions,
)


class SyncError(Exception):
    """Error during sync operation."""

    pass


async def upsert_transaction(
    session: AsyncSession,
    account_id: uuid.UUID,
    tx_data: dict[str, Any],
) -> bool:
    """Insert or update a transaction."""
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

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session

    async def run_sync(self) -> int:
        """Run a full sync operation."""
        # Get current auth
        auth = await self._get_auth()
        if not auth:
            raise SyncError("Not authenticated")

        # Check if token is expired
        if auth.expires_at < datetime.now(timezone.utc):
            raise SyncError("Token expired - re-authentication required")

        # Create sync log
        sync_log = await self._create_sync_log()
        transactions_synced = 0

        try:
            # Sync accounts
            accounts = await self._sync_accounts(auth.access_token)

            # Sync transactions and pots for each account
            for account in accounts:
                count = await self._sync_account_transactions(
                    auth.access_token, account
                )
                transactions_synced += count
                await self._sync_pots(auth.access_token, account)

            # Update sync log with success
            await self._update_sync_log(sync_log, "success", transactions_synced)
            await self.session.commit()

        except Exception as e:
            await self._update_sync_log(sync_log, "failed", error=str(e))
            await self.session.commit()
            raise SyncError(str(e)) from e

        return transactions_synced

    async def _get_auth(self) -> Auth | None:
        """Get current authentication."""
        result = await self.session.execute(select(Auth).limit(1))
        return result.scalar_one_or_none()

    async def _sync_accounts(self, access_token: str) -> list[Account]:
        """Sync accounts from Monzo."""
        monzo_accounts = await fetch_accounts(access_token)
        accounts = []

        for ma in monzo_accounts:
            result = await self.session.execute(
                select(Account).where(Account.monzo_id == ma["id"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                accounts.append(existing)
            else:
                account = Account(
                    monzo_id=ma["id"],
                    type=ma.get("type", "unknown"),
                    name=ma.get("description"),
                )
                self.session.add(account)
                await self.session.flush()
                accounts.append(account)

        return accounts

    async def _sync_account_transactions(
        self, access_token: str, account: Account
    ) -> int:
        """Sync transactions for a single account."""
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.account_id == account.id)
            .order_by(Transaction.created_at.desc())
            .limit(1)
        )
        latest = result.scalar_one_or_none()

        since = latest.created_at if latest else None
        transactions = await fetch_transactions(
            access_token, account.monzo_id, since=since
        )

        new_count = 0
        for tx_data in transactions:
            is_new = await upsert_transaction(self.session, account.id, tx_data)
            if is_new:
                new_count += 1

        await self.session.flush()
        return new_count

    async def _sync_pots(self, access_token: str, account: Account) -> None:
        """Sync pots for an account."""
        monzo_pots = await fetch_pots(access_token, account.monzo_id)

        for mp in monzo_pots:
            result = await self.session.execute(
                select(Pot).where(Pot.monzo_id == mp["id"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                existing.balance = mp.get("balance", 0)
                existing.deleted = mp.get("deleted", False)
            else:
                pot = Pot(
                    monzo_id=mp["id"],
                    account_id=account.id,
                    name=mp.get("name", "Unknown"),
                    balance=mp.get("balance", 0),
                    deleted=mp.get("deleted", False),
                )
                self.session.add(pot)

        await self.session.flush()

    async def _create_sync_log(self) -> SyncLog:
        """Create a new sync log entry."""
        sync_log = SyncLog(
            started_at=datetime.now(timezone.utc),
            status="running",
        )
        self.session.add(sync_log)
        await self.session.flush()
        return sync_log

    async def _update_sync_log(
        self,
        sync_log: SyncLog,
        status: str,
        transactions_synced: int = 0,
        error: str | None = None,
    ) -> None:
        """Update sync log with result."""
        sync_log.status = status
        sync_log.completed_at = datetime.now(timezone.utc)
        sync_log.transactions_synced = transactions_synced
        sync_log.error = error


async def get_latest_sync() -> SyncLog | None:
    """Get the most recent sync log entry."""
    async with get_session() as session:
        result = await session.execute(
            select(SyncLog).order_by(SyncLog.started_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()
