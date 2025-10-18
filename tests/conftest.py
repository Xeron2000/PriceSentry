"""
Pytest configuration and shared fixtures for PriceSentry tests.
"""

from unittest.mock import MagicMock

import pytest
import yaml



@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "exchange": "binance",
        "defaultTimeframe": "5m",
        "checkInterval": "5m",
        "defaultThreshold": 2.0,
        "notificationChannels": ["telegram"],
        "notificationTimezone": "Asia/Shanghai",
        "notificationSymbols": ["BTC/USDT:USDT"],
        "telegram": {
            "token": "1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijk",
            "chatId": "123456789",
        },
    }


@pytest.fixture
def mock_exchange():
    """Mock exchange instance for testing."""
    mock_exchange = MagicMock()
    mock_exchange.get_price.return_value = 50000.0
    mock_exchange.get_klines.return_value = [
        [1640995200000, 50000.0, 50100.0, 49900.0, 50050.0, 1000.0],
        [1640995260000, 50050.0, 50200.0, 50000.0, 50150.0, 1200.0],
    ]
    return mock_exchange


@pytest.fixture
def mock_notifier():
    """Mock notifier instance for testing."""
    mock_notifier = MagicMock()
    mock_notifier.send_notification.return_value = True
    return mock_notifier


@pytest.fixture
def sample_symbols():
    """Sample trading symbols for testing."""
    return ["BTC/USDT", "ETH/USDT", "BNB/USDT"]


@pytest.fixture
def temp_config_file(tmp_path, sample_config):
    """Create a temporary config file for testing."""
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(sample_config, f)
    return str(config_file)


@pytest.fixture
def temp_symbols_file(tmp_path, sample_symbols):
    """Create a temporary symbols file for testing."""
    symbols_file = tmp_path / "symbols.txt"
    with open(symbols_file, "w") as f:
        for symbol in sample_symbols:
            f.write(f"{symbol}\n")
    return str(symbols_file)
