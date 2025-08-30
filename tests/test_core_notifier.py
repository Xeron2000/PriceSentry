"""
Tests for core/notifier.py - Notification system.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.notifier import Notifier


class TestNotifier:
    """Test cases for Notifier class."""

    def test_init_basic(self, sample_config):
        """Test basic initialization of Notifier."""
        notifier = Notifier(sample_config)
        
        assert notifier.notification_channels == sample_config.get("notificationChannels", [])
        assert notifier.telegram_config == sample_config.get("telegram", {})
        assert notifier.dingding_config == sample_config.get("dingding", {})

    def test_init_with_empty_config(self):
        """Test initialization with empty configuration."""
        empty_config = {}
        notifier = Notifier(empty_config)
        
        assert notifier.notification_channels == []
        assert notifier.telegram_config == {}
        assert notifier.dingding_config == {}

    def test_init_with_full_config(self):
        """Test initialization with full configuration."""
        full_config = {
            "notificationChannels": ["telegram", "dingding"],
            "telegram": {
                "enabled": True,
                "token": "test_token",
                "chat_id": "test_chat_id"
            },
            "dingding": {
                "enabled": True,
                "webhook": "test_webhook"
            }
        }
        
        notifier = Notifier(full_config)
        
        assert notifier.notification_channels == ["telegram", "dingding"]
        assert notifier.telegram_config == {
            "enabled": True,
            "token": "test_token",
            "chat_id": "test_chat_id"
        }
        assert notifier.dingding_config == {
            "enabled": True,
            "webhook": "test_webhook"
        }

    def test_send_with_message_only(self, sample_config):
        """Test send method with only text message."""
        with patch('core.notifier.send_notifications') as mock_send_notifications:
            notifier = Notifier(sample_config)
            notifier.send("Test message")
            
            mock_send_notifications.assert_called_once_with(
                "Test message",
                sample_config.get("notificationChannels", []),
                sample_config.get("telegram", {}),
                sample_config.get("dingding", {}),
                image_bytes=None,
                image_caption=None,
                dingding_image_url=None
            )

    def test_send_with_image(self, sample_config):
        """Test send method with image bytes."""
        with patch('core.notifier.send_notifications') as mock_send_notifications:
            notifier = Notifier(sample_config)
            image_bytes = b"fake_image_data"
            image_caption = "Test caption"
            
            notifier.send("Test message with image", 
                         image_bytes=image_bytes, 
                         image_caption=image_caption)
            
            mock_send_notifications.assert_called_once_with(
                "Test message with image",
                sample_config.get("notificationChannels", []),
                sample_config.get("telegram", {}),
                sample_config.get("dingding", {}),
                image_bytes=image_bytes,
                image_caption=image_caption,
                dingding_image_url=None
            )

    def test_send_with_dingding_image_url(self, sample_config):
        """Test send method with DingDing image URL."""
        with patch('core.notifier.send_notifications') as mock_send_notifications:
            notifier = Notifier(sample_config)
            dingding_image_url = "https://example.com/image.jpg"
            
            notifier.send("Test message with DingDing image", 
                         dingding_image_url=dingding_image_url)
            
            mock_send_notifications.assert_called_once_with(
                "Test message with DingDing image",
                sample_config.get("notificationChannels", []),
                sample_config.get("telegram", {}),
                sample_config.get("dingding", {}),
                image_bytes=None,
                image_caption=None,
                dingding_image_url=dingding_image_url
            )

    def test_send_with_all_parameters(self, sample_config):
        """Test send method with all parameters."""
        with patch('core.notifier.send_notifications') as mock_send_notifications:
            notifier = Notifier(sample_config)
            image_bytes = b"fake_image_data"
            image_caption = "Test caption"
            dingding_image_url = "https://example.com/image.jpg"
            
            notifier.send("Complete message", 
                         image_bytes=image_bytes, 
                         image_caption=image_caption,
                         dingding_image_url=dingding_image_url)
            
            mock_send_notifications.assert_called_once_with(
                "Complete message",
                sample_config.get("notificationChannels", []),
                sample_config.get("telegram", {}),
                sample_config.get("dingding", {}),
                image_bytes=image_bytes,
                image_caption=image_caption,
                dingding_image_url=dingding_image_url
            )

    def test_send_with_empty_message(self, sample_config):
        """Test send method with empty message."""
        with patch('core.notifier.send_notifications') as mock_send_notifications:
            notifier = Notifier(sample_config)
            
            # Empty message should not trigger send_notifications
            notifier.send("")
            
            # Verify send_notifications was not called
            mock_send_notifications.assert_not_called()

    def test_send_with_none_message(self, sample_config):
        """Test send method with None message."""
        with patch('core.notifier.send_notifications') as mock_send_notifications:
            notifier = Notifier(sample_config)
            
            # None message should not trigger send_notifications
            notifier.send(None)
            
            # Verify send_notifications was not called
            mock_send_notifications.assert_not_called()

    def test_send_with_whitespace_message(self, sample_config):
        """Test send method with whitespace-only message."""
        with patch('core.notifier.send_notifications') as mock_send_notifications:
            notifier = Notifier(sample_config)
            
            # Whitespace-only message should not trigger send_notifications
            notifier.send("   ")
            
            # Verify send_notifications was not called
            mock_send_notifications.assert_not_called()

    def test_send_exception_handling(self, sample_config):
        """Test send method exception handling."""
        with patch('core.notifier.send_notifications', side_effect=Exception("Network error")):
            notifier = Notifier(sample_config)
            
            # Should not raise exception, but handle it gracefully
            notifier.send("Test message")
            
            # Test passes if no exception is raised

    def test_send_notifications_called_with_correct_channels(self):
        """Test that send_notifications is called with correct channels."""
        config = {
            "notificationChannels": ["telegram"],
            "telegram": {"enabled": True},
            "dingding": {"enabled": False}
        }
        
        with patch('core.notifier.send_notifications') as mock_send_notifications:
            notifier = Notifier(config)
            notifier.send("Test message")
            
            # Verify that the correct channels are passed
            args = mock_send_notifications.call_args[0]
            assert args[1] == ["telegram"]  # notification_channels
            assert args[2] == {"enabled": True}  # telegram_config
            assert args[3] == {"enabled": False}  # dingding_config