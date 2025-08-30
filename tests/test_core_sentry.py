"""
Tests for core/sentry.py - PriceSentry main controller.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.sentry import PriceSentry


class TestPriceSentry:
    """Test cases for PriceSentry main controller."""

    def test_init_basic(self, sample_config, mock_exchange, mock_notifier):
        """Test basic initialization of PriceSentry."""
        with patch('core.sentry.load_config', return_value=sample_config), \
             patch('core.sentry.get_exchange', return_value=mock_exchange), \
             patch('core.sentry.Notifier', return_value=mock_notifier), \
             patch('core.sentry.load_symbols_from_file', return_value=['BTC/USDT']), \
             patch('core.sentry.match_symbols', return_value=[{'symbol': 'BTC/USDT', 'exchange_symbol': 'BTCUSDT'}]), \
             patch('core.sentry.parse_timeframe', return_value=5):
            
            sentry = PriceSentry()
            
            assert sentry.config == sample_config
            assert sentry.notifier == mock_notifier
            assert sentry.exchange == mock_exchange
            assert sentry.matched_symbols == [{'symbol': 'BTC/USDT', 'exchange_symbol': 'BTCUSDT'}]
            assert sentry.minutes == 5
            assert sentry.threshold == 1

    def test_init_with_no_matched_symbols(self, sample_config, mock_exchange, mock_notifier):
        """Test initialization when no symbols are matched."""
        with patch('core.sentry.load_config', return_value=sample_config), \
             patch('core.sentry.get_exchange', return_value=mock_exchange), \
             patch('core.sentry.Notifier', return_value=mock_notifier), \
             patch('core.sentry.load_symbols_from_file', return_value=['BTC/USDT']), \
             patch('core.sentry.match_symbols', return_value=[]), \
             patch('core.sentry.parse_timeframe', return_value=5):
            
            with patch('core.sentry.logging') as mock_logging:
                sentry = PriceSentry()
                
                assert sentry.matched_symbols == []
                mock_logging.warning.assert_called_with("No matched symbols found. Please check your symbols file.")

    def test_init_with_custom_config(self, mock_exchange, mock_notifier):
        """Test initialization with custom configuration values."""
        custom_config = {
            'exchange': 'okx',
            'symbolsFilePath': 'custom/symbols.txt',
            'defaultTimeframe': '15m',
            'defaultThreshold': 2.5
        }
        
        with patch('core.sentry.load_config', return_value=custom_config), \
             patch('core.sentry.get_exchange', return_value=mock_exchange), \
             patch('core.sentry.Notifier', return_value=mock_notifier), \
             patch('core.sentry.load_symbols_from_file', return_value=['ETH/USDT']), \
             patch('core.sentry.match_symbols', return_value=[{'symbol': 'ETH/USDT', 'exchange_symbol': 'ETH-USDT'}]), \
             patch('core.sentry.parse_timeframe', return_value=15):
            
            sentry = PriceSentry()
            
            assert sentry.minutes == 15
            assert sentry.threshold == 2.5

    @pytest.mark.asyncio
    async def test_run_with_no_symbols(self, sample_config, mock_exchange, mock_notifier):
        """Test run method when no symbols are matched."""
        with patch('core.sentry.load_config', return_value=sample_config), \
             patch('core.sentry.get_exchange', return_value=mock_exchange), \
             patch('core.sentry.Notifier', return_value=mock_notifier), \
             patch('core.sentry.load_symbols_from_file', return_value=['BTC/USDT']), \
             patch('core.sentry.match_symbols', return_value=[]), \
             patch('core.sentry.parse_timeframe', return_value=5):
            
            sentry = PriceSentry()
            result = await sentry.run()
            
            # Should return early when no symbols
            assert result is None

    @pytest.mark.asyncio
    async def test_run_normal_operation(self, sample_config, mock_exchange, mock_notifier):
        """Test run method with normal operation."""
        with patch('core.sentry.load_config', return_value=sample_config), \
             patch('core.sentry.get_exchange', return_value=mock_exchange), \
             patch('core.sentry.Notifier', return_value=mock_notifier), \
             patch('core.sentry.load_symbols_from_file', return_value=['BTC/USDT']), \
             patch('core.sentry.match_symbols', return_value=[{'symbol': 'BTC/USDT', 'exchange_symbol': 'BTCUSDT'}]), \
             patch('core.sentry.parse_timeframe', return_value=1), \
             patch('core.sentry.monitor_top_movers') as mock_monitor, \
             patch('core.sentry.logging') as mock_logging:
            
            # Mock monitor_top_movers to return None (no price movements)
            mock_monitor.return_value = None
            
            sentry = PriceSentry()
            
            # Mock the websocket and time to simulate a short run
            mock_exchange.start_websocket = Mock()
            mock_exchange.close = Mock()
            mock_exchange.ws_connected = True
            
            # Simulate a short run by interrupting the loop
            with patch('asyncio.sleep', side_effect=KeyboardInterrupt()):
                await sentry.run()
            
            # Verify that websocket was started and closed
            mock_exchange.start_websocket.assert_called_once()
            mock_exchange.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_with_price_movements(self, sample_config, mock_exchange, mock_notifier):
        """Test run method when price movements are detected."""
        with patch('core.sentry.load_config', return_value=sample_config), \
             patch('core.sentry.get_exchange', return_value=mock_exchange), \
             patch('core.sentry.Notifier', return_value=mock_notifier), \
             patch('core.sentry.load_symbols_from_file', return_value=['BTC/USDT']), \
             patch('core.sentry.match_symbols', return_value=[{'symbol': 'BTC/USDT', 'exchange_symbol': 'BTCUSDT'}]), \
             patch('core.sentry.parse_timeframe', return_value=1), \
             patch('core.sentry.monitor_top_movers') as mock_monitor, \
             patch('core.sentry.logging') as mock_logging:
            
            # Mock monitor_top_movers to return price movements
            mock_monitor.return_value = ("Price movement detected", [("BTC/USDT", 5.0)])
            
            sentry = PriceSentry()
            
            # Mock the websocket and time to simulate a short run
            mock_exchange.start_websocket = Mock()
            mock_exchange.close = Mock()
            mock_exchange.ws_connected = True
            
            # Simulate a short run by interrupting the loop
            with patch('asyncio.sleep', side_effect=KeyboardInterrupt()):
                await sentry.run()
            
            # Verify that notification was sent
            mock_notifier.send.assert_called_once_with("Price movement detected")

    def test_default_config_values(self, mock_exchange, mock_notifier):
        """Test that default config values are applied correctly."""
        minimal_config = {'exchange': 'binance'}
        
        with patch('core.sentry.load_config', return_value=minimal_config), \
             patch('core.sentry.get_exchange', return_value=mock_exchange), \
             patch('core.sentry.Notifier', return_value=mock_notifier), \
             patch('core.sentry.load_symbols_from_file', return_value=['BTC/USDT']), \
             patch('core.sentry.match_symbols', return_value=[{'symbol': 'BTC/USDT', 'exchange_symbol': 'BTCUSDT'}]), \
             patch('core.sentry.parse_timeframe', return_value=5):
            
            sentry = PriceSentry()
            
            # Check default values
            assert sentry.config.get('symbolsFilePath') == 'config/symbols.txt'
            assert sentry.minutes == 5  # defaultTimeframe '5m' -> 5 minutes
            assert sentry.threshold == 1  # defaultThreshold

    @pytest.mark.asyncio
    async def test_websocket_reconnection(self, sample_config, mock_exchange, mock_notifier):
        """Test websocket reconnection logic."""
        with patch('core.sentry.load_config', return_value=sample_config), \
             patch('core.sentry.get_exchange', return_value=mock_exchange), \
             patch('core.sentry.Notifier', return_value=mock_notifier), \
             patch('core.sentry.load_symbols_from_file', return_value=['BTC/USDT']), \
             patch('core.sentry.match_symbols', return_value=[{'symbol': 'BTC/USDT', 'exchange_symbol': 'BTCUSDT'}]), \
             patch('core.sentry.parse_timeframe', return_value=1), \
             patch('core.sentry.monitor_top_movers', return_value=None), \
             patch('core.sentry.logging') as mock_logging:
            
            sentry = PriceSentry()
            
            # Mock websocket to be disconnected
            mock_exchange.start_websocket = Mock()
            mock_exchange.close = Mock()
            mock_exchange.ws_connected = False
            mock_exchange.check_ws_connection = Mock()
            
            # Simulate time passing and websocket check
            with patch('time.time', side_effect=[0, 60, 120]), \
                 patch('asyncio.sleep', side_effect=KeyboardInterrupt()):
                await sentry.run()
            
            # Verify that reconnection was attempted
            mock_exchange.check_ws_connection.assert_called()