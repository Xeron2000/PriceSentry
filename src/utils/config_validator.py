"""
Configuration validation utilities for PriceSentry system.
Provides comprehensive configuration validation with detailed error reporting.
"""

import logging
import os
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


class ValidationLevel(Enum):
    """Validation severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationResult:
    """Result of a configuration validation."""

    is_valid: bool
    errors: List[str]
    warnings: List[str]
    info: List[str]

    def add_error(self, message: str):
        """Add an error message."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)

    def add_info(self, message: str):
        """Add an info message."""
        self.info.append(message)


@dataclass
class ValidationRule:
    """Configuration validation rule."""

    key_path: str
    required: bool = True
    data_type: type = str
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    min_length: Optional[int] = None
    allowed_values: Optional[List[Any]] = None
    pattern: Optional[str] = None
    custom_validator: Optional[callable] = None
    error_message: Optional[str] = None
    level: ValidationLevel = ValidationLevel.ERROR


class ConfigValidator:
    """Configuration validation system."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.rules: Dict[str, ValidationRule] = {}
        self._setup_validation_rules()

    def _setup_validation_rules(self):
        """Setup validation rules for configuration."""

        # Exchange configuration
        self.rules["exchange"] = ValidationRule(
            key_path="exchange",
            required=True,
            data_type=str,
            allowed_values=["binance", "okx", "bybit"],
            error_message="Exchange must be one of: binance, okx, bybit",
        )

        self.rules["exchanges"] = ValidationRule(
            key_path="exchanges",
            required=True,
            data_type=list,
            custom_validator=self._validate_exchanges_list,
            error_message="Exchanges must be a list of valid exchange names",
        )

        # Timeframe configuration
        self.rules["defaultTimeframe"] = ValidationRule(
            key_path="defaultTimeframe",
            required=True,
            data_type=str,
            allowed_values=["1m", "5m", "15m", "1h", "1d"],
            error_message="Timeframe must be one of: 1m, 5m, 15m, 1h, 1d",
        )

        # Threshold configuration
        self.rules["defaultThreshold"] = ValidationRule(
            key_path="defaultThreshold",
            required=True,
            data_type=(int, float),
            min_value=0.001,
            max_value=100.0,
            error_message="Threshold must be between 0.001 and 100.0",
        )

        # Symbols file path
        self.rules["symbolsFilePath"] = ValidationRule(
            key_path="symbolsFilePath",
            required=True,
            data_type=str,
            custom_validator=self._validate_file_path,
            error_message="Symbols file path must be a valid file path",
        )

        # Notification channels
        self.rules["notificationChannels"] = ValidationRule(
            key_path="notificationChannels",
            required=True,
            data_type=list,
            custom_validator=self._validate_notification_channels,
            error_message=(
                "Notification channels must list supported channels (telegram)"
            ),
        )

        # Telegram configuration
        self.rules["telegram.token"] = ValidationRule(
            key_path="telegram.token",
            required=False,
            data_type=str,
            pattern=r"^\d+:[A-Za-z0-9_-]+$",
            error_message=(
                "Telegram token must be in format: numbers:letters_numbers_symbols"
            ),
        )

        self.rules["telegram.chatId"] = ValidationRule(
            key_path="telegram.chatId",
            required=False,
            data_type=str,
            pattern=r"^-?\d+$",
            error_message="Telegram chat ID must be a numeric string",
        )

        self.rules["telegram.webhookSecret"] = ValidationRule(
            key_path="telegram.webhookSecret",
            required=False,
            data_type=str,
            min_length=6,
            error_message="Telegram webhook secret must be at least 6 characters",
        )

        # Timezone configuration
        self.rules["notificationTimezone"] = ValidationRule(
            key_path="notificationTimezone",
            required=False,
            data_type=str,
            allowed_values=[
                "Asia/Shanghai",
                "America/New_York",
                "Europe/London",
                "UTC",
            ],
            error_message="Timezone must be a valid IANA timezone",
        )

        # Log level configuration
        self.rules["logLevel"] = ValidationRule(
            key_path="logLevel",
            required=False,
            data_type=str,
            allowed_values=["DEBUG", "INFO", "WARNING", "ERROR"],
            error_message="Log level must be one of: DEBUG, INFO, WARNING, ERROR",
        )

        # Volume monitoring configuration
        self.rules["volumeMonitoring"] = ValidationRule(
            key_path="volumeMonitoring",
            required=False,
            data_type=bool,
            error_message="Volume monitoring must be a boolean value",
        )

        self.rules["volumeThreshold"] = ValidationRule(
            key_path="volumeThreshold",
            required=False,
            data_type=(int, float),
            min_value=1,
            max_value=1000,
            error_message="Volume threshold must be between 1 and 1000",
        )

        # Volume sentry configuration
        self.rules["volumeSentry.enabled"] = ValidationRule(
            key_path="volumeSentry.enabled",
            required=False,
            data_type=bool,
            error_message="Volume sentry enabled must be a boolean value",
        )

        self.rules["volumeSentry.threshold"] = ValidationRule(
            key_path="volumeSentry.threshold",
            required=False,
            data_type=(int, float),
            min_value=1,
            max_value=100,
            error_message="Volume sentry threshold must be between 1 and 100",
        )

        # Open interest sentry configuration
        self.rules["openInterestSentry.enabled"] = ValidationRule(
            key_path="openInterestSentry.enabled",
            required=False,
            data_type=bool,
            error_message="Open interest sentry enabled must be a boolean value",
        )

        self.rules["openInterestSentry.threshold"] = ValidationRule(
            key_path="openInterestSentry.threshold",
            required=False,
            data_type=(int, float),
            min_value=1,
            max_value=100,
            error_message="Open interest sentry threshold must be between 1 and 100",
        )

        # Chart configuration
        self.rules["attachChart"] = ValidationRule(
            key_path="attachChart",
            required=False,
            data_type=bool,
            error_message="Attach chart must be a boolean value",
        )

        self.rules["chartTimeframe"] = ValidationRule(
            key_path="chartTimeframe",
            required=False,
            data_type=str,
            allowed_values=["1m", "5m", "15m", "1h", "1d"],
            error_message="Chart timeframe must be one of: 1m, 5m, 15m, 1h, 1d",
        )

        self.rules["chartLookbackMinutes"] = ValidationRule(
            key_path="chartLookbackMinutes",
            required=False,
            data_type=int,
            min_value=5,
            max_value=1440,
            error_message="Chart lookback minutes must be between 5 and 1440",
        )

        self.rules["chartTheme"] = ValidationRule(
            key_path="chartTheme",
            required=False,
            data_type=str,
            allowed_values=["dark", "light"],
            error_message="Chart theme must be either 'dark' or 'light'",
        )

        self.rules["chartIncludeMA"] = ValidationRule(
            key_path="chartIncludeMA",
            required=False,
            data_type=list,
            custom_validator=self._validate_moving_averages,
            error_message="Chart moving averages must be a list of positive integers",
        )

        self.rules["chartImageWidth"] = ValidationRule(
            key_path="chartImageWidth",
            required=False,
            data_type=int,
            min_value=400,
            max_value=4000,
            error_message="Chart image width must be between 400 and 4000 pixels",
        )

        self.rules["chartImageHeight"] = ValidationRule(
            key_path="chartImageHeight",
            required=False,
            data_type=int,
            min_value=300,
            max_value=3000,
            error_message="Chart image height must be between 300 and 3000 pixels",
        )

        self.rules["chartImageScale"] = ValidationRule(
            key_path="chartImageScale",
            required=False,
            data_type=int,
            allowed_values=[1, 2, 3],
            error_message="Chart image scale must be 1, 2, or 3",
        )

        # Security configuration
        self.rules["security.dashboardAccessKey"] = ValidationRule(
            key_path="security.dashboardAccessKey",
            required=False,
            data_type=str,
            min_length=4,
            error_message="Dashboard access key must be at least 4 characters long",
        )

    def _validate_exchanges_list(self, value: List[str]) -> Tuple[bool, str]:
        """Validate exchanges list."""
        if not isinstance(value, list):
            return False, "Exchanges must be a list"

        valid_exchanges = ["binance", "okx", "bybit"]
        for exchange in value:
            if exchange not in valid_exchanges:
                return (
                    False,
                    f"Invalid exchange: {exchange}. Must be one of: {valid_exchanges}",
                )

        return True, ""

    def _validate_notification_channels(self, value: List[str]) -> Tuple[bool, str]:
        """Validate notification channels."""
        if not isinstance(value, list):
            return False, "Notification channels must be a list"

        valid_channels = ["telegram"]
        for channel in value:
            if channel not in valid_channels:
                return (
                    False,
                    (
                        f"Invalid notification channel: {channel}. "
                        f"Must be one of: {valid_channels}"
                    ),
                )

        return True, ""

    def _validate_file_path(self, value: str) -> Tuple[bool, str]:
        """Validate file path exists or can be created."""
        if not isinstance(value, str):
            return False, "File path must be a string"

        try:
            path = Path(value)
            # Check if parent directory exists
            if not path.parent.exists():
                return False, f"Parent directory does not exist: {path.parent}"

            # If file exists, check if it's readable
            if path.exists():
                if not path.is_file():
                    return False, f"Path is not a file: {value}"
                if not os.access(value, os.R_OK):
                    return False, f"File is not readable: {value}"

            return True, ""
        except Exception as e:
            return False, f"Invalid file path: {e}"

    def _validate_moving_averages(self, value: List[int]) -> Tuple[bool, str]:
        """Validate moving averages list."""
        if not isinstance(value, list):
            return False, "Moving averages must be a list"

        for ma in value:
            if not isinstance(ma, int):
                return False, f"Moving average period must be an integer: {ma}"
            if ma <= 0:
                return False, f"Moving average period must be positive: {ma}"
            if ma > 200:
                return False, f"Moving average period too large: {ma}"

        return True, ""

    def get_value_by_path(self, config: Dict[str, Any], key_path: str) -> Any:
        """Get value from config by dot notation path."""
        keys = key_path.split(".")
        value = config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None

        return value

    def validate_type(self, value: Any, expected_type: Union[type, tuple]) -> bool:
        """Validate value type."""
        if isinstance(expected_type, tuple):
            return isinstance(value, expected_type)
        return isinstance(value, expected_type)

    def validate_range(
        self,
        value: Union[int, float],
        min_val: Optional[Union[int, float]],
        max_val: Optional[Union[int, float]],
    ) -> Tuple[bool, str]:
        """Validate numeric range."""
        if min_val is not None and value < min_val:
            return False, f"Value {value} is less than minimum {min_val}"

        if max_val is not None and value > max_val:
            return False, f"Value {value} is greater than maximum {max_val}"

        return True, ""

    def validate_pattern(self, value: str, pattern: str) -> Tuple[bool, str]:
        """Validate string pattern."""
        if not re.match(pattern, value):
            return False, f"Value '{value}' does not match pattern '{pattern}'"
        return True, ""

    def validate_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate entire configuration."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[], info=[])

        for key_path, rule in self.rules.items():
            value = self.get_value_by_path(config, key_path)

            # Check if required field is missing
            if rule.required and value is None:
                error_msg = (
                    rule.error_message or f"Required field '{key_path}' is missing"
                )
                result.add_error(error_msg)
                continue

            # Skip validation if optional field is missing
            if not rule.required and value is None:
                continue

            # Validate data type
            if not self.validate_type(value, rule.data_type):
                expected_type = (
                    rule.data_type.__name__
                    if isinstance(rule.data_type, type)
                    else str(rule.data_type)
                )
                actual_type = type(value).__name__
                error_msg = (
                    f"Field '{key_path}' must be of type {expected_type}, "
                    f"got {actual_type}"
                )
                result.add_error(error_msg)
                continue

            # Validate numeric range
            if isinstance(value, (int, float)) and (
                rule.min_value is not None or rule.max_value is not None
            ):
                is_valid, msg = self.validate_range(
                    value, rule.min_value, rule.max_value
                )
                if not is_valid:
                    result.add_error(f"Field '{key_path}': {msg}")

            # Validate allowed values
            if rule.allowed_values is not None and value not in rule.allowed_values:
                error_msg = (
                    rule.error_message
                    or f"Field '{key_path}' must be one of: {rule.allowed_values}"
                )
                result.add_error(error_msg)

            # Validate pattern
            if rule.pattern is not None and isinstance(value, str):
                is_valid, msg = self.validate_pattern(value, rule.pattern)
                if not is_valid:
                    result.add_error(f"Field '{key_path}': {msg}")

            # Validate string length
            if rule.min_length is not None and isinstance(value, str):
                if len(value) < rule.min_length:
                    result.add_error(
                        (
                            f"Field '{key_path}' must be at least "
                            f"{rule.min_length} characters long"
                        )
                    )

            # Custom validator
            if rule.custom_validator is not None:
                is_valid, msg = rule.custom_validator(value)
                if not is_valid:
                    result.add_error(f"Field '{key_path}': {msg}")

        # Additional cross-field validation
        self._validate_cross_fields(config, result)

        # Log validation results
        if result.errors:
            self.logger.error(
                f"Configuration validation failed with {len(result.errors)} errors"
            )
            for error in result.errors:
                self.logger.error(f"  - {error}")

        if result.warnings:
            self.logger.warning(
                f"Configuration validation has {len(result.warnings)} warnings"
            )
            for warning in result.warnings:
                self.logger.warning(f"  - {warning}")

        if result.info:
            self.logger.info(f"Configuration validation info: {len(result.info)} items")
            for info in result.info:
                self.logger.info(f"  - {info}")

        return result

    def _validate_cross_fields(self, config: Dict[str, Any], result: ValidationResult):
        """Validate cross-field dependencies."""

        # Check if Telegram is enabled but configuration is missing
        notification_channels = self.get_value_by_path(config, "notificationChannels")
        if notification_channels and "telegram" in notification_channels:
            telegram_token = self.get_value_by_path(config, "telegram.token")
            telegram_chat_id = self.get_value_by_path(config, "telegram.chatId")

            if not telegram_token:
                result.add_error("Telegram notifications enabled but token is missing")

            if not telegram_chat_id:
                result.add_info(
                    "Telegram fallback chat ID not configured. Notifications will rely on bound recipients."
                )

        # Check if chart is enabled but configuration is invalid
        attach_chart = self.get_value_by_path(config, "attachChart")
        if attach_chart:
            chart_timeframe = self.get_value_by_path(config, "chartTimeframe")
            chart_lookback = self.get_value_by_path(config, "chartLookbackMinutes")

            if not chart_timeframe:
                result.add_warning(
                    "Chart attachment enabled but timeframe is not configured"
                )

            if not chart_lookback:
                result.add_warning(
                    "Chart attachment enabled but lookback minutes is not configured"
                )

    def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for documentation."""
        schema = {}

        for key_path, rule in self.rules.items():
            keys = key_path.split(".")
            current = schema

            for i, key in enumerate(keys[:-1]):
                if key not in current:
                    current[key] = {}
                current = current[key]

            current[keys[-1]] = {
                "required": rule.required,
                "type": rule.data_type.__name__
                if isinstance(rule.data_type, type)
                else str(rule.data_type),
                "description": rule.error_message or f"Configuration for {key_path}",
                "allowed_values": rule.allowed_values,
                "min_value": rule.min_value,
                "max_value": rule.max_value,
                "pattern": rule.pattern,
            }

        return schema


# Global validator instance
config_validator = ConfigValidator()
