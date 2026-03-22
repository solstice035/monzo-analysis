"""Review queue API endpoints for pending transaction review."""

from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database import get_session
from app.services.review_queue import ReviewQueueService

router = APIRouter(tags=["review-queue"])


class ReviewAction(BaseModel):
    """Request model for review actions."""

    budget_id: str | None = None
    action: Literal["confirm", "reassign", "exclude"]
    create_rule: bool = True


class BulkReviewAction(BaseModel):
    """Request model for bulk review actions."""

    transaction_ids: list[str]
    budget_id: str
    action: Literal["confirm", "reassign"] = "reassign"
    create_rule: bool = True


class PendingReviewResponse(BaseModel):
    """Response for pending review list."""

    items: list[dict[str, Any]]
    total: int
    limit: int
    offset: int


@router.get(
    "/accounts/{account_id}/transactions/pending-review",
    response_model=PendingReviewResponse,
)
async def get_pending_reviews(
    account_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """Get transactions pending review for an account."""
    try:
        account_uuid = UUID(account_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid account_id")

    async with get_session() as session:
        service = ReviewQueueService(session)
        transactions, total = await service.get_pending_transactions(
            account_uuid, limit=limit, offset=offset
        )
        return {
            "items": [
                {
                    "id": str(tx.id),
                    "monzo_id": tx.monzo_id,
                    "amount": tx.amount,
                    "merchant_name": tx.merchant_name,
                    "monzo_category": tx.monzo_category,
                    "custom_category": tx.custom_category,
                    "budget_id": str(tx.budget_id) if tx.budget_id else None,
                    "review_status": tx.review_status,
                    "created_at": tx.created_at.isoformat() if tx.created_at else None,
                }
                for tx in transactions
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }


@router.patch("/accounts/{account_id}/transactions/{transaction_id}/review")
async def review_transaction(
    account_id: str,
    transaction_id: str,
    data: ReviewAction,
) -> dict[str, Any]:
    """Review a pending transaction: confirm, reassign, or exclude."""
    try:
        account_uuid = UUID(account_id)
        tx_uuid = UUID(transaction_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    async with get_session() as session:
        service = ReviewQueueService(session)

        if data.action == "confirm":
            tx = await service.confirm_transaction(
                tx_uuid, account_uuid, create_rule=data.create_rule
            )
        elif data.action == "reassign":
            if not data.budget_id:
                raise HTTPException(
                    status_code=400,
                    detail="budget_id required for reassign action",
                )
            try:
                new_budget_uuid = UUID(data.budget_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid budget_id")
            tx = await service.reassign_transaction(
                tx_uuid, account_uuid, new_budget_uuid, create_rule=data.create_rule
            )
        elif data.action == "exclude":
            tx = await service.exclude_transaction(tx_uuid, account_uuid)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {data.action}")

        if not tx:
            raise HTTPException(status_code=404, detail="Transaction not found or not pending")

        await session.commit()

        return {
            "id": str(tx.id),
            "budget_id": str(tx.budget_id) if tx.budget_id else None,
            "review_status": tx.review_status,
            "action": data.action,
        }


@router.post("/accounts/{account_id}/transactions/bulk-review")
async def bulk_review_transactions(
    account_id: str,
    data: BulkReviewAction,
) -> dict[str, Any]:
    """Bulk review multiple transactions at once."""
    try:
        account_uuid = UUID(account_id)
        budget_uuid = UUID(data.budget_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    async with get_session() as session:
        service = ReviewQueueService(session)
        results = []

        for tx_id_str in data.transaction_ids:
            try:
                tx_uuid = UUID(tx_id_str)
            except ValueError:
                continue

            if data.action == "reassign":
                tx = await service.reassign_transaction(
                    tx_uuid, account_uuid, budget_uuid, create_rule=data.create_rule
                )
            else:
                tx = await service.confirm_transaction(
                    tx_uuid, account_uuid, create_rule=data.create_rule
                )

            if tx:
                results.append(str(tx.id))

        await session.commit()

        return {
            "reviewed": len(results),
            "total": len(data.transaction_ids),
            "transaction_ids": results,
        }
