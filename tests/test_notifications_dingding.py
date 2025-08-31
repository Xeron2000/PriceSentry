"""
Tests for notifications/dingding.py - DingDing notification service.
"""

import os
import sys
from unittest.mock import Mock, patch

import requests

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from notifications.dingding import send_dingding_message


class TestDingDingNotification:
    """Test cases for DingDing notification functions."""

    def test_send_dingding_message_success(self):
        """Test successful DingDing message sending."""
        with patch("notifications.dingding.requests.post") as mock_post:
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            result = send_dingding_message(
                "Test message",
                "https://oapi.dingtalk.com/robot/send?access_token=test_token",
            )

            assert result is True
            mock_post.assert_called_once()

            # Verify the call parameters
            call_args = mock_post.call_args
            assert call_args[1]["json"]["msgtype"] == "text"
            assert call_args[1]["json"]["text"]["content"] == "Test message"
            assert call_args[1]["headers"]["Content-Type"] == "application/json"

    def test_send_dingding_message_missing_webhook(self):
        """Test DingDing message sending with missing webhook URL."""
        with patch("notifications.dingding.requests.post") as mock_post:
            with patch("builtins.print") as mock_print:
                result = send_dingding_message(
                    "Test message",
                    "",  # Empty webhook URL
                )

                assert result is False
                mock_post.assert_not_called()
                mock_print.assert_called_with("DingDing webhook URL is missing.")

    def test_send_dingding_message_api_error(self):
        """Test DingDing message sending with API error."""
        with patch("notifications.dingding.requests.post") as mock_post:
            with patch("builtins.print") as mock_print:
                # Mock error response
                mock_response = Mock()
                mock_response.status_code = 400
                mock_response.text = "Bad Request"
                mock_post.return_value = mock_response

                result = send_dingding_message(
                    "Test message",
                    "https://oapi.dingtalk.com/robot/send?access_token=test_token",
                )

                assert result is False
                mock_print.assert_called_with("Failed to send message: Bad Request")

    def test_send_dingding_message_network_error(self):
        """Test DingDing message sending with network error."""
        with patch("notifications.dingding.requests.post") as mock_post:
            with patch("builtins.print") as mock_print:
                # Mock network error
                mock_post.side_effect = requests.RequestException("Network error")

                result = send_dingding_message(
                    "Test message",
                    "https://oapi.dingtalk.com/robot/send?access_token=test_token",
                )

                assert result is False
                mock_print.assert_called_with(
                    "Error while sending DingDing message: Network error"
                )

    def test_send_dingding_message_with_secret(self):
        """Test DingDing message sending with secret."""
        with patch("notifications.dingding.requests.post") as mock_post, patch(
            "notifications.dingding.time.time", return_value=1640995200
        ), patch("notifications.dingding.hmac.new") as mock_hmac, patch(
            "notifications.dingding.base64.b64encode"
        ) as mock_b64encode, patch(
            "notifications.dingding.urllib.parse.quote_plus"
        ) as mock_quote_plus:
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            # Mock HMAC and encoding
            mock_hmac.return_value.digest.return_value = b"mock_signature"
            mock_b64encode.return_value = b"mock_b64_signature"
            mock_quote_plus.return_value = "mock_url_encoded_signature"

            result = send_dingding_message(
                "Test message",
                "https://oapi.dingtalk.com/robot/send?access_token=test_token",
                "test_secret",
            )

            assert result is True
            mock_post.assert_called_once()

            # Verify the webhook URL includes timestamp and signature
            call_args = mock_post.call_args
            webhook_url = call_args[0][0]
            assert "timestamp=1640995200000" in webhook_url
            assert "sign=mock_url_encoded_signature" in webhook_url

    def test_send_dingding_message_signature_generation(self):
        """Test DingDing message signature generation."""
        with patch("notifications.dingding.requests.post") as mock_post, patch(
            "notifications.dingding.time.time", return_value=1640995200
        ):
            # Mock HMAC calculation
            mock_hmac_instance = Mock()
            mock_hmac_instance.digest.return_value = b"test_signature_bytes"

            mock_hmac_new = Mock(return_value=mock_hmac_instance)

            with patch("notifications.dingding.hmac.new", mock_hmac_new), patch(
                "notifications.dingding.base64.b64encode",
                return_value=b"dGVzdF9zaWduYXR1cmU=",
            ), patch(
                "notifications.dingding.urllib.parse.quote_plus",
                return_value="test_signature_encoded",
            ):
                # Mock successful response
                mock_response = Mock()
                mock_response.status_code = 200
                mock_post.return_value = mock_response

                result = send_dingding_message(
                    "Test message",
                    "https://oapi.dingtalk.com/robot/send?access_token=test_token",
                    "test_secret",
                )

                assert result is True

                # Verify HMAC was called with correct parameters
                mock_hmac_new.assert_called_once()
                call_args = mock_hmac_new.call_args
                assert call_args[0][0] == b"test_secret"
                assert call_args[0][1] == b"1640995200000\ntest_secret"
                assert call_args[1]["digestmod"].__name__ == "openssl_sha256"

    def test_send_dingding_message_long_text(self):
        """Test DingDing message sending with long text."""
        with patch("notifications.dingding.requests.post") as mock_post:
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            long_message = "A" * 1000  # 1000 character message
            result = send_dingding_message(
                long_message,
                "https://oapi.dingtalk.com/robot/send?access_token=test_token",
            )

            assert result is True
            call_args = mock_post.call_args
            assert call_args[1]["json"]["text"]["content"] == long_message

    def test_send_dingding_message_special_characters(self):
        """Test DingDing message sending with special characters."""
        with patch("notifications.dingding.requests.post") as mock_post:
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            message = "Price 🚀 UP! BTC: ¥50,000.00"
            result = send_dingding_message(
                message, "https://oapi.dingtalk.com/robot/send?access_token=test_token"
            )

            assert result is True
            call_args = mock_post.call_args
            assert call_args[1]["json"]["text"]["content"] == message

    def test_send_dingding_message_empty_message(self):
        """Test DingDing message sending with empty message."""
        with patch("notifications.dingding.requests.post") as mock_post:
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            result = send_dingding_message(
                "",  # Empty message
                "https://oapi.dingtalk.com/robot/send?access_token=test_token",
            )

            assert result is True
            call_args = mock_post.call_args
            assert call_args[1]["json"]["text"]["content"] == ""

    def test_send_dingding_message_whitespace_message(self):
        """Test DingDing message sending with whitespace-only message."""
        with patch("notifications.dingding.requests.post") as mock_post:
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            result = send_dingding_message(
                "   ",  # Whitespace-only message
                "https://oapi.dingtalk.com/robot/send?access_token=test_token",
            )

            assert result is True
            call_args = mock_post.call_args
            assert call_args[1]["json"]["text"]["content"] == "   "

    def test_send_dingding_message_json_payload_structure(self):
        """Test DingDing message JSON payload structure."""
        with patch("notifications.dingding.requests.post") as mock_post:
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            result = send_dingding_message(
                "Test message",
                "https://oapi.dingtalk.com/robot/send?access_token=test_token",
            )

            assert result is True
            call_args = mock_post.call_args

            # Verify JSON structure
            payload = call_args[1]["json"]
            assert payload["msgtype"] == "text"
            assert "text" in payload
            assert "content" in payload["text"]
            assert payload["text"]["content"] == "Test message"

    def test_send_dingding_message_headers(self):
        """Test DingDing message HTTP headers."""
        with patch("notifications.dingding.requests.post") as mock_post:
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            result = send_dingding_message(
                "Test message",
                "https://oapi.dingtalk.com/robot/send?access_token=test_token",
            )

            assert result is True
            call_args = mock_post.call_args

            # Verify headers
            headers = call_args[1]["headers"]
            assert headers["Content-Type"] == "application/json"

    def test_send_dingding_message_url_encoding(self):
        """Test DingDing message URL encoding with special characters."""
        with patch("notifications.dingding.requests.post") as mock_post, patch(
            "notifications.dingding.time.time", return_value=1640995200
        ):
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            # Mock signature generation
            with patch("notifications.dingding.hmac.new") as mock_hmac, patch(
                "notifications.dingding.base64.b64encode"
            ) as mock_b64encode, patch(
                "notifications.dingding.urllib.parse.quote_plus"
            ) as mock_quote_plus:
                mock_hmac.return_value.digest.return_value = b"mock_signature"
                mock_b64encode.return_value = b"mock_b64_signature"
                mock_quote_plus.return_value = "mock_url_encoded_signature"

                result = send_dingding_message(
                    "Test message",
                    "https://oapi.dingtalk.com/robot/send?access_token=test_token",
                    "test_secret",
                )

                assert result is True

                # Verify URL encoding was called
                mock_quote_plus.assert_called_once()

    def test_send_dingding_message_timestamp_precision(self):
        """Test DingDing message timestamp precision."""
        with patch("notifications.dingding.requests.post") as mock_post, patch(
            "notifications.dingding.time.time", return_value=1640995200.123
        ):
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            with patch("notifications.dingding.hmac.new") as mock_hmac, patch(
                "notifications.dingding.base64.b64encode"
            ) as mock_b64encode, patch(
                "notifications.dingding.urllib.parse.quote_plus"
            ) as mock_quote_plus:
                mock_hmac.return_value.digest.return_value = b"mock_signature"
                mock_b64encode.return_value = b"mock_b64_signature"
                mock_quote_plus.return_value = "mock_url_encoded_signature"

                result = send_dingding_message(
                    "Test message",
                    "https://oapi.dingtalk.com/robot/send?access_token=test_token",
                    "test_secret",
                )

                assert result is True

                # Verify timestamp was rounded to milliseconds
                call_args = mock_post.call_args
                webhook_url = call_args[0][0]
                assert "timestamp=1640995200123" in webhook_url
