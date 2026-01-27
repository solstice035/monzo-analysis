"""Slack notification service for budget alerts and summaries."""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def format_currency(amount_pence: int) -> str:
    """Format pence as GBP currency string.

    Args:
        amount_pence: Amount in pence (can be negative)

    Returns:
        Formatted currency string (e.g., "£52.34")
    """
    pounds = abs(amount_pence) / 100
    return f"£{pounds:.2f}"


def format_daily_summary(summary: dict[str, Any]) -> str:
    """Format daily spending summary as Slack message.

    Args:
        summary: Dict with date, total_spend, transaction_count, etc.

    Returns:
        Formatted message string
    """
    total = format_currency(summary["total_spend"])
    count = summary["transaction_count"]
    top_cat = summary["top_category"]
    top_spend = format_currency(summary["top_category_spend"])

    return (
        f"📊 *Daily Summary for {summary['date']}*\n"
        f"Total spent: *{total}* across {count} transactions\n"
        f"Top category: *{top_cat}* ({top_spend})"
    )


def format_budget_warning(budget_status: dict[str, Any]) -> str:
    """Format budget warning message.

    Args:
        budget_status: Dict with category, amount, spent, percentage, remaining

    Returns:
        Formatted warning message
    """
    category = budget_status["category"]
    percentage = budget_status["percentage"]
    remaining = format_currency(budget_status["remaining"])

    return (
        f"⚠️ *Budget Warning: {category}*\n"
        f"You've used *{percentage:.0f}%* of your budget\n"
        f"Remaining: *{remaining}*"
    )


def format_budget_exceeded(budget_status: dict[str, Any]) -> str:
    """Format budget exceeded message.

    Args:
        budget_status: Dict with category, amount, spent, percentage, remaining

    Returns:
        Formatted exceeded message
    """
    category = budget_status["category"]
    percentage = budget_status["percentage"]
    overspend = format_currency(abs(budget_status["remaining"]))

    return (
        f"🚨 *Budget Exceeded: {category}*\n"
        f"You've spent *{percentage:.0f}%* of your budget\n"
        f"Over by: *{overspend}*"
    )


def format_sync_complete(sync_result: dict[str, Any]) -> str:
    """Format sync completion message.

    Args:
        sync_result: Dict with transactions_synced, new_transactions, duration_seconds

    Returns:
        Formatted sync message
    """
    total = sync_result["transactions_synced"]
    new = sync_result["new_transactions"]

    return f"✅ Sync complete: {total} transactions processed ({new} new)"


def create_header_block(text: str) -> dict[str, Any]:
    """Create a Slack header block.

    Args:
        text: Header text

    Returns:
        Header block dict
    """
    return {
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": text,
            "emoji": True,
        },
    }


def create_section_block(text: str) -> dict[str, Any]:
    """Create a Slack section block with markdown.

    Args:
        text: Markdown text content

    Returns:
        Section block dict
    """
    return {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": text,
        },
    }


def create_divider_block() -> dict[str, Any]:
    """Create a Slack divider block.

    Returns:
        Divider block dict
    """
    return {"type": "divider"}


def create_context_block(elements: list[str]) -> dict[str, Any]:
    """Create a Slack context block.

    Args:
        elements: List of text elements

    Returns:
        Context block dict
    """
    return {
        "type": "context",
        "elements": [
            {"type": "mrkdwn", "text": elem} for elem in elements
        ],
    }


class SlackService:
    """Service for sending Slack notifications."""

    def __init__(self, webhook_url: str | None) -> None:
        """Initialize with webhook URL.

        Args:
            webhook_url: Slack incoming webhook URL (can be None to skip sending)
        """
        self._webhook_url = webhook_url

    async def send_message(self, text: str) -> bool:
        """Send a text message to Slack.

        Args:
            text: Message text

        Returns:
            True if sent successfully or skipped, False on failure
        """
        if not self._webhook_url:
            return True  # Skip silently

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self._webhook_url,
                    json={"text": text},
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Slack notification failed: {e}", exc_info=True)
            return False

    async def send_blocks(self, blocks: list[dict[str, Any]], text: str = "") -> bool:
        """Send a rich block message to Slack.

        Args:
            blocks: List of Slack blocks
            text: Fallback text for notifications

        Returns:
            True if sent successfully or skipped, False on failure
        """
        if not self._webhook_url:
            return True  # Skip silently

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self._webhook_url,
                    json={"text": text, "blocks": blocks},
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Slack block notification failed: {e}", exc_info=True)
            return False

    async def notify_daily_summary(
        self,
        date: str,
        total_spend: int,
        transaction_count: int,
        top_category: str,
        top_category_spend: int,
    ) -> bool:
        """Send daily spending summary notification.

        Args:
            date: Summary date
            total_spend: Total spend in pence
            transaction_count: Number of transactions
            top_category: Category with highest spend
            top_category_spend: Spend in top category (pence)

        Returns:
            True if sent successfully
        """
        summary = {
            "date": date,
            "total_spend": total_spend,
            "transaction_count": transaction_count,
            "top_category": top_category,
            "top_category_spend": top_category_spend,
        }
        message = format_daily_summary(summary)
        return await self.send_message(message)

    async def notify_budget_warning(
        self,
        category: str,
        amount: int,
        spent: int,
        percentage: float,
    ) -> bool:
        """Send budget warning notification.

        Args:
            category: Budget category
            amount: Budget amount in pence
            spent: Amount spent in pence
            percentage: Percentage of budget used

        Returns:
            True if sent successfully
        """
        remaining = amount - spent
        budget_status = {
            "category": category,
            "amount": amount,
            "spent": spent,
            "percentage": percentage,
            "remaining": remaining,
        }
        message = format_budget_warning(budget_status)
        return await self.send_message(message)

    async def notify_budget_exceeded(
        self,
        category: str,
        amount: int,
        spent: int,
        percentage: float,
    ) -> bool:
        """Send budget exceeded notification.

        Args:
            category: Budget category
            amount: Budget amount in pence
            spent: Amount spent in pence
            percentage: Percentage of budget used

        Returns:
            True if sent successfully
        """
        remaining = amount - spent
        budget_status = {
            "category": category,
            "amount": amount,
            "spent": spent,
            "percentage": percentage,
            "remaining": remaining,
        }
        message = format_budget_exceeded(budget_status)
        return await self.send_message(message)

    async def notify_sync_complete(
        self,
        transactions_synced: int,
        new_transactions: int,
        duration_seconds: float,
    ) -> bool:
        """Send sync completion notification.

        Args:
            transactions_synced: Total transactions processed
            new_transactions: New transactions added
            duration_seconds: Sync duration

        Returns:
            True if sent successfully
        """
        sync_result = {
            "transactions_synced": transactions_synced,
            "new_transactions": new_transactions,
            "duration_seconds": duration_seconds,
        }
        message = format_sync_complete(sync_result)
        return await self.send_message(message)
