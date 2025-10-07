# core/sentry.py

import asyncio
import logging
import time
from queue import Empty, Queue
from threading import RLock
from typing import List, Tuple

from core.api import (
    set_exchange_instance,
    set_sentry_instance,
    start_api_server,
    update_api_data,
)
from core.config_manager import ConfigUpdateEvent, config_manager
from core.notifier import Notifier
from utils.cache_manager import price_cache
from utils.chart import generate_multi_candlestick_png
from utils.config_validator import config_validator
from utils.error_handler import ErrorSeverity, error_handler
from utils.get_exchange import get_exchange
from utils.load_symbols_from_file import load_symbols_from_file
from utils.match_symbols import match_symbols
from utils.monitor_top_movers import monitor_top_movers
from utils.parse_timeframe import parse_timeframe
from utils.performance_monitor import performance_monitor


def load_config() -> dict:
    """Backward compatible shim for legacy tests mocking core.sentry.load_config."""
    return config_manager.get_config()


class PriceSentry:
    def __init__(self):
        try:
            # Start performance monitoring
            performance_monitor.start()

            self._config_lock = RLock()
            self._config_events: "Queue[ConfigUpdateEvent]" = Queue()

            # Load configuration (patchable for unit tests while defaulting to manager data)
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

            self._sync_symbols(exchange_name)
            if not getattr(self, "matched_symbols", None):
                logging.warning(
                    "No matched symbols found. Please check your symbols file."
                )
                error_handler.handle_config_error(
                    Exception("No matched symbols found"),
                    {
                        "symbols_file": self.config.get(
                            "symbolsFilePath", "config/symbols.txt"
                        ),
                        "exchange": exchange_name,
                    },
                    ErrorSeverity.WARNING,
                )
                return

            self._refresh_runtime_settings()

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

            config_manager.subscribe(self._enqueue_config_update)
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

        last_check_time = 0

        try:
            logging.info("Entering main loop, starting price movement monitoring")
            minutes_snapshot, _, check_interval, _ = self._snapshot_runtime_state()
            logging.info(
                "Check interval set to %s minutes (%s seconds)",
                minutes_snapshot,
                int(check_interval),
            )
            while True:
                self._process_config_updates()

                minutes_snapshot, threshold_snapshot, check_interval, symbols_snapshot = (
                    self._snapshot_runtime_state()
                )

                current_time = time.time()

                if current_time - last_check_time >= check_interval:
                    logging.info(
                        "Checking price movements, %s seconds since last check",
                        int(current_time - last_check_time),
                    )

                    try:
                        if not symbols_snapshot:
                            logging.warning("No symbols available for monitoring")
                            last_check_time = current_time
                            continue

                        result = await monitor_top_movers(
                            minutes_snapshot,
                            symbols_snapshot,
                            threshold_snapshot,
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
                                    "threshold": threshold_snapshot,
                                    "minutes": minutes_snapshot,
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
                                        "minutes": minutes_snapshot,
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
                                    chart_timezone = self.config.get(
                                        "notificationTimezone", "Asia/Shanghai"
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
                                        timezone=chart_timezone,
                                    )
                                    chart_metadata = {
                                        "symbols": symbols_for_chart,
                                        "timeframe": chart_timeframe,
                                        "lookbackMinutes": chart_lookback,
                                        "theme": chart_theme,
                                        "width": img_width,
                                        "height": img_height,
                                        "scale": img_scale,
                                        "timezone": chart_timezone,
                                    }
                                except Exception as e:
                                    logging.warning(
                                        "Failed to generate composite chart image: "
                                        f"{e}. Skipping Telegram image."
                                    )
                                    image_bytes = None
                                    chart_metadata = None

                            send_kwargs = {
                                "image_bytes": image_bytes,
                                "image_caption": image_caption,
                            }
                            if chart_metadata is not None:
                                send_kwargs["chart_metadata"] = chart_metadata

                            self.notifier.send(message, **send_kwargs)
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

    def _enqueue_config_update(self, event: ConfigUpdateEvent) -> None:
        """Receive config updates from ConfigManager on background threads."""
        try:
            self._config_events.put_nowait(event)
        except Exception:
            # Fallback to blocking put; queue is unbounded but guard just in case.
            self._config_events.put(event)

    def _process_config_updates(self) -> None:
        while True:
            try:
                event = self._config_events.get_nowait()
            except Empty:
                break
            self._apply_config_update(event)

    def _apply_config_update(self, event: ConfigUpdateEvent) -> None:
        start_time = time.time()
        changed_keys = ", ".join(sorted(event.diff.changed_keys)) or "<none>"
        logging.info("Processing configuration update; changed keys: %s", changed_keys)
        if event.warnings:
            for warning in event.warnings:
                logging.warning("Configuration warning: %s", warning)

        with self._config_lock:
            self.config = event.new_config

        self._refresh_runtime_settings()

        if event.diff.requires_symbol_reload:
            self._reload_runtime_components(event)

        elapsed = time.time() - start_time
        if elapsed > 5:
            logging.warning(
                "Configuration update processing exceeded 5s target: %.2fs",
                elapsed,
            )
        else:
            logging.info("Configuration update applied in %.2fs", elapsed)

    def _refresh_runtime_settings(self) -> None:
        with self._config_lock:
            timeframe = self.config.get("defaultTimeframe", "5m")
            try:
                minutes = parse_timeframe(timeframe)
            except Exception as exc:
                logging.error(
                    "Failed to parse timeframe '%s': %s. Using previous value.",
                    timeframe,
                    exc,
                )
                minutes = getattr(self, "minutes", parse_timeframe("5m"))
            self.minutes = minutes
            self._check_interval = self.minutes * 60
            self.threshold = self.config.get("defaultThreshold", 1)
            if hasattr(self, "notifier") and self.notifier is not None:
                self.notifier.update_config(self.config)

    def _reload_runtime_components(self, event: ConfigUpdateEvent) -> None:
        exchange_name = self.config.get("exchange", "binance")
        logging.info(
            "Reloading exchange and symbol set due to config update (keys: %s)",
            ", ".join(sorted(event.diff.changed_keys)) or "<none>",
        )

        try:
            self.exchange.close()
        except Exception as exc:
            logging.warning(f"Failed to close existing exchange cleanly: {exc}")

        try:
            self.exchange = get_exchange(exchange_name)
        except Exception as exc:
            error_handler.handle_config_error(
                exc,
                {
                    "component": "PriceSentry",
                    "operation": "exchange_reload",
                    "exchange": exchange_name,
                },
                ErrorSeverity.CRITICAL,
            )
            logging.error("Exchange reload aborted: %s", exc)
            return

        self._sync_symbols(exchange_name)
        if not self.matched_symbols:
            logging.warning("Symbol reload produced empty set; skipping websocket")
            error_handler.handle_config_error(
                Exception("No matched symbols found"),
                {
                    "component": "PriceSentry",
                    "operation": "symbol_reload",
                    "exchange": exchange_name,
                    "symbols_file": self.config.get("symbolsFilePath", "config/symbols.txt"),
                },
                ErrorSeverity.WARNING,
            )
            return

        try:
            self.exchange.start_websocket(self.matched_symbols)
        except Exception as exc:
            error_handler.handle_network_error(
                exc,
                {
                    "component": "PriceSentry",
                    "operation": "websocket_restart",
                    "symbols_count": len(self.matched_symbols),
                },
                ErrorSeverity.ERROR,
            )
            logging.error("Failed to restart websocket after config change: %s", exc)
            return

        set_exchange_instance(self.exchange)
        set_sentry_instance(self)
        logging.info(
            "Exchange and symbol sets reloaded successfully (%s symbols)",
            len(self.matched_symbols),
        )

    def _sync_symbols(self, exchange_name: str) -> None:
        symbols_file_path = self.config.get("symbolsFilePath", "config/symbols.txt")
        symbols = load_symbols_from_file(symbols_file_path)
        matched = match_symbols(symbols, exchange_name)
        with self._config_lock:
            self.matched_symbols = matched
        logging.info(
            "Loaded %s matched symbols from %s",
            len(matched),
            symbols_file_path,
        )

    def _snapshot_runtime_state(self) -> Tuple[int, float, float, List[str]]:
        with self._config_lock:
            minutes = getattr(self, "minutes", parse_timeframe("5m"))
            threshold = getattr(self, "threshold", 1.0)
            check_interval = getattr(self, "_check_interval", minutes * 60)
            symbols_snapshot = list(getattr(self, "matched_symbols", []))
        return minutes, threshold, check_interval, symbols_snapshot
