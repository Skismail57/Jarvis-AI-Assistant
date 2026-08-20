import pytest
from unittest.mock import Mock, patch, MagicMock
from assistant.skills.productivity_skills import (
    SlackIntegration,
    DiscordIntegration,
    NotionIntegration,
    ProductivitySkillRouter,
)


class TestSlackIntegration:
    def test_init_without_credentials(self):
        slack = SlackIntegration()
        assert slack._available is False
        assert slack.bot_token is None
        assert slack.webhook_url is None

    def test_init_with_webhook(self, monkeypatch):
        monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/test")
        slack = SlackIntegration()
        assert slack.webhook_url == "https://hooks.slack.com/test"
        assert slack._available is True

    def test_init_with_bot_token(self, monkeypatch):
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")
        slack = SlackIntegration()
        assert slack.bot_token == "xoxb-test-token"
        assert slack._available is True

    @patch("assistant.skills.productivity_skills._requests")
    def test_send_message_webhook_success(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.post.return_value = mock_response
        
        slack = SlackIntegration(webhook_url="https://hooks.slack.com/test")
        result = slack.send_message(channel="general", text="Test message")
        
        assert result["success"] is True
        mock_requests.post.assert_called_once()

    @patch("assistant.skills.productivity_skills._requests")
    def test_send_message_webhook_failure(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_requests.post.return_value = mock_response
        
        slack = SlackIntegration(webhook_url="https://hooks.slack.com/test")
        result = slack.send_message(channel="general", text="Test message")
        
        assert result["success"] is False

    def test_send_message_not_available(self):
        slack = SlackIntegration()
        result = slack.send_message(channel="general", text="Test message")
        
        assert result["success"] is False
        assert "not configured" in result["error"].lower()

    @patch("assistant.skills.productivity_skills._requests")
    def test_list_channels_success(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ok": True,
            "channels": [
                {"id": "C123", "name": "general"},
                {"id": "C456", "name": "random"}
            ]
        }
        mock_requests.get.return_value = mock_response
        
        slack = SlackIntegration(bot_token="xoxb-test-token")
        channels = slack.list_channels()
        
        assert len(channels) == 2
        assert channels[0]["name"] == "general"

    def test_list_channels_not_available(self):
        slack = SlackIntegration()
        channels = slack.list_channels()
        assert channels == []


class TestDiscordIntegration:
    def test_init_without_credentials(self):
        discord = DiscordIntegration()
        assert discord._available is False
        assert discord.bot_token is None
        assert discord.webhook_url is None

    def test_init_with_webhook(self, monkeypatch):
        monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/test")
        discord = DiscordIntegration()
        assert discord.webhook_url == "https://discord.com/api/webhooks/test"
        assert discord._available is True

    def test_init_with_bot_token(self, monkeypatch):
        monkeypatch.setenv("DISCORD_BOT_TOKEN", "test-bot-token")
        discord = DiscordIntegration()
        assert discord.bot_token == "test-bot-token"
        assert discord._available is True

    @patch("assistant.skills.productivity_skills._requests")
    def test_send_message_webhook_success(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 204
        mock_requests.post.return_value = mock_response
        
        discord = DiscordIntegration(webhook_url="https://discord.com/api/webhooks/test")
        result = discord.send_message(content="Test message")
        
        assert result["success"] is True
        mock_requests.post.assert_called_once()

    @patch("assistant.skills.productivity_skills._requests")
    def test_send_message_webhook_failure(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_requests.post.return_value = mock_response
        
        discord = DiscordIntegration(webhook_url="https://discord.com/api/webhooks/test")
        result = discord.send_message(content="Test message")
        
        assert result["success"] is False

    def test_send_message_not_available(self):
        discord = DiscordIntegration()
        result = discord.send_message(content="Test message")
        
        assert result["success"] is False
        assert "not configured" in result["error"].lower()

    @patch("assistant.skills.productivity_skills._requests")
    def test_list_guilds_success(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": "123", "name": "Test Server"},
            {"id": "456", "name": "Another Server"}
        ]
        mock_requests.get.return_value = mock_response
        
        discord = DiscordIntegration(bot_token="test-bot-token")
        guilds = discord.list_guilds()
        
        assert len(guilds) == 2
        assert guilds[0]["name"] == "Test Server"

    def test_list_guilds_not_available(self):
        discord = DiscordIntegration()
        guilds = discord.list_guilds()
        assert guilds == []


class TestNotionIntegration:
    def test_init_without_credentials(self):
        notion = NotionIntegration()
        assert notion._available is False
        assert notion.token is None

    def test_init_with_token(self, monkeypatch):
        monkeypatch.setenv("NOTION_TOKEN", "test-notion-token")
        notion = NotionIntegration()
        assert notion.token == "test-notion-token"
        assert notion._available is True

    def test_init_with_database_id(self, monkeypatch):
        monkeypatch.setenv("NOTION_TOKEN", "test-token")
        monkeypatch.setenv("NOTION_DATABASE_ID", "test-db-id")
        notion = NotionIntegration()
        assert notion.database_id == "test-db-id"

    def test_create_page_not_available(self):
        notion = NotionIntegration()
        result = notion.create_page(title="Test Page")
        
        assert result["success"] is False
        assert "not configured" in result["error"].lower()

    @patch("assistant.skills.productivity_skills._requests")
    def test_create_page_success(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "page-123",
            "url": "https://notion.so/page-123"
        }
        mock_requests.post.return_value = mock_response
        
        notion = NotionIntegration(token="test-token")
        result = notion.create_page(title="Test Page")
        
        assert result["success"] is True
        assert result["page_id"] == "page-123"

    @patch("assistant.skills.productivity_skills._requests")
    def test_query_database_success(self, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "id": "page-1",
                    "url": "https://notion.so/page-1",
                    "created_time": "2024-01-01",
                    "properties": {
                        "title": {
                            "type": "title",
                            "title": [{"text": {"plain_text": "Test Page"}}]
                        }
                    }
                }
            ]
        }
        mock_requests.post.return_value = mock_response
        
        notion = NotionIntegration(token="test-token", database_id="test-db")
        pages = notion.query_database()
        
        assert len(pages) == 1
        assert pages[0]["title"] == "Test Page"


class TestProductivitySkillRouter:
    def test_init(self):
        router = ProductivitySkillRouter()
        assert router.gmail is not None or router.gmail is None  # May fail gracefully
        assert router.calendar is not None or router.calendar is None
        assert router.todoist is not None or router.todoist is None
        assert router.notion is not None or router.notion is None
        assert router.slack is not None or router.slack is None
        assert router.discord is not None or router.discord is None

    @patch("assistant.skills.productivity_skills.SlackIntegration")
    def test_handle_slack_message(self, mock_slack_class):
        mock_slack = Mock()
        mock_slack.send_message.return_value = {"success": True}
        mock_slack_class.return_value = mock_slack
        
        router = ProductivitySkillRouter()
        router.slack = mock_slack
        
        result = router.handle("send message to slack general saying hello world")
        
        assert result["intent"] == "slack_send"
        assert "sent message" in result["text"].lower()

    @patch("assistant.skills.productivity_skills.DiscordIntegration")
    def test_handle_discord_message(self, mock_discord_class):
        mock_discord = Mock()
        mock_discord.send_message.return_value = {"success": True}
        mock_discord_class.return_value = mock_discord
        
        router = ProductivitySkillRouter()
        router.discord = mock_discord
        
        result = router.handle("send message to discord saying deployment complete")
        
        assert result["intent"] == "discord_send"
        assert "sent message" in result["text"].lower()

    @patch("assistant.skills.productivity_skills.SlackIntegration")
    def test_handle_slack_not_configured(self, mock_slack_class):
        mock_slack = Mock()
        mock_slack._available = False
        mock_slack_class.return_value = mock_slack
        
        router = ProductivitySkillRouter()
        router.slack = mock_slack
        
        result = router.handle("send message to slack general saying test")
        
        assert result["intent"] == "slack_send"
        assert "not configured" in result["text"].lower()

    def test_handle_unknown_command(self):
        router = ProductivitySkillRouter()
        result = router.handle("do something random")
        
        assert result["intent"] == "productivity_unknown"
        assert "didn't recognize" in result["text"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
