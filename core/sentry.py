# core/sentry.py

import asyncio
import logging
import time

from core.notifier import Notifier
from utils.get_exchange import get_exchange
from utils.load_config import load_config
from utils.load_symbols_from_file import load_symbols_from_file
from utils.match_symbols import match_symbols
from utils.monitor_top_movers import monitor_top_movers
from utils.chart import generate_candlestick_png, generate_multi_candlestick_png
from utils.parse_timeframe import parse_timeframe


class PriceSentry:
    def __init__(self):
        self.config = load_config()
        self.notifier = Notifier(self.config)

        exchange_name = self.config.get("exchange", "binance")
        self.exchange = get_exchange(exchange_name)

        symbols_file_path = self.config.get("symbolsFilePath", "config/symbols.txt")
        symbols = load_symbols_from_file(symbols_file_path)

        self.matched_symbols = match_symbols(symbols, exchange_name)

        if not self.matched_symbols:
            logging.warning("No matched symbols found. Please check your symbols file.")
            return

        default_timeframe = self.config.get("defaultTimeframe", "5m")
        self.minutes = parse_timeframe(default_timeframe)

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
                f"Check interval set to {self.minutes} minutes "
                f"({check_interval} seconds)"
            )
            while True:
                current_time = time.time()

                if current_time - last_check_time >= check_interval:
                    logging.info(
                        "Checking price movements, %s seconds since last check",
                        int(current_time - last_check_time),
                    )

                    result = await monitor_top_movers(
                        self.minutes,
                        self.matched_symbols,
                        self.threshold,
                        self.exchange,
                        self.config,
                    )

                    if result:
                        message, top_movers_sorted = result
                        logging.info(
                            "Detected price movements exceeding threshold, "
                            f"message content: {message}"
                        )
                        # Build a composite chart image for top 6 movers and send only the image via Telegram
                        attach_chart = self.config.get("attachChart", False)
                        image_bytes = None
                        image_caption = ""  # no text per requirement
                        if attach_chart and top_movers_sorted:
                            try:
                                symbols_for_chart = [s for s, _ in top_movers_sorted[:6]]
                                chart_timeframe = self.config.get(
                                    "chartTimeframe", "1m"
                                )
                                chart_lookback = int(
                                    self.config.get("chartLookbackMinutes", 60)
                                )
                                chart_theme = self.config.get("chartTheme", "dark")
                                ma_windows = self.config.get(
                                    "chartIncludeMA", [7, 25]
                                )

                                img_width = int(self.config.get("chartImageWidth", 1200))
                                img_height = int(self.config.get("chartImageHeight", 900))
                                img_scale = int(self.config.get("chartImageScale", 2))

                                image_bytes = generate_multi_candlestick_png(
                                    self.exchange.exchange,
                                    symbols_for_chart,
                                    chart_timeframe,
                                    chart_lookback,
                                    chart_theme,
                                    ma_windows,
                                    width=img_width,
                                    height=img_height,
                                    scale=img_scale,
                                )
                            except Exception as e:
                                logging.warning(
                                    f"Failed to generate composite chart image: {e}. Skipping Telegram image."
                                )

                        self.notifier.send(
                            message,
                            image_bytes=image_bytes,
                            image_caption=image_caption,
                        )
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
                            "Number of symbols with cached prices: "
                            f"{len(self.exchange.last_prices)}"
                        )

                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logging.info("Received keyboard interrupt. Shutting down...")
        finally:
            self.exchange.close()
