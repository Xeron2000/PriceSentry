# core/sentry.py

import asyncio
import logging
import time

from core.api import (
    set_exchange_instance,
    set_sentry_instance,
    start_api_server,
    update_api_data,
)
from core.notifier import Notifier
from utils.cache_manager import price_cache
from utils.chart import generate_multi_candlestick_png
from utils.config_validator import config_validator
from utils.error_handler import ErrorSeverity, error_handler
from utils.get_exchange import get_exchange
from utils.load_config import load_config
from utils.load_symbols_from_file import load_symbols_from_file
from utils.match_symbols import match_symbols
from utils.monitor_top_movers import monitor_top_movers
from utils.parse_timeframe import parse_timeframe
from utils.performance_monitor import performance_monitor


class PriceSentry:
    def __init__(self):
        try:
            # Start performance monitoring
            performance_monitor.start()

            # Load configuration
            self.config = load_config()

            # Validate configuration
            validation_result = config_validator.validate_config(self.config)
            if not validation_result.is_valid:
                error_handler.handle_config_error(
                    Exception("Configuration validation failed"),
                    {
                        "component": "PriceSentry",
                        "operation": "config_validation",
                        "errors": validation_result.errors,
                    },
                    ErrorSeverity.CRITICAL,
                )
                raise ValueError(
                    f"Configuration validation failed: {validation_result.errors}"
                )

            # Log validation warnings and info
            if validation_result.warnings:
                for warning in validation_result.warnings:
                    logging.warning(f"Configuration warning: {warning}")

            if validation_result.info:
                for info in validation_result.info:
                    logging.info(f"Configuration info: {info}")

            self.notifier = Notifier(self.config)

            exchange_name = self.config.get("exchange", "binance")
            self.exchange = get_exchange(exchange_name)

            symbols_file_path = self.config.get("symbolsFilePath", "config/symbols.txt")
            symbols = load_symbols_from_file(symbols_file_path)

            self.matched_symbols = match_symbols(symbols, exchange_name)

            if not self.matched_symbols:
                logging.warning(
                    "No matched symbols found. Please check your symbols file."
                )
                error_handler.handle_config_error(
                    Exception("No matched symbols found"),
                    {"symbols_file": symbols_file_path, "exchange": exchange_name},
                    ErrorSeverity.WARNING,
                )
                return

            default_timeframe = self.config.get("defaultTimeframe", "5m")
            self.minutes = parse_timeframe(default_timeframe)

            self.threshold = self.config.get("defaultThreshold", 1)

            # 启动API服务器
            try:
                self.api_thread = start_api_server()
                logging.info("API server started successfully")

                # 设置API数据存储的实例引用
                set_sentry_instance(self)
                set_exchange_instance(self.exchange)

            except Exception as e:
                logging.error(f"Failed to start API server: {e}")
                # API服务器启动失败不应影响主要功能

            logging.info("PriceSentry initialized successfully")

        except Exception as e:
            error_handler.handle_config_error(
                e,
                {"component": "PriceSentry", "operation": "initialization"},
                ErrorSeverity.CRITICAL,
            )
            raise

    async def run(self):
        if not self.matched_symbols:
            return

        try:
            self.exchange.start_websocket(self.matched_symbols)
            logging.info(
                f"Started WebSocket connection for {len(self.matched_symbols)} symbols"
            )
        except Exception as e:
            error_handler.handle_network_error(
                e,
                {
                    "component": "PriceSentry",
                    "operation": "websocket_start",
                    "symbols_count": len(self.matched_symbols),
                },
                ErrorSeverity.ERROR,
            )
            raise

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

                    try:
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

                            # 更新API数据 - 发送告警信息
                            try:
                                alert_data = {
                                    "message": message,
                                    "severity": "warning",
                                    "top_movers": top_movers_sorted,
                                    "threshold": self.threshold,
                                    "minutes": self.minutes,
                                }

                                # 为每个top mover创建单独的告警
                                for symbol, change_percent in top_movers_sorted[
                                    :5
                                ]:  # 前5个
                                    price = self.exchange.last_prices.get(symbol, 0)
                                    individual_alert = {
                                        "symbol": symbol,
                                        "message": (
                                            f"{symbol} 价格变动 {change_percent:.2f}%"
                                        ),
                                        "severity": "warning"
                                        if abs(change_percent) > 5
                                        else "info",
                                        "price": price,
                                        "change": change_percent,
                                        "threshold": self.threshold,
                                        "minutes": self.minutes,
                                    }
                                    update_api_data(
                                        alerts=individual_alert, sentry_instance=self
                                    )

                                # 同时更新整体告警
                                update_api_data(alerts=alert_data, sentry_instance=self)

                                logging.debug("API data updated with alert information")
                            except Exception as e:
                                logging.error(
                                    f"Failed to update API data with alerts: {e}"
                                )
                            # Build a composite chart image for top 6 movers and
                            # send only the image via Telegram
                            attach_chart = self.config.get("attachChart", False)
                            image_bytes = None
                            image_caption = ""  # no text per requirement
                            chart_metadata = None
                            if attach_chart and top_movers_sorted:
                                try:
                                    symbols_for_chart = [
                                        s for s, _ in top_movers_sorted[:6]
                                    ]
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

                                    img_width = int(
                                        self.config.get("chartImageWidth", 1200)
                                    )
                                    img_height = int(
                                        self.config.get("chartImageHeight", 900)
                                    )
                                    img_scale = int(
                                        self.config.get("chartImageScale", 2)
                                    )

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
                                    chart_metadata = {
                                        "symbols": symbols_for_chart,
                                        "timeframe": chart_timeframe,
                                        "lookbackMinutes": chart_lookback,
                                        "theme": chart_theme,
                                        "width": img_width,
                                        "height": img_height,
                                        "scale": img_scale,
                                    }
                                except Exception as e:
                                    logging.warning(
                                        "Failed to generate composite chart image: "
                                        f"{e}. Skipping Telegram image."
                                    )
                                    image_bytes = None
                                    chart_metadata = None

                            self.notifier.send(
                                message,
                                image_bytes=image_bytes,
                                image_caption=image_caption,
                                chart_metadata=chart_metadata,
                            )
                        else:
                            logging.info(
                                "No price movements exceeding threshold detected"
                            )
                    except Exception as e:
                        error_handler.handle_api_error(
                            e,
                            {
                                "component": "PriceSentry",
                                "operation": "monitor_top_movers",
                            },
                            ErrorSeverity.ERROR,
                        )
                        logging.error(f"Error in price monitoring: {e}")
                        continue

                    last_check_time = current_time

                if int(current_time) % 60 == 0:
                    logging.debug("Checking WebSocket connection status")
                    if not self.exchange.ws_connected:
                        logging.warning(
                            "WebSocket connection disconnected, attempting to reconnect"
                        )
                        try:
                            self.exchange.check_ws_connection()
                        except Exception as e:
                            error_handler.handle_network_error(
                                e,
                                {
                                    "component": "PriceSentry",
                                    "operation": "websocket_reconnect",
                                },
                                ErrorSeverity.WARNING,
                            )
                    if hasattr(self.exchange, "last_prices"):
                        logging.debug(
                            "Number of symbols with cached prices: "
                            f"{len(self.exchange.last_prices)}"
                        )

                        # 定期更新API价格数据
                        try:
                            update_api_data(
                                prices=self.exchange.last_prices.copy(),
                                stats={
                                    "cache": price_cache.get_stats(),
                                    "performance": performance_monitor.get_stats(),
                                },
                                sentry_instance=self,
                            )
                            logging.debug("API price data updated")
                        except Exception as e:
                            logging.error(f"Failed to update API price data: {e}")

                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logging.info("Received keyboard interrupt. Shutting down...")
        finally:
            try:
                self.exchange.close()
            except Exception as e:
                error_handler.handle_api_error(
                    e,
                    {"component": "PriceSentry", "operation": "cleanup"},
                    ErrorSeverity.WARNING,
                )
