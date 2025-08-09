import asyncio
import logging
import threading
import time
from abc import ABC, abstractmethod

import ccxt
from expiringdict import ExpiringDict


class BaseExchange(ABC):
    def __init__(self, exchange_name):
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

    @abstractmethod
    async def _ws_connect(self, symbols):
        """Establish WebSocket connection and subscribe to market data"""
        raise NotImplementedError

    def start_websocket(self, symbols):
        """Start WebSocket connection thread"""
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
            f"Waiting for WebSocket connection to establish, timeout: {timeout} seconds"
        )
        while not self.ws_connected and time.time() - start_time < timeout:
            time.sleep(0.1)

        if not self.ws_connected:
            logging.error("WebSocket connection establishment failed, timeout")
            raise ConnectionError("Failed to establish WebSocket connection")

        logging.info(
            "WebSocket connection successfully established, "
            f"exchange: {self.exchange_name}"
        )

    def stop_websocket(self):
        """Stop WebSocket connection"""
        self.running = False
        if self.ws_thread:
            self.ws_thread.join(timeout=5)
            self.ws_thread = None
        logging.info(f"WebSocket connection closed for {self.exchange_name}")

    async def get_current_prices(self, symbols):
        """Get current prices (from WebSocket data)"""
        if not self.ws_connected:
            # If WebSocket not connected, use API call
            result = {}
            try:
                for symbol in symbols:
                    # Check cache
                    if symbol in self.priceCache:
                        result[symbol] = self.priceCache[symbol]
                        continue

                    # Call API to get price
                    ticker = self.exchange.fetch_ticker(symbol)
                    if ticker and "last" in ticker and ticker["last"]:
                        price = float(ticker["last"])
                        result[symbol] = price
                        # Update cache
                        self.priceCache[symbol] = price
            except Exception as e:
                logging.error(f"Error getting current prices: {e}")

            return result

        result = {}
        for symbol in symbols:
            if symbol in self.last_prices:
                result[symbol] = self.last_prices[symbol]

        # For symbols not found in WebSocket, use API
        missing_symbols = [s for s in symbols if s not in result]
        if missing_symbols:
            try:
                for symbol in missing_symbols:
                    # Check cache
                    if symbol in self.priceCache:
                        result[symbol] = self.priceCache[symbol]
                        continue

                    # Call API to get price
                    ticker = self.exchange.fetch_ticker(symbol)
                    if ticker and "last" in ticker and ticker["last"]:
                        price = float(ticker["last"])
                        result[symbol] = price
                        # Update cache
                        self.priceCache[symbol] = price
            except Exception as e:
                logging.error(f"Error getting current prices: {e}")

        return result

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
                        symbol, "1m", since=since, limit=1
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
                            symbol, "1m", since=since, limit=1
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
                        symbol, "1m", since=since, limit=1
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

    def check_ws_connection(self):
        """Check WebSocket connection status and attempt to reconnect"""
        if not self.ws_connected and self.running:
            logging.warning(
                f"{self.exchange_name} WebSocket connection disconnected, "
                "attempting to reconnect"
            )
            # Get currently subscribed symbols
            symbols = list(self.last_prices.keys())
            if not symbols:
                logging.error("No available symbol list for reconnection")
                return False

            # Restart WebSocket
            try:
                self.start_websocket(symbols)
                return True
            except Exception as e:
                logging.error(f"WebSocket reconnection failed: {e}")
                return False
        return self.ws_connected
