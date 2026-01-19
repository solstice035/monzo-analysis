"""Accounts API endpoints."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.database import get_session
from app.models import Account as AccountModel

router = APIRouter(prefix="/accounts", tags=["accounts"])


class AccountResponse(BaseModel):
    """Account response model."""

    id: str
    monzo_id: str
    type: str
    name: str | None = None


@router.get("", response_model=list[AccountResponse])
async def get_accounts() -> list[dict[str, Any]]:
    """Get all accounts.

    Returns accounts ordered by type (joint accounts first for default selection).
    """
    async with get_session() as session:
        # Order by type descending so uk_retail_joint comes before uk_retail
        result = await session.execute(
            select(AccountModel).order_by(AccountModel.type.desc())
        )
        accounts = result.scalars().all()
        return [
            {
                "id": str(a.id),
                "monzo_id": a.monzo_id,
                "type": a.type,
                "name": a.name,
            }
            for a in accounts
        ]
