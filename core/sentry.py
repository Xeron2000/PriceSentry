# core/sentry.py

import asyncio
import logging
import time

from core.notifier import Notifier
from exchanges.exchanges import Exchange
from utils.loadConfig import loadConfig
from utils.loadSymbolsFromFile import loadSymbolsFromFile
from utils.matchSymbols import matchSymbols
from utils.monitorTopMovers import monitorTopMovers
from utils.parseTimeframe import parseTimeframe


class PriceSentry:
    def __init__(self):
        self.config = loadConfig()
        self.notifier = Notifier(self.config)

        exchange_name = self.config.get("exchange", "binance")
        self.exchange = Exchange(exchange_name)

        symbols_file_path = self.config.get("symbolsFilePath", "config/symbols.txt")
        symbols = loadSymbolsFromFile(symbols_file_path)

        self.matched_symbols = matchSymbols(symbols, exchange_name)

        if not self.matched_symbols:
            logging.warning("No matched symbols found. Please check your symbols file.")
            return

        default_timeframe = self.config.get("defaultTimeframe", "5m")
        self.minutes = parseTimeframe(default_timeframe)

        self.threshold = self.config.get("defaultThreshold", 1)

    async def run(self):
        if not self.matched_symbols:
            return

        self.exchange.start_websocket(self.matched_symbols)
        logging.info(
            f"Started WebSocket connection for {len(self.matched_symbols)} symbols"
        )

        check_interval = self.minutes * 60
        last_check_time = 0

        try:
            logging.info("Entering main loop, starting price movement monitoring")
            logging.info(
                f"Check interval set to {self.minutes} minutes ({check_interval} seconds)"
            )
            while True:
                current_time = time.time()

                if current_time - last_check_time >= check_interval:
                    logging.info(
                        f"Checking price movements, {int(current_time - last_check_time)} seconds since last check"
                    )

                    message = await monitorTopMovers(
                        self.minutes,
                        self.matched_symbols,
                        self.threshold,
                        self.exchange,
                        self.config,
                    )

                    if message:
                        logging.info(
                            f"Detected price movements exceeding threshold, message content: {message}"
                        )
                        self.notifier.send(message)
                    else:
                        logging.info("No price movements exceeding threshold detected")

                    last_check_time = current_time

                if int(current_time) % 60 == 0:
                    logging.debug("Checking WebSocket connection status")
                    if not self.exchange.ws_connected:
                        logging.warning(
                            "WebSocket connection disconnected, attempting to reconnect"
                        )
                        self.exchange.check_ws_connection()
                    if hasattr(self.exchange, "last_prices"):
                        logging.debug(
                            f"Number of symbols with cached prices: {len(self.exchange.last_prices)}"
                        )

                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logging.info("Received keyboard interrupt. Shutting down...")
        finally:
            self.exchange.close()
