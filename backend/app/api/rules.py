"""Category rules API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database import get_session
from app.services.rules import RulesService

router = APIRouter(prefix="/rules", tags=["rules"])


class CategoryRuleResponse(BaseModel):
    """Category rule response model."""

    id: str
    account_id: str
    name: str
    conditions: dict[str, Any]
    target_category: str
    priority: int
    enabled: bool


class RuleCreate(BaseModel):
    """Request model for creating a rule."""

    account_id: str
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


@router.get("", response_model=list[CategoryRuleResponse])
async def get_rules(
    account_id: str = Query(..., description="Account ID to filter rules"),
) -> list[dict[str, Any]]:
    """Get all category rules for a specific account."""
    async with get_session() as session:
        service = RulesService(session)
        rules = await service.get_all_rules(account_id)
        return [
            {
                "id": str(r.id),
                "account_id": str(r.account_id),
                "name": r.name,
                "conditions": r.conditions,
                "target_category": r.target_category,
                "priority": r.priority,
                "enabled": r.enabled,
            }
            for r in rules
        ]


@router.post("", response_model=CategoryRuleResponse, status_code=201)
async def create_rule(data: RuleCreate) -> dict[str, Any]:
    """Create a new category rule for a specific account."""
    async with get_session() as session:
        service = RulesService(session)
        # Extract condition fields from the conditions dict
        conditions = data.conditions
        rule = await service.create_rule(
            account_id=data.account_id,
            name=data.name,
            target_category=data.target_category,
            priority=data.priority,
            merchant_pattern=conditions.get("merchant_pattern"),
            amount_min=conditions.get("amount_min"),
            amount_max=conditions.get("amount_max"),
            monzo_category=conditions.get("monzo_category"),
            enabled=data.enabled,
        )
        return {
            "id": str(rule.id),
            "account_id": str(rule.account_id),
            "name": rule.name,
            "conditions": rule.conditions,
            "target_category": rule.target_category,
            "priority": rule.priority,
            "enabled": rule.enabled,
        }


@router.patch("/{rule_id}", response_model=CategoryRuleResponse)
async def update_rule(rule_id: str, data: RuleUpdate) -> dict[str, Any]:
    """Update an existing rule."""
    async with get_session() as session:
        service = RulesService(session)
        conditions = data.conditions or {}
        rule = await service.update_rule(
            rule_id=rule_id,
            name=data.name,
            target_category=data.target_category,
            priority=data.priority,
            enabled=data.enabled,
            merchant_pattern=conditions.get("merchant_pattern"),
            amount_min=conditions.get("amount_min"),
            amount_max=conditions.get("amount_max"),
            monzo_category=conditions.get("monzo_category"),
        )
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        return {
            "id": str(rule.id),
            "account_id": str(rule.account_id),
            "name": rule.name,
            "conditions": rule.conditions,
            "target_category": rule.target_category,
            "priority": rule.priority,
            "enabled": rule.enabled,
        }


@router.delete("/{rule_id}", status_code=204)
async def delete_rule(rule_id: str) -> None:
    """Delete a category rule."""
    async with get_session() as session:
        service = RulesService(session)
        deleted = await service.delete_rule(rule_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Rule not found")
