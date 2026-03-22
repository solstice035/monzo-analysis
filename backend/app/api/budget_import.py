"""Budget import API endpoints for CSV/Excel upload."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from app.database import get_session
from app.services.budget_import import (
    BudgetImportService,
    parse_csv,
    parse_excel,
)

router = APIRouter(prefix="/budget-import", tags=["budget-import"])


class ImportPreviewResponse(BaseModel):
    """Response for import preview."""

    groups: list[dict[str, Any]]
    skipped_groups: list[str]
    warnings: list[str]
    total_monthly_pence: int
    total_line_items: int


class ImportCommitResponse(BaseModel):
    """Response for import commit."""

    created_groups: int
    created_budgets: int
    updated_budgets: int
    warnings: list[str]


@router.post("/preview", response_model=ImportPreviewResponse)
async def preview_import(
    account_id: str = Query(..., description="Account ID to preview import for"),
    file: UploadFile = File(...),
) -> dict[str, Any]:
    """Upload and parse a budget file, returning a preview without committing.

    Accepts CSV (.csv) or Excel (.xlsx) files.
    Expected columns: Group, Category, Monthly Amount, Timeline, Payment Method.
    """
    content = await file.read()
    filename = file.filename or ""

    if filename.endswith(".xlsx"):
        parsed = parse_excel(content)
    elif filename.endswith(".csv"):
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded")
        parsed = parse_csv(text)
    else:
        raise HTTPException(
            status_code=400,
            detail="File must be .csv or .xlsx",
        )

    async with get_session() as session:
        service = BudgetImportService(session)
        return await service.preview(parsed)


@router.post("/commit", response_model=ImportCommitResponse)
async def commit_import(
    account_id: str = Query(..., description="Account ID to import into"),
    file: UploadFile = File(...),
) -> dict[str, Any]:
    """Upload and commit a budget file, creating/updating groups and budgets.

    Accepts CSV (.csv) or Excel (.xlsx) files.
    Upserts: existing groups/budgets matched by name are updated; new ones created.
    """
    content = await file.read()
    filename = file.filename or ""

    if filename.endswith(".xlsx"):
        parsed = parse_excel(content)
    elif filename.endswith(".csv"):
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded")
        parsed = parse_csv(text)
    else:
        raise HTTPException(
            status_code=400,
            detail="File must be .csv or .xlsx",
        )

    try:
        account_uuid = UUID(account_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid account_id format")

    async with get_session() as session:
        service = BudgetImportService(session)
        result = await service.commit(account_uuid, parsed)
        await session.commit()
        return result
