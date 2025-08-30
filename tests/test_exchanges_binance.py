"""
Tests for exchanges/binance.py - Binance exchange implementation.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import time
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from exchanges.binance import BinanceExchange


class TestBinanceExchange:
    """Test cases for BinanceExchange class."""

    def test_init(self):
        """Test initialization of BinanceExchange."""
        with patch('exchanges.binance.ccxt.exchanges', ['binance']), \
             patch('exchanges.binance.ccxt.binance') as mock_binance:
            
            mock_exchange = Mock()
            mock_binance.return_value = mock_exchange
            
            exchange = BinanceExchange()
            
            assert exchange.exchange_name == "binance"
            assert exchange.exchange == mock_exchange
            
            # Verify default type is set to future
            assert exchange.exchange.options["defaultType"] == "future"

    @pytest.mark.asyncio
    async def test_ws_connect_success(self):
        """Test successful WebSocket connection."""
        with patch('exchanges.binance.ccxt.exchanges', ['binance']), \
             patch('exchanges.binance.ccxt.binance'), \
             patch('exchanges.binance.websockets.connect') as mock_connect, \
             patch('exchanges.binance.logging') as mock_logging:
            
            # Mock WebSocket
            mock_websocket = AsyncMock()
            mock_connect.return_value = mock_websocket
            
            # Mock WebSocket messages
            mock_websocket.recv.side_effect = [
                json.dumps({
                    "e": "24hrTicker",
                    "s": "BTCUSDT",
                    "c": "50000.00"
                }),
                json.dumps({
                    "e": "ping",
                    "data": "ping_data"
                }),
                json.dumps({
                    "e": "24hrTicker",
                    "s": "ETHUSDT",
                    "c": "3000.00"
                })
            ]
            
            exchange = BinanceExchange()
            exchange.running = True
            
            # Run for a short time then stop
            async def run_briefly():
                task = asyncio.create_task(exchange._ws_connect(['BTC/USDT', 'ETH/USDT']))
                await asyncio.sleep(0.1)  # Let it run briefly
                exchange.running = False
                await task
            
            await run_briefly()
            
            # Verify connection was established
            assert exchange.ws_connected is True
            mock_connect.assert_called_once()
            
            # Verify prices were stored
            assert exchange.last_prices['BTC/USDT'] == 50000.0
            assert exchange.last_prices['ETH/USDT'] == 3000.0
            
            # Verify historical data was stored
            assert 'BTC/USDT' in exchange.historical_prices
            assert 'ETH/USDT' in exchange.historical_prices

    @pytest.mark.asyncio
    async def test_ws_connect_with_retry(self):
        """Test WebSocket connection with retry mechanism."""
        with patch('exchanges.binance.ccxt.exchanges', ['binance']), \
             patch('exchanges.binance.ccxt.binance'), \
             patch('exchanges.binance.websockets.connect') as mock_connect, \
             patch('exchanges.binance.asyncio.sleep') as mock_sleep, \
             patch('exchanges.binance.logging') as mock_logging:
            
            # Mock first connection to fail, second to succeed
            mock_websocket = AsyncMock()
            mock_connect.side_effect = [
                Exception("Connection failed"),
                mock_websocket
            ]
            
            # Mock WebSocket messages
            mock_websocket.recv.side_effect = [
                json.dumps({
                    "e": "24hrTicker",
                    "s": "BTCUSDT",
                    "c": "50000.00"
                })
            ]
            
            exchange = BinanceExchange()
            exchange.running = True
            
            # Run for a short time then stop
            async def run_briefly():
                task = asyncio.create_task(exchange._ws_connect(['BTC/USDT']))
                await asyncio.sleep(0.1)  # Let it run briefly
                exchange.running = False
                await task
            
            await run_briefly()
            
            # Verify connection was established after retry
            assert exchange.ws_connected is True
            assert mock_connect.call_count == 2
            mock_sleep.assert_called_once_with(5)

    @pytest.mark.asyncio
    async def test_ws_connect_max_retries_exceeded(self):
        """Test WebSocket connection when max retries are exceeded."""
        with patch('exchanges.binance.ccxt.exchanges', ['binance']), \
             patch('exchanges.binance.ccxt.binance'), \
             patch('exchanges.binance.websockets.connect') as mock_connect, \
             patch('exchanges.binance.asyncio.sleep') as mock_sleep, \
             patch('exchanges.binance.logging') as mock_logging:
            
            # Mock all connections to fail
            mock_connect.side_effect = Exception("Connection failed")
            
            exchange = BinanceExchange()
            exchange.running = True
            
            # Run the connection attempt
            await exchange._ws_connect(['BTC/USDT'])
            
            # Verify connection failed
            assert exchange.ws_connected is False
            assert mock_connect.call_count == 3  # Max retries
            assert mock_sleep.call_count == 2  # Sleep between retries

    @pytest.mark.asyncio
    async def test_ws_connect_ping_pong(self):
        """Test WebSocket ping/pong handling."""
        with patch('exchanges.binance.ccxt.exchanges', ['binance']), \
             patch('exchanges.binance.ccxt.binance'), \
             patch('exchanges.binance.websockets.connect') as mock_connect, \
             patch('exchanges.binance.logging') as mock_logging:
            
            # Mock WebSocket
            mock_websocket = AsyncMock()
            mock_connect.return_value = mock_websocket
            
            # Mock ping response
            mock_websocket.recv.side_effect = [
                json.dumps({
                    "e": "ping",
                    "data": "ping_data"
                }),
                json.dumps({
                    "e": "24hrTicker",
                    "s": "BTCUSDT",
                    "c": "50000.00"
                })
            ]
            
            exchange = BinanceExchange()
            exchange.running = True
            
            # Run for a short time then stop
            async def run_briefly():
                task = asyncio.create_task(exchange._ws_connect(['BTC/USDT']))
                await asyncio.sleep(0.1)  # Let it run briefly
                exchange.running = False
                await task
            
            await run_briefly()
            
            # Verify ping was handled (pong was sent)
            mock_websocket.ping.assert_called_once()
            mock_websocket.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_ws_connect_uri_construction(self):
        """Test WebSocket URI construction."""
        with patch('exchanges.binance.ccxt.exchanges', ['binance']), \
             patch('exchanges.binance.ccxt.binance'), \
             patch('exchanges.binance.websockets.connect') as mock_connect, \
             patch('exchanges.binance.logging') as mock_logging:
            
            # Mock WebSocket
            mock_websocket = AsyncMock()
            mock_connect.return_value = mock_websocket
            
            # Mock WebSocket messages
            mock_websocket.recv.side_effect = [
                json.dumps({
                    "e": "24hrTicker",
                    "s": "BTCUSDT",
                    "c": "50000.00"
                })
            ]
            
            exchange = BinanceExchange()
            exchange.running = True
            
            # Run for a short time then stop
            async def run_briefly():
                task = asyncio.create_task(exchange._ws_connect(['BTC/USDT', 'ETH/USDT']))
                await asyncio.sleep(0.1)  # Let it run briefly
                exchange.running = False
                await task
            
            await run_briefly()
            
            # Verify correct URI was used
            expected_uri = "wss://fstream.binance.com/ws/btcusdt@ticker/ethusdt@ticker"
            mock_connect.assert_called_once_with(expected_uri)

    @pytest.mark.asyncio
    async def test_ws_connect_symbol_mapping(self):
        """Test symbol mapping from Binance format back to original."""
        with patch('exchanges.binance.ccxt.exchanges', ['binance']), \
             patch('exchanges.binance.ccxt.binance'), \
             patch('exchanges.binance.websockets.connect') as mock_connect, \
             patch('exchanges.binance.logging') as mock_logging:
            
            # Mock WebSocket
            mock_websocket = AsyncMock()
            mock_connect.return_value = mock_websocket
            
            # Mock WebSocket messages with different symbol formats
            mock_websocket.recv.side_effect = [
                json.dumps({
                    "e": "24hrTicker",
                    "s": "BTCUSDT",  # Binance format
                    "c": "50000.00"
                }),
                json.dumps({
                    "e": "24hrTicker",
                    "s": "ETHUSDT",  # Binance format
                    "c": "3000.00"
                })
            ]
            
            exchange = BinanceExchange()
            exchange.running = True
            
            # Run for a short time then stop
            async def run_briefly():
                task = asyncio.create_task(exchange._ws_connect(['BTC/USDT', 'ETH/USDT']))
                await asyncio.sleep(0.1)  # Let it run briefly
                exchange.running = False
                await task
            
            await run_briefly()
            
            # Verify symbols were mapped back to original format
            assert exchange.last_prices['BTC/USDT'] == 50000.0
            assert exchange.last_prices['ETH/USDT'] == 3000.0

    @pytest.mark.asyncio
    async def test_ws_connect_historical_data_cleanup(self):
        """Test historical data cleanup (keeping only 24 hours)."""
        with patch('exchanges.binance.ccxt.exchanges', ['binance']), \
             patch('exchanges.binance.ccxt.binance'), \
             patch('exchanges.binance.websockets.connect') as mock_connect, \
             patch('exchanges.binance.time.time', return_value=1640995200), \
             patch('exchanges.binance.logging') as mock_logging:
            
            # Mock WebSocket
            mock_websocket = AsyncMock()
            mock_connect.return_value = mock_websocket
            
            # Mock WebSocket messages
            mock_websocket.recv.side_effect = [
                json.dumps({
                    "e": "24hrTicker",
                    "s": "BTCUSDT",
                    "c": "50000.00"
                })
            ]
            
            exchange = BinanceExchange()
            exchange.running = True
            
            # Pre-populate with old historical data
            old_time = 1640995200000 - (25 * 60 * 60 * 1000)  # 25 hours ago
            exchange.historical_prices['BTC/USDT'] = [
                (old_time, 49000.0)
            ]
            
            # Run for a short time then stop
            async def run_briefly():
                task = asyncio.create_task(exchange._ws_connect(['BTC/USDT']))
                await asyncio.sleep(0.1)  # Let it run briefly
                exchange.running = False
                await task
            
            await run_briefly()
            
            # Verify old data was cleaned up
            assert len(exchange.historical_prices['BTC/USDT']) == 1
            assert exchange.historical_prices['BTC/USDT'][0][0] == 1640995200000  # Current time

    @pytest.mark.asyncio
    async def test_ws_connect_error_handling(self):
        """Test error handling in WebSocket connection."""
        with patch('exchanges.binance.ccxt.exchanges', ['binance']), \
             patch('exchanges.binance.ccxt.binance'), \
             patch('exchanges.binance.websockets.connect') as mock_connect, \
             patch('exchanges.binance.logging') as mock_logging:
            
            # Mock WebSocket
            mock_websocket = AsyncMock()
            mock_connect.return_value = mock_websocket
            
            # Mock WebSocket error
            mock_websocket.recv.side_effect = Exception("WebSocket error")
            
            exchange = BinanceExchange()
            exchange.running = True
            
            # Run the connection attempt
            await exchange._ws_connect(['BTC/USDT'])
            
            # Verify error was logged
            mock_logging.error.assert_called()

    @pytest.mark.asyncio
    async def test_ws_connect_stops_when_running_false(self):
        """Test that WebSocket stops when running is set to False."""
        with patch('exchanges.binance.ccxt.exchanges', ['binance']), \
             patch('exchanges.binance.ccxt.binance'), \
             patch('exchanges.binance.websockets.connect') as mock_connect, \
             patch('exchanges.binance.logging') as mock_logging:
            
            # Mock WebSocket
            mock_websocket = AsyncMock()
            mock_connect.return_value = mock_websocket
            
            # Mock WebSocket messages
            mock_websocket.recv.side_effect = [
                json.dumps({
                    "e": "24hrTicker",
                    "s": "BTCUSDT",
                    "c": "50000.00"
                })
            ]
            
            exchange = BinanceExchange()
            exchange.running = True
            
            # Stop running after first message
            async def stop_after_message():
                await asyncio.sleep(0.05)
                exchange.running = False
            
            # Run the connection attempt
            task = asyncio.create_task(exchange._ws_connect(['BTC/USDT']))
            stop_task = asyncio.create_task(stop_after_message())
            
            await task
            await stop_task
            
            # Verify connection was closed
            assert exchange.ws_connected is False

    def test_inheritance(self):
        """Test that BinanceExchange properly inherits from BaseExchange."""
        with patch('exchanges.binance.ccxt.exchanges', ['binance']), \
             patch('exchanges.binance.ccxt.binance'):
            
            exchange = BinanceExchange()
            
            # Verify inheritance
            assert hasattr(exchange, 'get_current_prices')
            assert hasattr(exchange, 'get_price_minutes_ago')
            assert hasattr(exchange, 'start_websocket')
            assert hasattr(exchange, 'stop_websocket')
            assert hasattr(exchange, 'close')
            assert hasattr(exchange, 'check_ws_connection')