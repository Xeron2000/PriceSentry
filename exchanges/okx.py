import asyncio
import json
import logging
import time

import websockets

from .base import BaseExchange


class OkxExchange(BaseExchange):
    def __init__(self):
        super().__init__("okx")

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
                uri = "wss://ws.okx.com:8443/ws/v5/public"
                logging.debug(f"OKX WebSocket URI: {uri}")

                # Prepare subscription message - modify format to meet OKX
                # requirements
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
                            logging.error(f"OKX WebSocket data processing error: {e}")
                            break

                    self.ws_connected = False
                    logging.warning("OKX WebSocket connection closed")

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
