"""Budget import service for CSV/Excel parsing and upsert.

Parses budget spreadsheets with columns: Group, Category, Monthly Amount,
Timeline, Payment Method. Maps to BudgetGroup + Budget models.
"""

import csv
import io
import logging
import re
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Budget, BudgetGroup

logger = logging.getLogger(__name__)

# Groups that are sinking funds (annual targets, not monthly envelopes)
SINKING_FUND_GROUPS = {"car expenses", "savings"}

# Groups to skip entirely during import
SKIP_GROUPS = {"nanny"}


@dataclass
class ParsedLineItem:
    """A parsed budget line item from the spreadsheet."""

    group: str
    category: str
    amount_pence: int  # Monthly amount in pence
    timeline: str = ""
    payment_method: str = ""
    period_type: str = "monthly"  # 'monthly' or 'annual'
    annual_amount_pence: int | None = None
    is_zero: bool = False  # True if amount was 0 or TBC
    notes: str = ""


@dataclass
class ParsedBudget:
    """Result of parsing a budget spreadsheet."""

    groups: dict[str, list[ParsedLineItem]] = field(default_factory=dict)
    skipped_groups: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    total_monthly_pence: int = 0
    line_count: int = 0


def parse_amount(amount_str: str) -> int:
    """Parse a monetary amount string to pence.

    Handles formats: £650.00, 650.00, 650, £0, TBC, empty.
    Returns 0 for TBC/empty/unparseable values.
    """
    if not amount_str:
        return 0

    cleaned = amount_str.strip().upper()
    if cleaned in ("TBC", "N/A", "-", ""):
        return 0

    # Remove currency symbol, commas, whitespace
    cleaned = re.sub(r"[£$,\s]", "", cleaned)

    try:
        return int(float(cleaned) * 100)
    except (ValueError, TypeError):
        return 0


def determine_period_type(group_name: str, timeline: str) -> str:
    """Determine if a line item is monthly or annual (sinking fund).

    Car Expenses and Savings groups are always sinking funds.
    Items with 'annual' in their timeline are sinking funds.
    """
    if group_name.lower().strip() in SINKING_FUND_GROUPS:
        return "annual"

    timeline_lower = timeline.lower().strip() if timeline else ""
    if "annual" in timeline_lower or "bi-annual" in timeline_lower:
        return "annual"

    return "monthly"


def parse_csv(content: str) -> ParsedBudget:
    """Parse a CSV budget file.

    Expected columns: Group, Category, Monthly Amount, Timeline, Payment Method
    Column matching is case-insensitive and flexible.
    """
    result = ParsedBudget()
    reader = csv.DictReader(io.StringIO(content))

    if not reader.fieldnames:
        result.warnings.append("No columns found in CSV")
        return result

    # Normalise column names for flexible matching
    col_map = _map_columns(reader.fieldnames)

    for row_num, row in enumerate(reader, start=2):
        _process_row(row, row_num, col_map, result)

    return result


def parse_excel(file_bytes: bytes) -> ParsedBudget:
    """Parse an Excel budget file.

    Uses openpyxl for .xlsx files. Expects same column structure as CSV.
    """
    try:
        import openpyxl
    except ImportError:
        result = ParsedBudget()
        result.warnings.append("openpyxl not installed — cannot parse Excel files")
        return result

    result = ParsedBudget()
    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True)
    ws = wb.active

    if ws is None:
        result.warnings.append("No active worksheet found")
        return result

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        result.warnings.append("Worksheet is empty")
        return result

    # First row is headers
    headers = [str(h).strip() if h else "" for h in rows[0]]
    col_map = _map_columns(headers)

    for row_num, row_data in enumerate(rows[1:], start=2):
        row_dict = {headers[i]: (str(v).strip() if v else "") for i, v in enumerate(row_data) if i < len(headers)}
        _process_row(row_dict, row_num, col_map, result)

    wb.close()
    return result


def _map_columns(fieldnames: list[str] | Any) -> dict[str, str]:
    """Map expected logical columns to actual column names.

    Handles variations like 'Monthly Amount', 'Amount', 'monthly_amount', etc.
    """
    col_map: dict[str, str] = {}
    normalised = {f.lower().strip().replace("_", " "): f for f in fieldnames if f}

    # Group
    for candidate in ("group", "budget group", "category group"):
        if candidate in normalised:
            col_map["group"] = normalised[candidate]
            break

    # Category
    for candidate in ("category", "line item", "item", "name", "budget"):
        if candidate in normalised:
            col_map["category"] = normalised[candidate]
            break

    # Monthly Amount
    for candidate in ("monthly amount", "amount", "monthly", "budget amount"):
        if candidate in normalised:
            col_map["amount"] = normalised[candidate]
            break

    # Timeline
    for candidate in ("timeline", "frequency", "period", "schedule"):
        if candidate in normalised:
            col_map["timeline"] = normalised[candidate]
            break

    # Payment Method
    for candidate in ("payment method", "payment", "method", "type"):
        if candidate in normalised:
            col_map["payment_method"] = normalised[candidate]
            break

    return col_map


def _process_row(
    row: dict[str, Any],
    row_num: int,
    col_map: dict[str, str],
    result: ParsedBudget,
) -> None:
    """Process a single row from the spreadsheet."""
    group = str(row.get(col_map.get("group", ""), "")).strip()
    category = str(row.get(col_map.get("category", ""), "")).strip()
    amount_str = str(row.get(col_map.get("amount", ""), "")).strip()
    timeline = str(row.get(col_map.get("timeline", ""), "")).strip()
    payment_method = str(row.get(col_map.get("payment_method", ""), "")).strip()

    if not group or not category:
        return  # Skip empty rows

    # Skip excluded groups
    if group.lower().strip() in SKIP_GROUPS:
        if group not in result.skipped_groups:
            result.skipped_groups.append(group)
        return

    amount_pence = parse_amount(amount_str)
    is_zero = amount_pence == 0 and amount_str.strip().upper() not in ("0", "£0", "£0.00")
    period_type = determine_period_type(group, timeline)

    # For sinking funds, calculate annual amount from monthly
    annual_amount = None
    if period_type == "annual" and amount_pence > 0:
        annual_amount = amount_pence * 12

    item = ParsedLineItem(
        group=group,
        category=category,
        amount_pence=amount_pence,
        timeline=timeline,
        payment_method=payment_method,
        period_type=period_type,
        annual_amount_pence=annual_amount,
        is_zero=is_zero,
    )

    if group not in result.groups:
        result.groups[group] = []
    result.groups[group].append(item)
    result.total_monthly_pence += amount_pence
    result.line_count += 1

    if is_zero:
        result.warnings.append(f"Row {row_num}: '{category}' has £0/TBC amount")


class BudgetImportService:
    """Service for importing budgets from parsed spreadsheets."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def preview(self, parsed: ParsedBudget) -> dict[str, Any]:
        """Return a preview of what would be imported, without committing.

        Returns:
            Dict with groups, line items, warnings, and totals.
        """
        preview_groups = []
        for group_name, items in parsed.groups.items():
            group_total = sum(i.amount_pence for i in items)
            preview_groups.append({
                "name": group_name,
                "item_count": len(items),
                "total_monthly_pence": group_total,
                "items": [
                    {
                        "category": i.category,
                        "amount_pence": i.amount_pence,
                        "period_type": i.period_type,
                        "annual_amount_pence": i.annual_amount_pence,
                        "timeline": i.timeline,
                        "payment_method": i.payment_method,
                        "is_zero": i.is_zero,
                    }
                    for i in items
                ],
            })

        return {
            "groups": preview_groups,
            "skipped_groups": parsed.skipped_groups,
            "warnings": parsed.warnings,
            "total_monthly_pence": parsed.total_monthly_pence,
            "total_line_items": parsed.line_count,
        }

    async def commit(
        self,
        account_id: UUID,
        parsed: ParsedBudget,
    ) -> dict[str, Any]:
        """Upsert BudgetGroups and Budgets from parsed data.

        Groups are matched by name (case-insensitive).
        Budgets are matched by category within a group (case-insensitive).
        Existing records are updated; new records are created.

        Returns:
            Dict with counts: created_groups, created_budgets, updated_budgets, warnings.
        """
        created_groups = 0
        created_budgets = 0
        updated_budgets = 0

        # Load existing groups for this account
        existing_groups = await self._get_existing_groups(account_id)
        existing_budgets = await self._get_existing_budgets(account_id)

        display_order = 0
        for group_name, items in parsed.groups.items():
            display_order += 1
            group_key = group_name.lower().strip()

            # Upsert group
            if group_key in existing_groups:
                group = existing_groups[group_key]
            else:
                group = BudgetGroup(
                    id=uuid4(),
                    account_id=account_id,
                    name=group_name,
                    display_order=display_order,
                )
                self._session.add(group)
                await self._session.flush()
                existing_groups[group_key] = group
                created_groups += 1

            # Upsert budgets within group
            for item in items:
                budget_key = (group.id, item.category.lower().strip())

                if budget_key in existing_budgets:
                    budget = existing_budgets[budget_key]
                    budget.amount = item.amount_pence
                    budget.period_type = item.period_type
                    if item.annual_amount_pence is not None:
                        budget.annual_amount = item.annual_amount_pence
                    updated_budgets += 1
                else:
                    budget = Budget(
                        id=uuid4(),
                        account_id=account_id,
                        group_id=group.id,
                        name=item.category,
                        category=item.category.lower().replace(" ", "_"),
                        amount=item.amount_pence,
                        period="monthly",
                        period_type=item.period_type,
                        start_day=28,
                        annual_amount=item.annual_amount_pence,
                    )
                    self._session.add(budget)
                    existing_budgets[budget_key] = budget
                    created_budgets += 1

        return {
            "created_groups": created_groups,
            "created_budgets": created_budgets,
            "updated_budgets": updated_budgets,
            "warnings": parsed.warnings,
        }

    async def _get_existing_groups(self, account_id: UUID) -> dict[str, BudgetGroup]:
        """Load existing groups indexed by lowercase name."""
        result = await self._session.execute(
            select(BudgetGroup).where(BudgetGroup.account_id == account_id)
        )
        return {g.name.lower().strip(): g for g in result.scalars().all()}

    async def _get_existing_budgets(self, account_id: UUID) -> dict[tuple, Budget]:
        """Load existing budgets indexed by (group_id, lowercase category)."""
        result = await self._session.execute(
            select(Budget).where(
                and_(
                    Budget.account_id == account_id,
                    Budget.deleted_at.is_(None),
                )
            )
        )
        return {
            (b.group_id, b.category.lower().strip()): b
            for b in result.scalars().all()
            if b.group_id is not None
        }
