"""Transactions API endpoints."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel

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


@router.get("", response_model=TransactionList)
async def get_transactions(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    category: str | None = Query(None),
    since: str | None = Query(None),
    until: str | None = Query(None),
) -> dict[str, Any]:
    """Get paginated list of transactions."""
    # TODO: Implement database query
    return {"items": [], "total": 0}


@router.patch("/{transaction_id}", response_model=Transaction)
async def update_transaction(
    transaction_id: str,
    data: TransactionUpdate,
) -> dict[str, Any]:
    """Update a transaction (custom category, notes)."""
    # TODO: Implement database update
    return {
        "id": transaction_id,
        "monzo_id": "",
        "amount": 0,
        "created_at": datetime.now(),
    }
