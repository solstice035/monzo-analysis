"""Tests for budget import service: CSV/Excel parsing and upsert logic."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.budget_import import (
    SINKING_FUND_GROUPS,
    SKIP_GROUPS,
    BudgetImportService,
    ParsedBudget,
    ParsedLineItem,
    determine_period_type,
    parse_amount,
    parse_csv,
)


class TestParseAmount:
    """Tests for monetary amount parsing."""

    def test_parse_pounds_and_pence(self):
        assert parse_amount("£650.00") == 65000

    def test_parse_without_symbol(self):
        assert parse_amount("650.00") == 65000

    def test_parse_integer(self):
        assert parse_amount("650") == 65000

    def test_parse_zero(self):
        assert parse_amount("£0") == 0
        assert parse_amount("0") == 0
        assert parse_amount("£0.00") == 0

    def test_parse_tbc(self):
        assert parse_amount("TBC") == 0

    def test_parse_empty(self):
        assert parse_amount("") == 0

    def test_parse_na(self):
        assert parse_amount("N/A") == 0

    def test_parse_with_commas(self):
        assert parse_amount("£1,598.81") == 159881

    def test_parse_whitespace(self):
        assert parse_amount("  £40.00  ") == 4000

    def test_parse_small_amount(self):
        assert parse_amount("£3.25") == 325

    def test_parse_large_amount(self):
        assert parse_amount("£1598.81") == 159881


class TestDeterminePeriodType:
    """Tests for period type determination."""

    def test_regular_group_monthly(self):
        assert determine_period_type("Kids", "Monthly") == "monthly"

    def test_car_expenses_always_annual(self):
        assert determine_period_type("Car Expenses", "Monthly") == "annual"

    def test_savings_always_annual(self):
        assert determine_period_type("Savings", "Monthly") == "annual"

    def test_sinking_fund_case_insensitive(self):
        assert determine_period_type("car expenses", "anything") == "annual"
        assert determine_period_type("SAVINGS", "anything") == "annual"

    def test_annual_timeline(self):
        assert determine_period_type("Fixed Bills", "Annual") == "annual"

    def test_bi_annual_timeline(self):
        assert determine_period_type("Fixed Bills", "Bi-annual (2×)") == "annual"

    def test_empty_timeline(self):
        assert determine_period_type("Kids", "") == "monthly"

    def test_weekly_timeline_treated_as_monthly(self):
        """Weekly items are imported as monthly equivalents."""
        assert determine_period_type("Kids", "Weekly (52×)") == "monthly"


class TestParseCSV:
    """Tests for CSV parsing."""

    def test_parse_basic_csv(self):
        csv_content = (
            "Group,Category,Monthly Amount,Timeline,Payment Method\n"
            "Kids,Swimming Lessons,£125.00,Monthly,Direct Debit\n"
            "Kids,Piano,£40.00,Termly (3×),Card Payment\n"
        )
        result = parse_csv(csv_content)
        assert result.line_count == 2
        assert "Kids" in result.groups
        assert len(result.groups["Kids"]) == 2
        assert result.groups["Kids"][0].category == "Swimming Lessons"
        assert result.groups["Kids"][0].amount_pence == 12500

    def test_parse_skips_nanny_group(self):
        csv_content = (
            "Group,Category,Monthly Amount,Timeline,Payment Method\n"
            "Nanny,Nanny Salary,£1500.00,Monthly,Standing Order\n"
            "Kids,Swimming,£125.00,Monthly,Direct Debit\n"
        )
        result = parse_csv(csv_content)
        assert "Nanny" not in result.groups
        assert "Nanny" in result.skipped_groups
        assert result.line_count == 1

    def test_parse_sinking_funds(self):
        csv_content = (
            "Group,Category,Monthly Amount,Timeline,Payment Method\n"
            "Car Expenses,Car Tax,£56.25,Annual (October),Direct Debit\n"
            "Car Expenses,Insurance,£54.17,Annual (March),Card Payment\n"
        )
        result = parse_csv(csv_content)
        items = result.groups["Car Expenses"]
        assert all(i.period_type == "annual" for i in items)
        assert items[0].annual_amount_pence == 5625 * 12  # £56.25/month * 12

    def test_parse_savings_as_sinking_funds(self):
        csv_content = (
            "Group,Category,Monthly Amount,Timeline,Payment Method\n"
            "Savings,House Savings,£500.00,Monthly,Standing Order\n"
            "Savings,Holiday Savings,£400.00,Monthly,Standing Order\n"
        )
        result = parse_csv(csv_content)
        items = result.groups["Savings"]
        assert all(i.period_type == "annual" for i in items)

    def test_parse_zero_amounts_flagged(self):
        csv_content = (
            "Group,Category,Monthly Amount,Timeline,Payment Method\n"
            "Kids,Art Club,TBC,Termly (3×),Card Payment\n"
            "Fixed Bills,Gardener,TBC,Fortnightly,TBC\n"
        )
        result = parse_csv(csv_content)
        assert len(result.warnings) == 2
        assert all("£0/TBC" in w for w in result.warnings)

    def test_parse_multiple_groups(self):
        csv_content = (
            "Group,Category,Monthly Amount,Timeline,Payment Method\n"
            "Kids,Swimming,£125.00,Monthly,Direct Debit\n"
            "Fixed Bills,Netflix,£10.00,Monthly,Direct Debit\n"
            "Variable Expenses,Groceries,£650.00,Weekly (52×),Card Payment\n"
        )
        result = parse_csv(csv_content)
        assert len(result.groups) == 3
        assert result.total_monthly_pence == 12500 + 1000 + 65000

    def test_parse_empty_csv(self):
        result = parse_csv("")
        assert result.line_count == 0

    def test_parse_skips_empty_rows(self):
        csv_content = (
            "Group,Category,Monthly Amount,Timeline,Payment Method\n"
            "Kids,Swimming,£125.00,Monthly,Direct Debit\n"
            ",,,,\n"
            "Kids,Piano,£40.00,Termly,Card\n"
        )
        result = parse_csv(csv_content)
        assert result.line_count == 2

    def test_parse_fixed_bills(self):
        """Fixed Bills should be monthly envelopes (not sinking funds)."""
        csv_content = (
            "Group,Category,Monthly Amount,Timeline,Payment Method\n"
            "Fixed Bills,Mortgage (1),£1598.81,Monthly,Direct Debit\n"
            "Fixed Bills,Virgin (broadband),£86.25,Monthly,Direct Debit\n"
        )
        result = parse_csv(csv_content)
        items = result.groups["Fixed Bills"]
        assert all(i.period_type == "monthly" for i in items)

    def test_parse_real_structure(self):
        """Test with a realistic subset of the actual budget structure."""
        csv_content = (
            "Group,Category,Monthly Amount,Timeline,Payment Method\n"
            "Nanny,Nanny Salary,£0,Monthly,Standing Order\n"
            "Kids,Swimming Lessons,£125.00,Monthly,Direct Debit\n"
            "Kids,Elodie Piano,£40.00,Termly (3×),Card Payment\n"
            "Fun & Activities,Days out,£100.00,Monthly,Ad-hoc\n"
            "Fixed Bills,Mortgage (1),£1598.81,Monthly,Direct Debit\n"
            "Fixed Bills,Netflix,£10.00,Monthly,Direct Debit\n"
            "Variable Expenses,Food (groceries),£650.00,Weekly (52×),Card Payment\n"
            "Variable Expenses,Petrol,£100.00,Monthly,Ad-hoc\n"
            "Car Expenses,Car Tax,£56.25,Annual (October),Direct Debit\n"
            "Car Expenses,Insurance,£54.17,Annual (March),Card Payment\n"
            "Savings,House Savings,£500.00,Monthly,Standing Order\n"
            "Savings,Holiday Savings,£400.00,Monthly,Standing Order\n"
            "Emergency Funds,Contingency,£188.45,Monthly,N/A\n"
        )
        result = parse_csv(csv_content)

        # Nanny skipped
        assert "Nanny" not in result.groups
        assert "Nanny" in result.skipped_groups

        # 7 groups imported (excluding Nanny)
        assert len(result.groups) == 7

        # Car Expenses and Savings are sinking funds
        for item in result.groups["Car Expenses"]:
            assert item.period_type == "annual"
        for item in result.groups["Savings"]:
            assert item.period_type == "annual"

        # Regular groups are monthly
        for item in result.groups["Kids"]:
            assert item.period_type == "monthly"
        for item in result.groups["Fixed Bills"]:
            assert item.period_type == "monthly"

        # 12 line items imported (13 minus 1 Nanny)
        assert result.line_count == 12


class TestBudgetImportServicePreview:
    """Tests for the preview method."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session):
        return BudgetImportService(mock_session)

    @pytest.mark.asyncio
    async def test_preview_returns_structure(self, service):
        parsed = ParsedBudget(
            groups={
                "Kids": [
                    ParsedLineItem(
                        group="Kids",
                        category="Swimming",
                        amount_pence=12500,
                        period_type="monthly",
                    ),
                ],
            },
            total_monthly_pence=12500,
            line_count=1,
        )
        preview = await service.preview(uuid.UUID("00000000-0000-0000-0000-000000000001"), parsed)
        assert len(preview["groups"]) == 1
        assert preview["groups"][0]["name"] == "Kids"
        assert preview["groups"][0]["item_count"] == 1
        assert preview["total_line_items"] == 1
        assert preview["total_monthly_pence"] == 12500

    @pytest.mark.asyncio
    async def test_preview_includes_warnings(self, service):
        parsed = ParsedBudget(
            groups={"Kids": [ParsedLineItem(group="Kids", category="Art", amount_pence=0, is_zero=True)]},
            warnings=["Row 2: 'Art' has £0/TBC amount"],
            line_count=1,
        )
        preview = await service.preview(uuid.UUID("00000000-0000-0000-0000-000000000001"), parsed)
        assert len(preview["warnings"]) == 1

    @pytest.mark.asyncio
    async def test_preview_includes_skipped(self, service):
        parsed = ParsedBudget(
            groups={},
            skipped_groups=["Nanny"],
            line_count=0,
        )
        preview = await service.preview(uuid.UUID("00000000-0000-0000-0000-000000000001"), parsed)
        assert "Nanny" in preview["skipped_groups"]


class TestSkipAndSinkingFundConstants:
    """Tests for import configuration constants."""

    def test_nanny_in_skip_groups(self):
        assert "nanny" in SKIP_GROUPS

    def test_car_expenses_is_sinking_fund(self):
        assert "car expenses" in SINKING_FUND_GROUPS

    def test_savings_is_sinking_fund(self):
        assert "savings" in SINKING_FUND_GROUPS


class TestColumnMapping:
    """Tests for flexible column name matching."""

    def test_standard_columns(self):
        csv_content = (
            "Group,Category,Monthly Amount,Timeline,Payment Method\n"
            "Kids,Swimming,£125.00,Monthly,Direct Debit\n"
        )
        result = parse_csv(csv_content)
        assert result.line_count == 1
        assert result.groups["Kids"][0].category == "Swimming"

    def test_alternative_column_names(self):
        csv_content = (
            "Budget Group,Item,Amount,Frequency,Payment\n"
            "Kids,Swimming,£125.00,Monthly,Direct Debit\n"
        )
        result = parse_csv(csv_content)
        assert result.line_count == 1

    def test_case_insensitive_columns(self):
        csv_content = (
            "GROUP,CATEGORY,MONTHLY AMOUNT,TIMELINE,PAYMENT METHOD\n"
            "Kids,Swimming,£125.00,Monthly,Direct Debit\n"
        )
        result = parse_csv(csv_content)
        assert result.line_count == 1
