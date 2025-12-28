"""Main CLI entry point for PriceSentry."""

import asyncio
import logging
import shutil
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SRC_DIR = ROOT_DIR / "src"

for candidate in (SRC_DIR, ROOT_DIR):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)


CONFIG_FILE = ROOT_DIR / "config" / "config.yaml"
CONFIG_EXAMPLE = ROOT_DIR / "config" / "config.yaml.example"


def ensure_config_exists():
    """Ensure configuration file exists, create from template if not."""
    if CONFIG_FILE.exists():
        return

    logging.info(f"Creating configuration file from template...")
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(CONFIG_EXAMPLE, CONFIG_FILE)
    logging.info(f"Configuration file created: {CONFIG_FILE}")

    print(
        f"""
⚠️  配置文件已创建: {CONFIG_FILE}
📝 请编辑配置文件，设置:
   - telegram.token: Telegram bot token
   - telegram.chatId: 你的 Telegram chat ID
   - exchange: 交易所 (binance/okx/bybit)
   - notificationSymbols: 要监控的交易对

编辑完成后，程序会自动开始运行...
"""
    )


def update_markets(config):
    """Update supported markets for configured exchange."""
    exchange = config.get("exchange", "binance")

    logging.info(f"Updating supported markets for {exchange}...")

    from utils.supported_markets import refresh_supported_markets

    try:
        refreshed = refresh_supported_markets([exchange])
        if refreshed:
            logging.info(
                f"Successfully updated markets for: {', '.join(sorted(refreshed))}"
            )
        else:
            logging.warning("No market data received")
    except Exception as e:
        logging.warning(f"Failed to update markets: {e}")


async def run_monitoring():
    """Run price monitoring service."""
    from utils.setup_logging import setup_logging
    from core.sentry import PriceSentry
    from notifications.telegram_bot_service import TelegramBotService

    bot_service = None
    try:
        sentry = PriceSentry()

        log_level = sentry.config.get("logLevel")
        if log_level:
            setup_logging(log_level)
        else:
            setup_logging()

        telegram_cfg = sentry.config.get("telegram", {})
        bot_service = TelegramBotService(telegram_cfg.get("token"))

        await bot_service.start()
        await sentry.run()
    except Exception as e:
        logging.error(f"Error in monitoring: {e}")
        raise
    finally:
        if bot_service:
            try:
                await bot_service.stop()
            except Exception:
                pass


def load_config():
    """Load configuration file."""
    import yaml

    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {CONFIG_FILE}\n"
            f"Please create config file manually."
        )

    with CONFIG_FILE.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main():
    """Main entry point."""
    from utils.setup_logging import setup_logging

    setup_logging()

    print("\n🚀 PriceSentry 启动中...\n")

    try:
        ensure_config_exists()

        config = load_config()

        update_markets(config)

        asyncio.run(run_monitoring())

    except KeyboardInterrupt:
        logging.info("\n\n👋 PriceSentry 已停止")
    except Exception as e:
        logging.error(f"❌ 启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
