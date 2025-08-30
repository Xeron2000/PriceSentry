"""
Tests for exchanges/base.py - Base exchange functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
import time
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from exchanges.base import BaseExchange


class TestBaseExchange:
    """Test cases for BaseExchange class."""

    def test_init_valid_exchange(self):
        """Test initialization with a valid exchange name."""
        with patch('exchanges.base.ccxt.exchanges', ['binance']), \
             patch('exchanges.base.ccxt.binance') as mock_binance:
            
            mock_exchange = Mock()
            mock_binance.return_value = mock_exchange
            
            exchange = BaseExchange("binance")
            
            assert exchange.exchange_name == "binance"
            assert exchange.exchange == mock_exchange
            assert not exchange.ws_connected
            assert exchange.running is False
            assert exchange.last_prices == {}
            assert exchange.historical_prices == {}
            
            # Verify exchange was initialized with rate limiting
            mock_binance.assert_called_once_with({"enableRateLimit": True})

    def test_init_invalid_exchange(self):
        """Test initialization with an invalid exchange name."""
        with patch('exchanges.base.ccxt.exchanges', ['binance']):
            
            with pytest.raises(ValueError, match="Exchange invalid not supported by ccxt"):
                BaseExchange("invalid")

    def test_init_with_price_cache(self):
        """Test that price cache is properly initialized."""
        with patch('exchanges.base.ccxt.exchanges', ['binance']), \
             patch('exchanges.base.ccxt.binance'):
            
            exchange = BaseExchange("binance")
            
            # Verify price cache exists
            assert hasattr(exchange, 'priceCache')
            assert exchange.priceCache.max_len == 1000
            assert exchange.priceCache.max_age_seconds == 300

    def test_get_current_prices_no_websocket_with_cache(self):
        """Test getting current prices when WebSocket is not connected but cache has data."""
        with patch('exchanges.base.ccxt.exchanges', ['binance']), \
             patch('exchanges.base.ccxt.binance') as mock_binance:
            
            mock_exchange = Mock()
            mock_binance.return_value = mock_exchange
            
            exchange = BaseExchange("binance")
            exchange.ws_connected = False
            
            # Pre-populate cache
            exchange.priceCache['BTC/USDT'] = 50000.0
            
            result = exchange.get_current_prices(['BTC/USDT', 'ETH/USDT'])
            
            assert result['BTC/USDT'] == 50000.0
            # ETH/USDT should trigger API call, but we'll test that separately

    def test_get_current_prices_no_websocket_api_call(self):
        """Test getting current prices when WebSocket is not connected and cache is empty."""
        with patch('exchanges.base.ccxt.exchanges', ['binance']), \
             patch('exchanges.base.ccxt.binance') as mock_binance, \
             patch('exchanges.base.logging') as mock_logging:
            
            mock_exchange = Mock()
            mock_binance.return_value = mock_exchange
            
            # Mock API response
            mock_exchange.fetch_ticker.return_value = {
                'last': 50000.0,
                'symbol': 'BTC/USDT'
            }
            
            exchange = BaseExchange("binance")
            exchange.ws_connected = False
            
            result = exchange.get_current_prices(['BTC/USDT'])
            
            assert result['BTC/USDT'] == 50000.0
            mock_exchange.fetch_ticker.assert_called_once_with('BTC/USDT')
            
            # Verify cache was updated
            assert exchange.priceCache['BTC/USDT'] == 50000.0

    def test_get_current_prices_with_websocket(self):
        """Test getting current prices when WebSocket is connected."""
        with patch('exchanges.base.ccxt.exchanges', ['binance']), \
             patch('exchanges.base.ccxt.binance'):
            
            exchange = BaseExchange("binance")
            exchange.ws_connected = True
            exchange.last_prices = {'BTC/USDT': 50000.0}
            
            result = exchange.get_current_prices(['BTC/USDT'])
            
            assert result['BTC/USDT'] == 50000.0

    def test_get_current_prices_mixed_sources(self):
        """Test getting prices from mixed sources (WebSocket and API)."""
        with patch('exchanges.base.ccxt.exchanges', ['binance']), \
             patch('exchanges.base.ccxt.binance') as mock_binance:
            
            mock_exchange = Mock()
            mock_binance.return_value = mock_exchange
            
            # Mock API response for missing symbol
            mock_exchange.fetch_ticker.return_value = {
                'last': 3000.0,
                'symbol': 'ETH/USDT'
            }
            
            exchange = BaseExchange("binance")
            exchange.ws_connected = True
            exchange.last_prices = {'BTC/USDT': 50000.0}  # From WebSocket
            
            result = exchange.get_current_prices(['BTC/USDT', 'ETH/USDT'])
            
            assert result['BTC/USDT'] == 50000.0  # From WebSocket
            assert result['ETH/USDT'] == 3000.0   # From API

    def test_get_price_minutes_ago_no_websocket(self):
        """Test getting historical prices when WebSocket is not connected."""
        with patch('exchanges.base.ccxt.exchanges', ['binance']), \
             patch('exchanges.base.ccxt.binance') as mock_binance, \
             patch('time.time', return_value=1640995200):
            
            mock_exchange = Mock()
            mock_binance.return_value = mock_exchange
            
            # Mock API response
            mock_exchange.fetch_ohlcv.return_value = [
                [1640995140000, 49900.0, 50100.0, 49800.0, 50000.0, 1000.0]
            ]
            
            exchange = BaseExchange("binance")
            exchange.ws_connected = False
            
            result = exchange.get_price_minutes_ago(['BTC/USDT'], 1)
            
            assert result['BTC/USDT'] == 50000.0
            mock_exchange.fetch_ohlcv.assert_called_once()

    def test_get_price_minutes_ago_with_websocket(self):
        """Test getting historical prices when WebSocket is connected."""
        with patch('exchanges.base.ccxt.exchanges', ['binance']), \
             patch('exchanges.base.ccxt.binance') as mock_binance, \
             patch('time.time', return_value=1640995200):
            
            mock_exchange = Mock()
            mock_binance.return_value = mock_exchange
            
            exchange = BaseExchange("binance")
            exchange.ws_connected = True
            
            # Pre-populate historical data
            target_time = 1640995200000 - 60000  # 1 minute ago
            exchange.historical_prices = {
                'BTC/USDT': [
                    (target_time, 49900.0),
                    (1640995200000, 50000.0)
                ]
            }
            
            result = exchange.get_price_minutes_ago(['BTC/USDT'], 1)
            
            assert result['BTC/USDT'] == 49900.0

    def test_get_price_minutes_ago_fallback_to_api(self):
        """Test fallback to API when historical data is too old."""
        with patch('exchanges.base.ccxt.exchanges', ['binance']), \
             patch('exchanges.base.ccxt.binance') as mock_binance, \
             patch('time.time', return_value=1640995200):
            
            mock_exchange = Mock()
            mock_binance.return_value = mock_exchange
            
            # Mock API response
            mock_exchange.fetch_ohlcv.return_value = [
                [1640995140000, 49900.0, 50100.0, 49800.0, 50000.0, 1000.0]
            ]
            
            exchange = BaseExchange("binance")
            exchange.ws_connected = True
            
            # Pre-populate old historical data (more than 10 minutes old)
            old_time = 1640995200000 - 700000  # More than 10 minutes ago
            exchange.historical_prices = {
                'BTC/USDT': [
                    (old_time, 49000.0)
                ]
            }
            
            result = exchange.get_price_minutes_ago(['BTC/USDT'], 1)
            
            assert result['BTC/USDT'] == 50000.0  # From API
            mock_exchange.fetch_ohlcv.assert_called_once()

    def test_close(self):
        """Test closing the exchange connection."""
        with patch('exchanges.base.ccxt.exchanges', ['binance']), \
             patch('exchanges.base.ccxt.binance') as mock_binance:
            
            mock_exchange = Mock()
            mock_binance.return_value = mock_exchange
            
            exchange = BaseExchange("binance")
            exchange.running = True
            exchange.ws_thread = Mock()
            
            exchange.close()
            
            assert not exchange.running
            exchange.ws_thread.join.assert_called_once_with(timeout=5)
            mock_exchange.close.assert_called_once()

    def test_check_ws_connection_reconnect_needed(self):
        """Test WebSocket reconnection logic."""
        with patch('exchanges.base.ccxt.exchanges', ['binance']), \
             patch('exchanges.base.ccxt.binance') as mock_binance, \
             patch('exchanges.base.logging') as mock_logging:
            
            mock_exchange = Mock()
            mock_binance.return_value = mock_exchange
            
            exchange = BaseExchange("binance")
            exchange.ws_connected = False
            exchange.running = True
            exchange.last_prices = {'BTC/USDT': 50000.0}
            
            # Mock successful reconnection
            with patch.object(exchange, 'start_websocket') as mock_start:
                mock_start.return_value = None
                
                result = exchange.check_ws_connection()
                
                assert result is True
                mock_start.assert_called_once_with(['BTC/USDT'])

    def test_check_ws_connection_no_symbols(self):
        """Test WebSocket reconnection when no symbols are available."""
        with patch('exchanges.base.ccxt.exchanges', ['binance']), \
             patch('exchanges.base.ccxt.binance') as mock_binance, \
             patch('exchanges.base.logging') as mock_logging:
            
            mock_exchange = Mock()
            mock_binance.return_value = mock_exchange
            
            exchange = BaseExchange("binance")
            exchange.ws_connected = False
            exchange.running = True
            exchange.last_prices = {}  # No symbols
            
            result = exchange.check_ws_connection()
            
            assert result is False
            mock_logging.error.assert_called_with("No available symbol list for reconnection")

    def test_check_ws_connection_already_connected(self):
        """Test WebSocket check when already connected."""
        with patch('exchanges.base.ccxt.exchanges', ['binance']), \
             patch('exchanges.base.ccxt.binance'):
            
            exchange = BaseExchange("binance")
            exchange.ws_connected = True
            exchange.running = True
            
            result = exchange.check_ws_connection()
            
            assert result is True

    @pytest.mark.asyncio
    async def test_start_websocket_success(self):
        """Test successful WebSocket startup."""
        with patch('exchanges.base.ccxt.exchanges', ['binance']), \
             patch('exchanges.base.ccxt.binance'), \
             patch('exchanges.base.threading.Thread') as mock_thread, \
             patch('exchanges.base.time.sleep') as mock_sleep, \
             patch('exchanges.base.logging') as mock_logging:
            
            exchange = BaseExchange("binance")
            
            # Mock thread creation
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance
            
            # Simulate WebSocket connection established
            def set_connected(*args, **kwargs):
                exchange.ws_connected = True
            
            mock_thread_instance.start.side_effect = set_connected
            
            exchange.start_websocket(['BTC/USDT'])
            
            assert exchange.running is True
            mock_thread.assert_called_once()
            mock_thread_instance.start.assert_called_once()

    def test_start_websocket_timeout(self):
        """Test WebSocket startup timeout."""
        with patch('exchanges.base.ccxt.exchanges', ['binance']), \
             patch('exchanges.base.ccxt.binance'), \
             patch('exchanges.base.threading.Thread') as mock_thread, \
             patch('exchanges.base.time.sleep') as mock_sleep, \
             patch('exchanges.base.logging') as mock_logging, \
             patch('exchanges.base.time.time', side_effect=[0, 11]):  # Timeout after 11 seconds
            
            exchange = BaseExchange("binance")
            
            # Mock thread creation
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance
            
            with pytest.raises(ConnectionError, match="Failed to establish WebSocket connection"):
                exchange.start_websocket(['BTC/USDT'])

    def test_stop_websocket(self):
        """Test stopping WebSocket connection."""
        with patch('exchanges.base.ccxt.exchanges', ['binance']), \
             patch('exchanges.base.ccxt.binance'), \
             patch('exchanges.base.logging') as mock_logging:
            
            exchange = BaseExchange("binance")
            exchange.running = True
            exchange.ws_thread = Mock()
            
            exchange.stop_websocket()
            
            assert not exchange.running
            exchange.ws_thread.join.assert_called_once_with(timeout=5)

    def test_error_handling_get_current_prices(self):
        """Test error handling in get_current_prices."""
        with patch('exchanges.base.ccxt.exchanges', ['binance']), \
             patch('exchanges.base.ccxt.binance') as mock_binance, \
             patch('exchanges.base.logging') as mock_logging:
            
            mock_exchange = Mock()
            mock_binance.return_value = mock_exchange
            
            # Mock API error
            mock_exchange.fetch_ticker.side_effect = Exception("API Error")
            
            exchange = BaseExchange("binance")
            exchange.ws_connected = False
            
            result = exchange.get_current_prices(['BTC/USDT'])
            
            # Should return empty dict on error
            assert result == {}
            mock_logging.error.assert_called()

    def test_error_handling_get_historical_prices(self):
        """Test error handling in get_price_minutes_ago."""
        with patch('exchanges.base.ccxt.exchanges', ['binance']), \
             patch('exchanges.base.ccxt.binance') as mock_binance, \
             patch('exchanges.base.logging') as mock_logging:
            
            mock_exchange = Mock()
            mock_binance.return_value = mock_exchange
            
            # Mock API error
            mock_exchange.fetch_ohlcv.side_effect = Exception("API Error")
            
            exchange = BaseExchange("binance")
            exchange.ws_connected = False
            
            result = exchange.get_price_minutes_ago(['BTC/USDT'], 1)
            
            # Should return empty dict on error
            assert result == {}
            mock_logging.error.assert_called()