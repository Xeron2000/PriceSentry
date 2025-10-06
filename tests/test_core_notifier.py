"""Tests for core/notifier.py - Notification system."""

from unittest.mock import patch

from core.notifier import Notifier


class TestNotifier:
    """Test cases for Notifier class."""

    def test_init_basic(self, sample_config):
        notifier = Notifier(sample_config)

        assert notifier.notification_channels == ["telegram"]
        assert notifier.telegram_config == sample_config.get("telegram", {})

    def test_init_with_empty_config(self):
        notifier = Notifier({})

        assert notifier.notification_channels == []
        assert notifier.telegram_config == {}

    def test_send_with_message_only(self, sample_config):
        with patch("core.notifier.send_notifications") as mock_send_notifications:
            notifier = Notifier(sample_config)
            notifier.send("Test message")

            mock_send_notifications.assert_called_once_with(
                "Test message",
                ["telegram"],
                sample_config.get("telegram", {}),
                image_bytes=None,
                image_caption=None,
            )

    def test_send_with_image(self, sample_config):
        with patch("core.notifier.send_notifications") as mock_send_notifications:
            notifier = Notifier(sample_config)
            image_bytes = b"fake_image_data"
            image_caption = "Test caption"

            notifier.send(
                "Test message with image",
                image_bytes=image_bytes,
                image_caption=image_caption,
            )

            mock_send_notifications.assert_called_once_with(
                "Test message with image",
                ["telegram"],
                sample_config.get("telegram", {}),
                image_bytes=image_bytes,
                image_caption=image_caption,
            )

    def test_send_ignores_empty_messages(self, sample_config):
        with patch("core.notifier.send_notifications") as mock_send_notifications:
            notifier = Notifier(sample_config)

            notifier.send("")
            notifier.send(None)
            notifier.send("   ")

            mock_send_notifications.assert_not_called()

    def test_send_handles_exception(self, sample_config):
        with patch(
            "core.notifier.send_notifications", side_effect=Exception("Network error")
        ):
            notifier = Notifier(sample_config)

            notifier.send("Test message")
            # Should not raise despite underlying exception
