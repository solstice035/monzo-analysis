"""Sync API endpoints."""

from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select

from app.database import get_session
from app.models import SyncLog
from app.services.sync import SyncError, SyncService

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
    sync_id: str | None = None


async def run_sync_task() -> None:
    """Background task to run sync."""
    async with get_session() as session:
        service = SyncService(session)
        try:
            await service.run_sync()
        except SyncError:
            # Error already logged in sync_log
            pass


@router.get("/status", response_model=SyncStatus)
async def get_sync_status() -> dict[str, Any]:
    """Get current sync status from database."""
    async with get_session() as session:
        result = await session.execute(
            select(SyncLog).order_by(SyncLog.started_at.desc()).limit(1)
        )
        sync_log = result.scalar_one_or_none()

        if not sync_log:
            return {
                "last_sync": None,
                "transactions_synced": None,
                "status": "idle",
                "error": None,
            }

        return {
            "last_sync": sync_log.completed_at or sync_log.started_at,
            "transactions_synced": sync_log.transactions_synced,
            "status": sync_log.status,
            "error": sync_log.error,
        }


@router.post("/trigger", response_model=SyncTriggerResponse)
async def trigger_sync(background_tasks: BackgroundTasks) -> dict[str, Any]:
    """Manually trigger a sync operation."""
    # Check if sync is already running
    async with get_session() as session:
        result = await session.execute(
            select(SyncLog)
            .where(SyncLog.status == "running")
            .order_by(SyncLog.started_at.desc())
            .limit(1)
        )
        running = result.scalar_one_or_none()

        if running:
            return {
                "message": "Sync already in progress",
                "sync_id": str(running.id),
            }

    # Trigger background sync
    background_tasks.add_task(run_sync_task)
    return {"message": "Sync triggered successfully", "sync_id": None}
