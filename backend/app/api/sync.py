"""Sync API endpoints."""

from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/sync", tags=["sync"])


class SyncStatus(BaseModel):
    """Sync status response model."""

    last_sync: datetime | None = None
    transactions_synced: int | None = None
    status: Literal["idle", "running", "success", "failed"]
    error: str | None = None


class SyncTriggerResponse(BaseModel):
    """Response for sync trigger."""

    message: str


# In-memory sync state (would be stored in Redis/database in production)
_sync_status: dict[str, Any] = {
    "last_sync": None,
    "transactions_synced": None,
    "status": "idle",
    "error": None,
}


@router.get("/status", response_model=SyncStatus)
async def get_sync_status() -> dict[str, Any]:
    """Get current sync status."""
    return _sync_status


@router.post("/trigger", response_model=SyncTriggerResponse)
async def trigger_sync() -> dict[str, Any]:
    """Manually trigger a sync."""
    # TODO: Implement actual sync trigger via scheduler
    _sync_status["status"] = "running"
    return {"message": "Sync triggered successfully"}
