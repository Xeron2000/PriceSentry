"""Main CLI entry point for PriceSentry."""

import asyncio
import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SRC_DIR = ROOT_DIR / "src"

for candidate in (SRC_DIR, ROOT_DIR):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)


def get_user_input(prompt, default=None, secret=False):
    """Get user input with optional default value."""
    if default:
        suffix = f" [{default}]"
    else:
        suffix = ""

    if secret:
        import getpass

        value = getpass.getpass(f"{prompt}{suffix}: ")
    else:
        value = input(f"{prompt}{suffix}: ")

    if not value and default:
        return default
    return value


def interactive_config():
    """Interactive configuration setup."""
    print("\n" + "=" * 60)
    print("📝 PriceSentry 配置向导")
    print("=" * 60 + "\n")

    config = {}

    config["exchange"] = get_user_input("选择交易所", default="okx")
    config["defaultTimeframe"] = get_user_input("默认时间周期", default="5m")
    config["checkInterval"] = get_user_input("监控检查间隔", default="1m")
    config["defaultThreshold"] = float(get_user_input("价格变化阈值 (%)", default="1"))

    config["notificationChannels"] = ["telegram"]
    config["notificationTimezone"] = get_user_input("通知时区", default="Asia/Shanghai")

    symbols_input = get_user_input(
        "监控交易对 (逗号分隔，留空监控全部)",
        default="BTC/USDT,ETH/USDT",
    )
    config["notificationSymbols"] = [
        s.strip() for s in symbols_input.split(",") if s.strip()
    ]

    print("\n📱 Telegram 配置\n")
    telegram = {}

    telegram["token"] = get_user_input("Telegram Bot Token", secret=True)
    telegram["chatId"] = get_user_input("Telegram Chat ID", default="")
    config["telegram"] = telegram

    print("\n📊 图表设置\n")
    config["attachChart"] = True
    config["chartTimeframe"] = "5m"
    config["chartLookbackMinutes"] = 500
    config["chartTheme"] = "dark"
    config["chartIncludeMA"] = [7, 25]
    config["chartImageWidth"] = 1600
    config["chartImageHeight"] = 1200
    config["chartImageScale"] = 2

    print("\n" + "=" * 60)
    print("✅ 配置完成!")
    print("=" * 60 + "\n")

    return config


def ensure_config_exists():
    """Ensure configuration file exists, create from template if not."""
    CONFIG_FILE = Path("config/config.yaml")

    if CONFIG_FILE.exists():
        logging.info(f"Configuration file exists: {CONFIG_FILE}")
        return CONFIG_FILE.absolute()

    print("\n⚠️  未找到配置文件，开始交互式配置...\n")
    config = interactive_config()

    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

    import yaml

    with CONFIG_FILE.open("w", encoding="utf-8") as f:
        yaml.safe_dump(
            config, f, default_flow_style=False, allow_unicode=True, sort_keys=False
        )

    print(f"✅ 配置文件已保存: {CONFIG_FILE.absolute()}")
    print(f"📝 如需修改，请编辑: {CONFIG_FILE.absolute()}\n")

    return CONFIG_FILE.absolute()


def show_data_info():
    """Show data directory information."""
    data_dir = Path("config").absolute()
    print(f"📁 数据目录: {data_dir}")
    print(f"   - 配置文件: {data_dir / 'config.yaml'}")
    print(f"   - 市场数据: {data_dir / 'supported_markets.json'}")
    print()


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
            return True
        else:
            logging.warning("No market data received")
            return False
    except Exception as e:
        logging.warning(f"Failed to update markets: {e}")
        logging.warning(
            "You can try updating markets manually with: "
            f"uv run python tools/update_markets.py --exchanges {exchange}"
        )
        return False


def ensure_market_data(config):
    """Ensure market data is available before starting."""
    exchange = config.get("exchange", "binance")

    from pathlib import Path

    supported_markets_file = Path("config/supported_markets.json")

    if not supported_markets_file.exists():
        logging.info("Market data file not found, updating now...")
        success = update_markets(config)
        if not success:
            logging.warning(
                f"Failed to update markets for {exchange}. "
                "Please run update_markets.py manually:"
            )
            logging.info(
                f"  uv run python tools/update_markets.py --exchanges {exchange}"
            )
            return False
    else:
        import json

        with supported_markets_file.open("r") as f:
            markets_data = json.load(f)

        if exchange not in markets_data or not markets_data[exchange]:
            logging.info(f"No market data for {exchange}, updating now...")
            success = update_markets(config)
            if not success:
                logging.warning(
                    f"Failed to update markets for {exchange}. "
                    "Please run update_markets.py manually:"
                )
                logging.info(
                    f"  uv run python tools/update_markets.py --exchanges {exchange}"
                )
                return False

    logging.info(f"Market data verified for {exchange}")
    return True


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


def load_config(config_path):
    """Load configuration file."""
    import yaml

    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            f"Please create config file manually."
        )

    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main():
    """Main entry point."""
    from utils.setup_logging import setup_logging

    setup_logging()

    print("\n🚀 PriceSentry 启动中...\n")

    try:
        config_path = ensure_config_exists()
        show_data_info()

        config = load_config(config_path)

        # Ensure market data is available before starting
        print("📊 正在验证市场数据...")
        if not ensure_market_data(config):
            logging.error("❌ 无法获取市场数据，请检查网络或使用代理")
            logging.info("💡 提示:")
            logging.info(
                "   1. 手动运行: uv run python tools/update_markets.py --exchanges <exchange>"
            )
            logging.info("   2. 检查网络连接")
            logging.info("   3. Binance 可能需要代理")
            sys.exit(1)

        asyncio.run(run_monitoring())

    except KeyboardInterrupt:
        logging.info("\n\n👋 PriceSentry 已停止")
    except Exception as e:
        logging.error(f"❌ 启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
