import asyncio
import json
import logging
import time

import websockets

from .base import BaseExchange


class BybitExchange(BaseExchange):
    def __init__(self):
        super().__init__("bybit")
        self.exchange.options["defaultType"] = "swap"

    async def _ws_connect(self, symbols):
        """Establish WebSocket connection and subscribe to market data"""
        logging.info(
            f"Attempting to establish WebSocket connection for {self.exchange_name}, "
            f"subscribing symbols: {symbols}"
        )

        max_retries = 3
        retry_count = 0

        while retry_count < max_retries and self.running:
            try:
                # Bybit uses different endpoints for spot and derivatives
                # This implementation will focus on the unified public endpoint
                uri = "wss://stream.bybit.com/v5/public/linear"
                logging.debug(f"Bybit WebSocket URI: {uri}")

                subscribe_msg = {"op": "subscribe", "args": []}

                for symbol in symbols:
                    # Bybit uses symbol format like BTCUSDT without any separator
                    formatted_symbol = symbol.replace("/", "")
                    subscribe_msg["args"].append(f"tickers.{formatted_symbol}")

                logging.debug(f"Subscription message: {subscribe_msg}")

                async with websockets.connect(uri) as websocket:
                    self.ws = websocket
                    self.ws_connected = True
                    logging.info("Bybit WebSocket connection established")

                    # Send subscription request
                    await websocket.send(json.dumps(subscribe_msg))
                    logging.info("Subscription request sent to Bybit")

                    # Continuously receive data
                    while self.running:
                        try:
                            response = await websocket.recv()
                            data = json.loads(response)

                            # Handle ping/pong
                            if "op" in data and data.get("op") == "ping":
                                pong_msg = {"op": "pong", "req_id": data.get("req_id")}
                                await websocket.send(json.dumps(pong_msg))
                                logging.debug("Heartbeat response sent")
                                continue

                            if "topic" in data and "tickers" in data["topic"]:
                                symbol = data["data"]["symbol"]
                                price = float(data["data"]["lastPrice"])
                                self.last_prices[symbol] = price

                                # Log received price data every 10 minutes
                                if time.time() % 600 < 1:
                                    logging.info(
                                        f"Bybit price update - {symbol}: {price}"
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
                            logging.error(f"Bybit WebSocket data processing error: {e}")
                            break

                    self.ws_connected = False
                    logging.warning("Bybit WebSocket connection closed")

                # If connection successful, break retry loop
                break

            except Exception as e:
                logging.error(
                    f"Error establishing WebSocket connection "
                    f"(attempt {retry_count + 1}/{max_retries}): {e}"
                )
                retry_count += 1
                await asyncio.sleep(5)  # Wait 5 seconds before retrying

        if not self.ws_connected:
            logging.error(
                f"Unable to establish WebSocket connection after {max_retries} attempts"
            )
