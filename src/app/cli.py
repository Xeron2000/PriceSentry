"""Main CLI entry point for PriceSentry."""

import asyncio
import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"

for candidate in (SRC_DIR, ROOT_DIR):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)


from utils.setup_logging import setup_logging
from utils.supported_markets import refresh_supported_markets
from core.sentry import PriceSentry
from notifications.telegram_bot_service import TelegramBotService

CONFIG_FILE = ROOT_DIR / "config" / "config.yaml"
CONFIG_EXAMPLE = ROOT_DIR / "config" / "config.yaml.example"


def init_config():
    """Initialize configuration file if not exists."""
    if CONFIG_FILE.exists():
        logging.info(f"Configuration file already exists: {CONFIG_FILE}")
        return

    logging.info(f"Creating configuration file from template...")
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

    import shutil
    import yaml

    shutil.copyfile(CONFIG_EXAMPLE, CONFIG_FILE)
    logging.info(f"Configuration file created: {CONFIG_FILE}")

    config_content = f"""
⚠️  配置文件已创建: {CONFIG_FILE}
📝 请编辑配置文件，设置:
   - telegram.token: Telegram bot token
   - telegram.chatId: 你的 Telegram chat ID
   - exchange: 交易所 (binance/okx/bybit)
   - notificationSymbols: 要监控的交易对

编辑完成后，程序会自动开始运行...
"""
    print(config_content)


def update_markets(config):
    """Update supported markets for the configured exchange."""
    exchange = config.get("exchange", "binance")

    logging.info(f"Updating supported markets for {exchange}...")

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


async def run_monitoring(config):
    """Run the price monitoring service."""
    bot_service = None
    try:
        sentry = PriceSentry()

        log_level = sentry.config.get("logLevel")
        if log_level:
            setup_logging(log_level)
        else:
            setup_logging()

        telegram_cfg = config.get("telegram", {})
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
            f"Please run init_config first or create config file manually."
        )

    with CONFIG_FILE.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main():
    """Main entry point."""
    setup_logging()

    print("\n🚀 PriceSentry 启动中...\n")

    try:
        init_config()

        config = load_config()

        update_markets(config)

        asyncio.run(run_monitoring(config))

    except KeyboardInterrupt:
        logging.info("\n\n👋 PriceSentry 已停止")
    except Exception as e:
        logging.error(f"❌ 启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
