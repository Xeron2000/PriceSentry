# core/sentry.py

import asyncio
import logging
import time
from queue import Empty, Queue
from threading import RLock
from typing import List, Optional, Set, Tuple

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
from utils.monitor_top_movers import monitor_top_movers
from utils.parse_timeframe import parse_timeframe
from utils.performance_monitor import performance_monitor
from utils.supported_markets import load_usdt_contracts


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
            self.notification_symbols: Optional[List[str]] = None
            self._notification_symbol_set: Set[str] = set()

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

            try:
                self._sync_symbols(exchange_name)
            except ValueError as exc:
                error_handler.handle_config_error(
                    exc,
                    {
                        "exchange": exchange_name,
                        "operation": "symbol_bootstrap",
                    },
                    ErrorSeverity.ERROR,
                )
                logging.error("Failed to bootstrap symbols: %s", exc)
                return

            if not getattr(self, "matched_symbols", None):
                logging.warning(
                    "No USDT contract symbols found for exchange %s. "
                    "Run tools/update_markets.py to refresh supported markets.",
                    exchange_name,
                )
                error_handler.handle_config_error(
                    Exception("No matched symbols found"),
                    {
                        "exchange": exchange_name,
                        "operation": "symbol_bootstrap",
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
            minutes_snapshot, _, check_interval, _, _ = self._snapshot_runtime_state()
            interval_minutes = max(check_interval / 60, 1)
            logging.info(
                "Check interval set to %.2f minutes (%s seconds)",
                interval_minutes,
                int(check_interval),
            )
            while True:
                self._process_config_updates()

                (
                    minutes_snapshot,
                    threshold_snapshot,
                    check_interval,
                    symbols_snapshot,
                    notification_filter_snapshot,
                ) = (
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
                            notification_filter_snapshot,
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
            interval_source = self.config.get("checkInterval") or timeframe
            try:
                interval_minutes = parse_timeframe(interval_source)
            except Exception as exc:
                logging.error(
                    "Failed to parse check interval '%s': %s. Using previous value.",
                    interval_source,
                    exc,
                )
                interval_seconds = getattr(
                    self,
                    "_check_interval",
                    getattr(self, "minutes", parse_timeframe("5m")) * 60,
                )
            else:
                if interval_minutes <= 0:
                    logging.warning(
                        "Parsed check interval '%s' resolved to %s minutes. "
                        "Falling back to timeframe duration.",
                        interval_source,
                        interval_minutes,
                    )
                    interval_minutes = max(self.minutes, 1)
                interval_seconds = max(interval_minutes, 1) * 60
            self._check_interval = interval_seconds
            self.check_interval_minutes = max(int(interval_seconds / 60) or 1, 1)
            self.threshold = self.config.get("defaultThreshold", 1)
            self._rebuild_notification_filter_locked()
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

        try:
            self._sync_symbols(exchange_name)
        except ValueError as exc:
            error_handler.handle_config_error(
                exc,
                {
                    "component": "PriceSentry",
                    "operation": "symbol_reload",
                    "exchange": exchange_name,
                },
                ErrorSeverity.ERROR,
            )
            logging.error("Symbol reload aborted: %s", exc)
            return

        if not self.matched_symbols:
            logging.warning("Symbol reload produced empty set; skipping websocket")
            error_handler.handle_config_error(
                Exception("No matched symbols found"),
                {
                    "component": "PriceSentry",
                    "operation": "symbol_reload",
                    "exchange": exchange_name,
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

    def _rebuild_notification_filter_locked(self) -> None:
        selection = self.config.get("notificationSymbols")
        monitored = list(getattr(self, "matched_symbols", []))
        monitored_set = set(monitored)

        if not selection:
            self.notification_symbols = None
            self._notification_symbol_set = set()
            return

        allowed: List[str] = []
        missing: List[str] = []

        if isinstance(selection, list):
            for raw_symbol in selection:
                if not isinstance(raw_symbol, str):
                    continue
                candidate = raw_symbol.strip()
                if not candidate:
                    continue
                if monitored_set and candidate not in monitored_set:
                    missing.append(candidate)
                    continue
                allowed.append(candidate)
        else:
            logging.warning(
                "Ignored notificationSymbols of type %s; expected list of symbol strings.",
                type(selection).__name__,
            )

        if missing:
            logging.warning(
                "Notification symbols ignored because they are not monitored: %s",
                ", ".join(sorted(set(missing))),
            )

        if allowed:
            self.notification_symbols = allowed
            self._notification_symbol_set = set(allowed)
        else:
            self.notification_symbols = None
            self._notification_symbol_set = set()

    def _sync_symbols(self, exchange_name: str) -> None:
        available_symbols = load_usdt_contracts(exchange_name)

        if not available_symbols:
            with self._config_lock:
                self.matched_symbols = []
                self._rebuild_notification_filter_locked()
            logging.warning(
                "No USDT contract symbols available for exchange %s. "
                "Ensure config/supported_markets.json is up-to-date.",
                exchange_name,
            )
            return

        selection = self.config.get("notificationSymbols")
        if not isinstance(selection, list) or not selection:
            message = (
                "Configuration must include at least one notification symbol. "
                "Save the configuration with a non-empty list before restarting."
            )
            logging.error(message)
            raise ValueError(message)

        available_set = set(available_symbols)
        monitored_symbols: List[str] = []
        missing_symbols: List[str] = []

        for raw_symbol in selection:
            if not isinstance(raw_symbol, str):
                continue
            candidate = raw_symbol.strip()
            if not candidate:
                continue
            if candidate in available_set:
                monitored_symbols.append(candidate)
            else:
                missing_symbols.append(candidate)

        if not monitored_symbols:
            detail = ""
            if missing_symbols:
                detail = (
                    " Missing symbols: "
                    + ", ".join(sorted(set(missing_symbols)))
                    + "."
                )
            message = (
                "No valid notification symbols remain after filtering against available contracts. "
                "Select at least one supported symbol and retry." + detail
            )
            logging.error(message)
            raise ValueError(message)

        with self._config_lock:
            self.matched_symbols = monitored_symbols
            self._rebuild_notification_filter_locked()

        if monitored_symbols:
            logging.info(
                "Loaded %s USDT contract symbols for exchange %s",
                len(monitored_symbols),
                exchange_name,
            )
        else:
            logging.warning(
                "No USDT contract symbols available for exchange %s. "
                "Ensure config/supported_markets.json is up-to-date.",
                exchange_name,
            )

    def _snapshot_runtime_state(self) -> Tuple[int, float, float, List[str], Optional[List[str]]]:
        with self._config_lock:
            minutes = getattr(self, "minutes", parse_timeframe("5m"))
            threshold = getattr(self, "threshold", 1.0)
            check_interval = getattr(
                self,
                "_check_interval",
                getattr(self, "minutes", parse_timeframe("5m")) * 60,
            )
            symbols_snapshot = list(getattr(self, "matched_symbols", []))
            notification_snapshot = (
                list(self.notification_symbols) if self.notification_symbols else None
            )
        return minutes, threshold, check_interval, symbols_snapshot, notification_snapshot
