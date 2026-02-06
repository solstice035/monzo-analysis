"""Tests for Slack notification service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestSlackMessageFormatting:
    """Tests for formatting Slack messages."""

    def test_format_daily_summary_message(self) -> None:
        """Should format daily summary with spending stats."""
        from app.services.slack import format_daily_summary

        summary = {
            "date": "2025-01-18",
            "total_spend": 5234,  # £52.34
            "transaction_count": 7,
            "top_category": "Groceries",
            "top_category_spend": 2500,  # £25.00
        }

        message = format_daily_summary(summary)

        assert "£52.34" in message
        assert "7 transactions" in message
        assert "Groceries" in message

    def test_format_budget_warning_message(self) -> None:
        """Should format budget warning with percentage."""
        from app.services.slack import format_budget_warning

        budget_status = {
            "category": "Eating Out",
            "amount": 20000,  # £200
            "spent": 18000,  # £180
            "percentage": 90.0,
            "remaining": 2000,  # £20
        }

        message = format_budget_warning(budget_status)

        assert "Eating Out" in message
        assert "90%" in message
        assert "£20" in message
        assert "warning" in message.lower() or "⚠️" in message

    def test_format_budget_exceeded_message(self) -> None:
        """Should format budget exceeded with overspend amount."""
        from app.services.slack import format_budget_exceeded

        budget_status = {
            "category": "Entertainment",
            "amount": 10000,  # £100
            "spent": 12500,  # £125
            "percentage": 125.0,
            "remaining": -2500,  # -£25 (overspent)
        }

        message = format_budget_exceeded(budget_status)

        assert "Entertainment" in message
        assert "125%" in message
        assert "£25" in message  # Overspend amount
        assert "exceeded" in message.lower() or "🚨" in message

    def test_format_sync_complete_message(self) -> None:
        """Should format sync completion with transaction count."""
        from app.services.slack import format_sync_complete

        sync_result = {
            "transactions_synced": 42,
            "new_transactions": 5,
            "duration_seconds": 3.2,
        }

        message = format_sync_complete(sync_result)

        assert "42" in message
        assert "5 new" in message.lower()


class TestSlackWebhook:
    """Tests for sending messages to Slack webhook."""

    @pytest.mark.asyncio
    async def test_send_message_posts_to_webhook(self) -> None:
        """Should POST message payload to configured webhook URL."""
        from app.services.slack import SlackService

        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with patch("httpx.AsyncClient") as MockAsyncClient:
            MockAsyncClient.return_value.__aenter__.return_value = mock_client
            MockAsyncClient.return_value.__aexit__.return_value = None

            service = SlackService(webhook_url="https://hooks.slack.com/test")
            result = await service.send_message("Test message")

            assert result is True
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args.args[0] == "https://hooks.slack.com/test"
            assert "text" in call_args.kwargs.get("json", {})

    @pytest.mark.asyncio
    async def test_send_message_handles_failure(self) -> None:
        """Should return False on webhook failure."""
        from app.services.slack import SlackService

        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with patch("httpx.AsyncClient") as MockAsyncClient:
            MockAsyncClient.return_value.__aenter__.return_value = mock_client
            MockAsyncClient.return_value.__aexit__.return_value = None

            service = SlackService(webhook_url="https://hooks.slack.com/test")
            result = await service.send_message("Test message")

            assert result is False

    @pytest.mark.asyncio
    async def test_send_message_handles_exception(self) -> None:
        """Should return False on network exception."""
        from app.services.slack import SlackService

        mock_client = AsyncMock()
        mock_client.post.side_effect = Exception("Network error")

        with patch("httpx.AsyncClient") as MockAsyncClient:
            MockAsyncClient.return_value.__aenter__.return_value = mock_client
            MockAsyncClient.return_value.__aexit__.return_value = None

            service = SlackService(webhook_url="https://hooks.slack.com/test")
            result = await service.send_message("Test message")

            assert result is False

    @pytest.mark.asyncio
    async def test_send_message_skipped_without_webhook(self) -> None:
        """Should skip sending when webhook URL is None."""
        from app.services.slack import SlackService

        service = SlackService(webhook_url=None)
        result = await service.send_message("Test message")

        # No error, just skipped
        assert result is True


class TestSlackBlockFormatting:
    """Tests for rich Slack block formatting."""

    def test_create_header_block(self) -> None:
        """Should create header block with text."""
        from app.services.slack import create_header_block

        block = create_header_block("Daily Summary")

        assert block["type"] == "header"
        assert "Daily Summary" in block["text"]["text"]

    def test_create_section_block(self) -> None:
        """Should create section block with markdown text."""
        from app.services.slack import create_section_block

        block = create_section_block("*Bold* and _italic_")

        assert block["type"] == "section"
        assert block["text"]["type"] == "mrkdwn"

    def test_create_divider_block(self) -> None:
        """Should create divider block."""
        from app.services.slack import create_divider_block

        block = create_divider_block()

        assert block["type"] == "divider"

    def test_create_context_block(self) -> None:
        """Should create context block with elements."""
        from app.services.slack import create_context_block

        block = create_context_block(["Last synced: 10:00 AM", "7 transactions"])

        assert block["type"] == "context"
        assert len(block["elements"]) == 2


class TestSlackAuthExpired:
    """Tests for auth expired notification."""

    @pytest.mark.asyncio
    async def test_notify_auth_expired_sends_message(self) -> None:
        """Should send auth expired notification with error details."""
        from app.services.slack import SlackService

        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with patch("httpx.AsyncClient") as MockAsyncClient:
            MockAsyncClient.return_value.__aenter__.return_value = mock_client
            MockAsyncClient.return_value.__aexit__.return_value = None

            service = SlackService(webhook_url="https://hooks.slack.com/test")
            result = await service.notify_auth_expired(error="Invalid refresh token")

            assert result is True
            call_args = mock_client.post.call_args
            message_text = call_args.kwargs["json"]["text"]
            assert "Authentication Expired" in message_text
            assert "Invalid refresh token" in message_text


class TestSlackServiceIntegration:
    """Integration tests for Slack notification workflows."""

    @pytest.mark.asyncio
    async def test_notify_daily_summary(self) -> None:
        """Should send formatted daily summary notification."""
        from app.services.slack import SlackService

        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with patch("httpx.AsyncClient") as MockAsyncClient:
            MockAsyncClient.return_value.__aenter__.return_value = mock_client
            MockAsyncClient.return_value.__aexit__.return_value = None

            service = SlackService(webhook_url="https://hooks.slack.com/test")
            result = await service.notify_daily_summary(
                date="2025-01-18",
                total_spend=5234,
                transaction_count=7,
                top_category="Groceries",
                top_category_spend=2500,
            )

            assert result is True
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_notify_budget_warning(self) -> None:
        """Should send budget warning notification."""
        from app.services.slack import SlackService

        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with patch("httpx.AsyncClient") as MockAsyncClient:
            MockAsyncClient.return_value.__aenter__.return_value = mock_client
            MockAsyncClient.return_value.__aexit__.return_value = None

            service = SlackService(webhook_url="https://hooks.slack.com/test")
            result = await service.notify_budget_warning(
                category="Eating Out",
                amount=20000,
                spent=18000,
                percentage=90.0,
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_notify_budget_exceeded(self) -> None:
        """Should send budget exceeded notification."""
        from app.services.slack import SlackService

        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with patch("httpx.AsyncClient") as MockAsyncClient:
            MockAsyncClient.return_value.__aenter__.return_value = mock_client
            MockAsyncClient.return_value.__aexit__.return_value = None

            service = SlackService(webhook_url="https://hooks.slack.com/test")
            result = await service.notify_budget_exceeded(
                category="Entertainment",
                amount=10000,
                spent=12500,
                percentage=125.0,
            )

            assert result is True
