"""
Test cases for configuration validation system.
"""

import os
import tempfile

from utils.config_validator import ValidationResult, config_validator


class TestConfigValidator:
    """Test configuration validation functionality."""

    def test_valid_configuration(self):
        """Test validation of a valid configuration."""
        config = {
            "exchange": "binance",
            "exchanges": ["binance", "okx"],
            "defaultTimeframe": "5m",
            "defaultThreshold": 1.0,
            "symbolsFilePath": "config/symbols.txt",
            "notificationChannels": ["telegram"],
            "telegram": {"token": "123456789:ABCdef123456", "chatId": "123456789"},
            "notificationTimezone": "Asia/Shanghai",
            "logLevel": "INFO",
            "attachChart": True,
            "chartTimeframe": "1m",
            "chartLookbackMinutes": 60,
            "chartTheme": "dark",
            "chartIncludeMA": [7, 25],
            "chartImageWidth": 1600,
            "chartImageHeight": 1200,
            "chartImageScale": 2,
        }

        result = config_validator.validate_config(config)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_missing_required_fields(self):
        """Test validation fails when required fields are missing."""
        config = {}

        result = config_validator.validate_config(config)
        assert not result.is_valid
        assert len(result.errors) > 0

        # Check for specific required field errors
        error_messages = [str(error) for error in result.errors]
        assert any("exchange" in msg.lower() for msg in error_messages)
        assert any("timeframe" in msg.lower() for msg in error_messages)
        assert any("threshold" in msg.lower() for msg in error_messages)

    def test_invalid_exchange(self):
        """Test validation fails with invalid exchange."""
        config = {
            "exchange": "invalid_exchange",
            "exchanges": ["binance", "okx"],
            "defaultTimeframe": "5m",
            "defaultThreshold": 1.0,
            "symbolsFilePath": "config/symbols.txt",
            "notificationChannels": ["telegram"],
        }

        result = config_validator.validate_config(config)
        assert not result.is_valid
        assert any("exchange" in str(error).lower() for error in result.errors)

    def test_invalid_timeframe(self):
        """Test validation fails with invalid timeframe."""
        config = {
            "exchange": "binance",
            "exchanges": ["binance", "okx"],
            "defaultTimeframe": "invalid_timeframe",
            "defaultThreshold": 1.0,
            "symbolsFilePath": "config/symbols.txt",
            "notificationChannels": ["telegram"],
        }

        result = config_validator.validate_config(config)
        assert not result.is_valid
        assert any("timeframe" in str(error).lower() for error in result.errors)

    def test_invalid_threshold_range(self):
        """Test validation fails with threshold out of range."""
        config = {
            "exchange": "binance",
            "exchanges": ["binance", "okx"],
            "defaultTimeframe": "5m",
            "defaultThreshold": 150.0,  # Above max value
            "symbolsFilePath": "config/symbols.txt",
            "notificationChannels": ["telegram"],
        }

        result = config_validator.validate_config(config)
        assert not result.is_valid
        assert any("threshold" in str(error).lower() for error in result.errors)

    def test_invalid_telegram_token(self):
        """Test validation fails with invalid Telegram token."""
        config = {
            "exchange": "binance",
            "exchanges": ["binance", "okx"],
            "defaultTimeframe": "5m",
            "defaultThreshold": 1.0,
            "symbolsFilePath": "config/symbols.txt",
            "notificationChannels": ["telegram"],
            "telegram": {"token": "invalid_token", "chatId": "123456789"},
        }

        result = config_validator.validate_config(config)
        assert not result.is_valid
        assert any(
            "telegram" in str(error).lower() and "token" in str(error).lower()
            for error in result.errors
        )

    def test_invalid_notification_channels(self):
        """Test validation fails with invalid notification channels."""
        config = {
            "exchange": "binance",
            "exchanges": ["binance", "okx"],
            "defaultTimeframe": "5m",
            "defaultThreshold": 1.0,
            "symbolsFilePath": "config/symbols.txt",
            "notificationChannels": ["invalid_channel"],
        }

        result = config_validator.validate_config(config)
        assert not result.is_valid
        assert any(
            "notification" in str(error).lower() and "channel" in str(error).lower()
            for error in result.errors
        )

    def test_telegram_configuration_missing(self):
        """
        Test validation warns when Telegram is enabled but configuration is missing.
        """
        config = {
            "exchange": "binance",
            "exchanges": ["binance", "okx"],
            "defaultTimeframe": "5m",
            "defaultThreshold": 1.0,
            "symbolsFilePath": "config/symbols.txt",
            "notificationChannels": ["telegram"],
            # Missing telegram configuration
        }

        result = config_validator.validate_config(config)
        assert not result.is_valid
        assert any("telegram" in str(error).lower() for error in result.errors)

    def test_invalid_chart_dimensions(self):
        """Test validation fails with invalid chart dimensions."""
        config = {
            "exchange": "binance",
            "exchanges": ["binance", "okx"],
            "defaultTimeframe": "5m",
            "defaultThreshold": 1.0,
            "symbolsFilePath": "config/symbols.txt",
            "notificationChannels": ["telegram"],
            "telegram": {"token": "123456789:ABCdef123456", "chatId": "123456789"},
            "attachChart": True,
            "chartImageWidth": 5000,  # Above max value
            "chartImageHeight": 100,  # Below min value
        }

        result = config_validator.validate_config(config)
        assert not result.is_valid
        assert any("width" in str(error).lower() for error in result.errors)
        assert any("height" in str(error).lower() for error in result.errors)

    def test_invalid_moving_averages(self):
        """Test validation fails with invalid moving averages."""
        config = {
            "exchange": "binance",
            "exchanges": ["binance", "okx"],
            "defaultTimeframe": "5m",
            "defaultThreshold": 1.0,
            "symbolsFilePath": "config/symbols.txt",
            "notificationChannels": ["telegram"],
            "telegram": {"token": "123456789:ABCdef123456", "chatId": "123456789"},
            "chartIncludeMA": [7, -5, 300],  # Invalid values
        }

        result = config_validator.validate_config(config)
        assert not result.is_valid
        assert any("moving" in str(error).lower() for error in result.errors)

    def test_valid_file_path(self):
        """Test validation of valid file path."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            config = {
                "exchange": "binance",
                "exchanges": ["binance", "okx"],
                "defaultTimeframe": "5m",
                "defaultThreshold": 1.0,
                "symbolsFilePath": temp_path,
                "notificationChannels": ["telegram"],
                "telegram": {"token": "123456789:ABCdef123456", "chatId": "123456789"},
            }

            result = config_validator.validate_config(config)
            assert result.is_valid
        finally:
            os.unlink(temp_path)

    def test_invalid_file_path(self):
        """Test validation fails with invalid file path."""
        config = {
            "exchange": "binance",
            "exchanges": ["binance", "okx"],
            "defaultTimeframe": "5m",
            "defaultThreshold": 1.0,
            "symbolsFilePath": "/nonexistent/path/symbols.txt",
            "notificationChannels": ["telegram"],
            "telegram": {"token": "123456789:ABCdef123456", "chatId": "123456789"},
        }

        result = config_validator.validate_config(config)
        assert not result.is_valid
        assert any("file" in str(error).lower() for error in result.errors)

    def test_get_config_schema(self):
        """Test getting configuration schema."""
        schema = config_validator.get_config_schema()

        assert isinstance(schema, dict)
        assert "exchange" in schema
        assert "defaultTimeframe" in schema
        assert "telegram" in schema
        assert "chartImageWidth" in schema

        # Check schema structure
        exchange_schema = schema["exchange"]
        assert "required" in exchange_schema
        assert "type" in exchange_schema
        assert "description" in exchange_schema

    def test_validation_result_add_methods(self):
        """Test ValidationResult add methods."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[], info=[])

        result.add_error("Test error")
        result.add_warning("Test warning")
        result.add_info("Test info")

        assert not result.is_valid
        assert len(result.errors) == 1
        assert len(result.warnings) == 1
        assert len(result.info) == 1
        assert result.errors[0] == "Test error"
        assert result.warnings[0] == "Test warning"
        assert result.info[0] == "Test info"

    def test_partial_valid_configuration(self):
        """Test validation with warnings but no errors."""
        config = {
            "exchange": "binance",
            "exchanges": ["binance", "okx"],
            "defaultTimeframe": "5m",
            "defaultThreshold": 1.0,
            "symbolsFilePath": "config/symbols.txt",
            "notificationChannels": [],  # Empty to avoid requiring telegram config
            "attachChart": True,
            # Missing chart configuration - should generate warnings
        }

        result = config_validator.validate_config(config)
        # This should be valid but with warnings
        assert result.is_valid
        assert len(result.warnings) > 0
        assert any("chart" in str(warning).lower() for warning in result.warnings)
