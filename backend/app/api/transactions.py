"""Transactions API endpoints."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import and_, func, select

from app.database import get_session
from app.models import Transaction as TransactionModel

router = APIRouter(prefix="/transactions", tags=["transactions"])


class Transaction(BaseModel):
    """Transaction response model."""

    id: str
    monzo_id: str
    amount: int
    merchant_name: str | None = None
    monzo_category: str | None = None
    custom_category: str | None = None
    created_at: datetime
    settled_at: datetime | None = None
    notes: str | None = None


class TransactionList(BaseModel):
    """Paginated transaction list response."""

    items: list[Transaction]
    total: int


class TransactionUpdate(BaseModel):
    """Request model for updating a transaction."""

    custom_category: str | None = None
    notes: str | None = None


def transaction_to_dict(tx: TransactionModel) -> dict[str, Any]:
    """Convert a transaction model to response dict."""
    raw = tx.raw_payload or {}
    return {
        "id": str(tx.id),
        "monzo_id": tx.monzo_id,
        "amount": tx.amount,
        "merchant_name": tx.merchant_name,
        "monzo_category": tx.monzo_category,
        "custom_category": tx.custom_category,
        "created_at": tx.created_at,
        "settled_at": tx.settled_at,
        "notes": raw.get("notes"),
    }


@router.get("", response_model=TransactionList)
async def get_transactions(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    category: str | None = Query(None),
    since: str | None = Query(None),
    until: str | None = Query(None),
) -> dict[str, Any]:
    """Get paginated list of transactions."""
    async with get_session() as session:
        # Build filters
        filters = []
        if category:
            # Match either custom or monzo category
            filters.append(
                (TransactionModel.custom_category == category)
                | (TransactionModel.monzo_category == category)
            )
        if since:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
            filters.append(TransactionModel.created_at >= since_dt)
        if until:
            until_dt = datetime.fromisoformat(until.replace("Z", "+00:00"))
            filters.append(TransactionModel.created_at <= until_dt)

        # Get total count
        count_query = select(func.count(TransactionModel.id))
        if filters:
            count_query = count_query.where(and_(*filters))
        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated transactions
        query = select(TransactionModel).order_by(
            TransactionModel.created_at.desc()
        )
        if filters:
            query = query.where(and_(*filters))
        query = query.offset(offset).limit(limit)

        result = await session.execute(query)
        transactions = result.scalars().all()

        return {
            "items": [transaction_to_dict(tx) for tx in transactions],
            "total": total,
        }


@router.patch("/{transaction_id}", response_model=Transaction)
async def update_transaction(
    transaction_id: str,
    data: TransactionUpdate,
) -> dict[str, Any]:
    """Update a transaction (custom category, notes)."""
    async with get_session() as session:
        result = await session.execute(
            select(TransactionModel).where(TransactionModel.id == transaction_id)
        )
        tx = result.scalar_one_or_none()

        if not tx:
            raise HTTPException(status_code=404, detail="Transaction not found")

        # Update fields
        if data.custom_category is not None:
            tx.custom_category = data.custom_category

        if data.notes is not None:
            # Store notes in raw_payload
            if tx.raw_payload is None:
                tx.raw_payload = {}
            tx.raw_payload["notes"] = data.notes

        await session.commit()
        await session.refresh(tx)

        return transaction_to_dict(tx)
