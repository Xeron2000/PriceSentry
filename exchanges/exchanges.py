import asyncio
import json
import logging
import threading
import time

import ccxt
import websockets
from expiringdict import ExpiringDict


class Exchange:
    def __init__(self, exchangeName):
        if exchangeName not in ccxt.exchanges:
            raise ValueError(f"Exchange {exchangeName} not supported by ccxt")

        self.exchangeName = exchangeName
        self.exchange = getattr(ccxt, exchangeName)(
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

    async def _ws_connect(self, symbols):
        """Establish WebSocket connection and subscribe to market data"""
        logging.info(
            f"Attempting to establish WebSocket connection for {self.exchangeName}, subscribing symbols: {symbols}"
        )

        max_retries = 3
        retry_count = 0

        while retry_count < max_retries and self.running:
            try:
                if self.exchangeName == "okx":
                    uri = "wss://ws.okx.com:8443/ws/v5/public"
                    logging.debug(f"OKX WebSocket URI: {uri}")

                    # Prepare subscription message - modify format to meet OKX requirements
                    subscribe_msg = {"op": "subscribe", "args": []}

                    # OKX requires specific format for trading pairs
                    for symbol in symbols:
                        # Convert format, e.g., BTC/USDT:USDT to BTC-USDT-SWAP
                        if ":USDT" in symbol:
                            # Futures trading pair
                            base_symbol = symbol.split("/")[0]
                            formatted_symbol = f"{base_symbol}-USDT-SWAP"
                        else:
                            # Spot trading pair
                            formatted_symbol = symbol.replace("/", "-")

                        subscribe_msg["args"].append(
                            {"channel": "tickers", "instId": formatted_symbol}
                        )

                    logging.debug(f"Subscription message: {subscribe_msg}")

                    async with websockets.connect(uri) as websocket:
                        self.ws = websocket
                        self.ws_connected = True
                        logging.info("OKX WebSocket connection established")

                        # Send subscription request
                        await websocket.send(json.dumps(subscribe_msg))
                        logging.info("Subscription request sent to OKX")

                        # Wait for subscription confirmation
                        response = await websocket.recv()
                        logging.debug(f"Subscription response: {response}")

                        # Continuously receive data
                        while self.running:
                            try:
                                response = await websocket.recv()
                                data = json.loads(response)

                                # Handle heartbeat messages
                                if "event" in data and data["event"] == "ping":
                                    pong_msg = {"event": "pong"}
                                    await websocket.send(json.dumps(pong_msg))
                                    logging.debug("Heartbeat response sent")
                                    continue

                                # Process ticker data
                                if "data" in data:
                                    for item in data["data"]:
                                        symbol = item["instId"]
                                        price = float(item["last"])
                                        self.last_prices[symbol] = price

                                        # Log received price data every 10 minutes
                                        if (
                                            time.time() % 600 < 1
                                        ):  # Approximately every 10 minutes
                                            logging.info(
                                                f"OKX price update - {symbol}: {price}"
                                            )

                                        # Store historical data
                                        timestamp = int(time.time() * 1000)
                                        if symbol not in self.historical_prices:
                                            self.historical_prices[symbol] = []
                                        self.historical_prices[symbol].append(
                                            (timestamp, price)
                                        )

                                        # Clean up old historical data (keep 24 hours)
                                        cutoff = timestamp - (24 * 60 * 60 * 1000)
                                        self.historical_prices[symbol] = [
                                            item
                                            for item in self.historical_prices[symbol]
                                            if item[0] >= cutoff
                                        ]
                            except Exception as e:
                                logging.error(
                                    f"OKX WebSocket data processing error: {e}"
                                )
                                break

                        self.ws_connected = False
                        logging.warning("OKX WebSocket connection closed")

                    # If connection successful, break retry loop
                    break

            except Exception as e:
                logging.error(
                    f"Error establishing WebSocket connection (attempt {retry_count + 1}/{max_retries}): {e}"
                )
                retry_count += 1
                await asyncio.sleep(5)  # Wait 5 seconds before retrying

        if not self.ws_connected:
            logging.error(
                f"Unable to establish WebSocket connection after {max_retries} attempts"
            )

    def start_websocket(self, symbols):
        """Start WebSocket connection thread"""
        logging.info(
            f"Starting WebSocket connection for {self.exchangeName}, number of symbols: {len(symbols)}"
        )

        # Print symbol list for debugging
        for i, symbol in enumerate(symbols):
            logging.debug(f"Symbol {i + 1}/{len(symbols)}: {symbol}")

        self.running = True

        def run_websocket_loop():
            logging.info(
                f"WebSocket thread started, creating new event loop for {self.exchangeName}"
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
            f"WebSocket connection successfully established, exchange: {self.exchangeName}"
        )

    def stop_websocket(self):
        """Stop WebSocket connection"""
        self.running = False
        if self.ws_thread:
            self.ws_thread.join(timeout=5)
            self.ws_thread = None
        logging.info(f"WebSocket connection closed for {self.exchangeName}")

    async def getCurrentPrices(self, symbols):
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

    def getPriceMinutesAgo(self, symbols, minutes):
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

                # If the closest price differs from target time by more than 10 minutes, use API
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
                f"{self.exchangeName} WebSocket connection disconnected, attempting to reconnect"
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
