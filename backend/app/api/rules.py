"""Category rules API endpoints."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/rules", tags=["rules"])


class CategoryRule(BaseModel):
    """Category rule response model."""

    id: str
    name: str
    conditions: dict[str, Any]
    target_category: str
    priority: int
    enabled: bool


class RuleCreate(BaseModel):
    """Request model for creating a rule."""

    name: str
    conditions: dict[str, Any]
    target_category: str
    priority: int = 100
    enabled: bool = True


class RuleUpdate(BaseModel):
    """Request model for updating a rule."""

    name: str | None = None
    conditions: dict[str, Any] | None = None
    target_category: str | None = None
    priority: int | None = None
    enabled: bool | None = None


@router.get("", response_model=list[CategoryRule])
async def get_rules() -> list[dict[str, Any]]:
    """Get all category rules."""
    # TODO: Implement database query
    return []


@router.post("", response_model=CategoryRule, status_code=201)
async def create_rule(data: RuleCreate) -> dict[str, Any]:
    """Create a new category rule."""
    # TODO: Implement database insert
    return {
        "id": "new-rule-id",
        "name": data.name,
        "conditions": data.conditions,
        "target_category": data.target_category,
        "priority": data.priority,
        "enabled": data.enabled,
    }


@router.patch("/{rule_id}", response_model=CategoryRule)
async def update_rule(rule_id: str, data: RuleUpdate) -> dict[str, Any]:
    """Update an existing rule."""
    # TODO: Implement database update
    return {
        "id": rule_id,
        "name": data.name or "unknown",
        "conditions": data.conditions or {},
        "target_category": data.target_category or "",
        "priority": data.priority or 100,
        "enabled": data.enabled if data.enabled is not None else True,
    }


@router.delete("/{rule_id}", status_code=204)
async def delete_rule(rule_id: str) -> None:
    """Delete a category rule."""
    # TODO: Implement database delete
    pass
