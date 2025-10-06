import asyncio
import logging
import threading
import time
from abc import ABC, abstractmethod

import ccxt
from expiringdict import ExpiringDict

from utils.cache_manager import price_cache
from utils.error_handler import ErrorSeverity, error_handler
from utils.performance_monitor import performance_monitor


class BaseExchange(ABC):
    def __init__(self, exchange_name):
        try:
            if exchange_name not in ccxt.exchanges:
                raise ValueError(f"Exchange {exchange_name} not supported by ccxt")

            self.exchange_name = exchange_name
            self.exchange = getattr(ccxt, exchange_name)(
                {
                    "enableRateLimit": True,
                }
            )

            # Cache for storing price data with TTL of 300 seconds
            self.priceCache = ExpiringDict(max_len=1000, max_age_seconds=300)

            # WebSocket related properties
            self.ws = None
            self.ws_connected = False
            self.ws_data = {}
            self.last_prices = {}
            self.historical_prices = {}
            self.ws_thread = None
            self.running = False

            logging.info(f"BaseExchange initialized for {exchange_name}")

        except Exception as e:
            error_handler.handle_config_error(
                e,
                {
                    "component": "BaseExchange",
                    "operation": "initialization",
                    "exchange_name": exchange_name,
                },
                ErrorSeverity.CRITICAL,
            )
            raise

    def _get_ohlcv_params(self, symbol):
        """Parameters forwarded to fetch_ohlcv for historical data."""
        return {}

    @abstractmethod
    async def _ws_connect(self, symbols):
        """Establish WebSocket connection and subscribe to market data"""
        raise NotImplementedError

    @error_handler.circuit_breaker_protect(
        "websocket_start", failure_threshold=5, recovery_timeout=60
    )
    def start_websocket(self, symbols):
        """Start WebSocket connection thread"""
        try:
            logging.info(
                f"Starting WebSocket connection for {self.exchange_name}, "
                f"number of symbols: {len(symbols)}"
            )

            # Print symbol list for debugging
            for i, symbol in enumerate(symbols):
                logging.debug(f"Symbol {i + 1}/{len(symbols)}: {symbol}")

            self.running = True

            def run_websocket_loop():
                logging.info(
                    f"WebSocket thread started, creating new event loop for "
                    f"{self.exchange_name}"
                )
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self._ws_connect(symbols))
                except Exception as e:
                    error_handler.handle_network_error(
                        e,
                        {
                            "component": "BaseExchange",
                            "operation": "websocket_loop",
                            "exchange": self.exchange_name,
                        },
                        ErrorSeverity.ERROR,
                    )
                    logging.error(f"Error running WebSocket thread: {e}")
                finally:
                    logging.info("WebSocket thread ending, closing event loop")
                    loop.close()

            self.ws_thread = threading.Thread(target=run_websocket_loop)
            self.ws_thread.daemon = True
            self.ws_thread.start()
            logging.info(f"WebSocket thread started: {self.ws_thread.name}")

            # Wait for connection to establish
            timeout = 10
            start_time = time.time()
            logging.info(
                f"Waiting for WebSocket connection to establish, timeout: {timeout} "
                "seconds"
            )
            while not self.ws_connected and time.time() - start_time < timeout:
                time.sleep(0.1)

            if not self.ws_connected:
                error_msg = "WebSocket connection establishment failed, timeout"
                error_handler.handle_network_error(
                    Exception(error_msg),
                    {
                        "component": "BaseExchange",
                        "operation": "websocket_start",
                        "exchange": self.exchange_name,
                    },
                    ErrorSeverity.ERROR,
                )
                raise ConnectionError(error_msg)

            logging.info(
                "WebSocket connection successfully established, "
                f"exchange: {self.exchange_name}"
            )

        except Exception as e:
            error_handler.handle_network_error(
                e,
                {
                    "component": "BaseExchange",
                    "operation": "websocket_start",
                    "exchange": self.exchange_name,
                },
                ErrorSeverity.ERROR,
            )
            raise

    def stop_websocket(self):
        """Stop WebSocket connection"""
        self.running = False
        if self.ws_thread:
            self.ws_thread.join(timeout=5)
            self.ws_thread = None
        logging.info(f"WebSocket connection closed for {self.exchange_name}")

    @error_handler.retry_with_backoff(max_retries=3, base_delay=1.0, max_delay=10.0)
    @performance_monitor.time_function("get_current_prices")
    async def get_current_prices(self, symbols):
        """Get current prices (from WebSocket data)"""
        try:
            # First try to get prices from cache
            cached_prices = price_cache.get_prices(symbols)

            # Check which symbols are missing from cache
            missing_symbols = [s for s in symbols if cached_prices.get(s) is None]

            if not missing_symbols:
                performance_monitor.record_counter("cache_hits", len(symbols))
                return cached_prices

            # For missing symbols, fetch from API or WebSocket
            result = cached_prices.copy()

            if not self.ws_connected:
                # If WebSocket not connected, use API call
                try:
                    timer_id = performance_monitor.start_timer("api_price_fetch")
                    for symbol in missing_symbols:
                        # Call API to get price
                        ticker = self.exchange.fetch_ticker(symbol)
                        if (
                            ticker
                            and hasattr(ticker, "__getitem__")
                            and "last" in ticker
                            and ticker["last"]
                        ):
                            price = float(ticker["last"])
                            result[symbol] = price
                            # Update cache
                            price_cache.set_price(symbol, price)
                            performance_monitor.record_counter("cache_misses", 1)
                    performance_monitor.stop_timer(timer_id, "api_price_fetch")
                except Exception as e:
                    error_handler.handle_api_error(
                        e,
                        {
                            "component": "BaseExchange",
                            "operation": "get_current_prices_api",
                            "symbols": symbols,
                        },
                        ErrorSeverity.WARNING,
                    )
                    performance_monitor.record_counter("api_errors", 1)
                    logging.error(f"Error getting current prices via API: {e}")

                return result

            # If WebSocket is connected, try to get from WebSocket data
            for symbol in missing_symbols:
                if symbol in self.last_prices:
                    result[symbol] = self.last_prices[symbol]
                    price_cache.set_price(symbol, self.last_prices[symbol])
                    performance_monitor.record_counter("cache_misses", 1)

            # For symbols still missing, use API
            still_missing = [s for s in symbols if result.get(s) is None]
            if still_missing:
                try:
                    timer_id = performance_monitor.start_timer(
                        "api_price_fetch_missing"
                    )
                    for symbol in still_missing:
                        # Call API to get price
                        ticker = self.exchange.fetch_ticker(symbol)
                        if (
                            ticker
                            and hasattr(ticker, "__getitem__")
                            and "last" in ticker
                            and ticker["last"]
                        ):
                            price = float(ticker["last"])
                            result[symbol] = price
                            # Update cache
                            price_cache.set_price(symbol, price)
                            performance_monitor.record_counter("cache_misses", 1)
                    performance_monitor.stop_timer(timer_id, "api_price_fetch_missing")
                except Exception as e:
                    error_handler.handle_api_error(
                        e,
                        {
                            "component": "BaseExchange",
                            "operation": "get_current_prices_missing",
                            "symbols": still_missing,
                        },
                        ErrorSeverity.WARNING,
                    )
                    performance_monitor.record_counter("api_errors", 1)
                    logging.error(
                        f"Error getting current prices for missing symbols: {e}"
                    )

            # Record cache performance metrics
            total_symbols = len(symbols)
            cache_hits = total_symbols - len(missing_symbols)
            hit_rate = (cache_hits / total_symbols * 100) if total_symbols > 0 else 0
            performance_monitor.record_gauge("cache_hit_rate", hit_rate)

            return result

        except Exception as e:
            error_handler.handle_api_error(
                e,
                {
                    "component": "BaseExchange",
                    "operation": "get_current_prices",
                    "symbols": symbols,
                },
                ErrorSeverity.ERROR,
            )
            performance_monitor.record_counter("get_current_prices_errors", 1)
            raise

    def get_price_minutes_ago(self, symbols, minutes):
        """Get prices from specified minutes ago (from historical data)"""
        if not self.ws_connected:
            # If WebSocket not connected, use API call
            result = {}
            try:
                for symbol in symbols:
                    # Get historical data
                    since = int(
                        (time.time() - minutes * 60) * 1000
                    )  # Convert to milliseconds
                    ohlcv = self.exchange.fetch_ohlcv(
                        symbol, "1m", since=since, limit=1, params=self._get_ohlcv_params(symbol)
                    )

                    if ohlcv and len(ohlcv) > 0:
                        # OHLCV format: [timestamp, open, high, low, close, volume]
                        price = float(ohlcv[0][4])  # Close price
                        result[symbol] = price
            except Exception as e:
                logging.error(f"Error getting historical prices: {e}")

            return result

        target_time = int(time.time() * 1000) - (minutes * 60 * 1000)
        result = {}

        for symbol in symbols:
            if symbol in self.historical_prices and self.historical_prices[symbol]:
                # Find the price closest to target time
                closest_price = min(
                    self.historical_prices[symbol],
                    key=lambda x: abs(x[0] - target_time),
                )

                # If the closest price differs from target time by more than 10
                # minutes, use API
                if abs(closest_price[0] - target_time) > (10 * 60 * 1000):
                    try:
                        # Get historical data
                        since = int(
                            (time.time() - minutes * 60) * 1000
                        )  # Convert to milliseconds
                        ohlcv = self.exchange.fetch_ohlcv(
                            symbol, "1m", since=since, limit=1, params=self._get_ohlcv_params(symbol)
                        )

                        if ohlcv and len(ohlcv) > 0:
                            # OHLCV format: [timestamp, open, high, low, close, volume]
                            price = float(ohlcv[0][4])  # Close price
                            result[symbol] = price
                    except Exception as e:
                        logging.error(f"Error getting historical prices: {e}")
                else:
                    result[symbol] = closest_price[1]
            else:
                try:
                    # Get historical data
                    since = int(
                        (time.time() - minutes * 60) * 1000
                    )  # Convert to milliseconds
                    ohlcv = self.exchange.fetch_ohlcv(
                        symbol, "1m", since=since, limit=1, params=self._get_ohlcv_params(symbol)
                    )

                    if ohlcv and len(ohlcv) > 0:
                        # OHLCV format: [timestamp, open, high, low, close, volume]
                        price = float(ohlcv[0][4])  # Close price
                        result[symbol] = price
                except Exception as e:
                    logging.error(f"Error getting historical prices: {e}")

        return result

    def close(self):
        """Close connection"""
        self.stop_websocket()
        if hasattr(self.exchange, "close"):
            self.exchange.close()

    @error_handler.circuit_breaker_protect(
        "websocket_reconnect", failure_threshold=3, recovery_timeout=30
    )
    def check_ws_connection(self):
        """Check WebSocket connection status and attempt to reconnect"""
        try:
            if not self.ws_connected and self.running:
                logging.warning(
                    f"{self.exchange_name} WebSocket connection disconnected, "
                    "attempting to reconnect"
                )
                # Get currently subscribed symbols
                symbols = list(self.last_prices.keys())
                if not symbols:
                    error_handler.handle_network_error(
                        Exception("No available symbol list for reconnection"),
                        {
                            "component": "BaseExchange",
                            "operation": "check_ws_connection",
                            "exchange": self.exchange_name,
                        },
                        ErrorSeverity.ERROR,
                    )
                    logging.error("No available symbol list for reconnection")
                    return False

                # Restart WebSocket
                try:
                    self.start_websocket(symbols)
                    return True
                except Exception as e:
                    error_handler.handle_network_error(
                        e,
                        {
                            "component": "BaseExchange",
                            "operation": "websocket_reconnect",
                            "exchange": self.exchange_name,
                        },
                        ErrorSeverity.ERROR,
                    )
                    logging.error(f"WebSocket reconnection failed: {e}")
                    return False
            return self.ws_connected

        except Exception as e:
            error_handler.handle_network_error(
                e,
                {
                    "component": "BaseExchange",
                    "operation": "check_ws_connection",
                    "exchange": self.exchange_name,
                },
                ErrorSeverity.ERROR,
            )
            return False
