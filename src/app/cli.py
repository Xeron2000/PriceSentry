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


def print_section(title: str, char: str = "─"):
    """Print a section header."""
    print(f"\n📌 {title}")
    print(char * 40)


def print_help(text: str):
    """Print help text."""
    print(text)
    print()


def validate_exchange(value: str, language: str) -> tuple[bool, str]:
    """Validate exchange input."""
    from utils.default_symbols import VALID_EXCHANGES, get_prompt

    value = value.lower().strip()
    if value in VALID_EXCHANGES:
        return True, value
    return False, get_prompt(language, "invalid_exchange")


def validate_timeframe(value: str, language: str) -> tuple[bool, str]:
    """Validate timeframe input."""
    from utils.default_symbols import VALID_TIMEFRAMES, get_prompt

    value = value.lower().strip()
    if value in VALID_TIMEFRAMES:
        return True, value
    return False, get_prompt(language, "invalid_timeframe")


def validate_positive_number(value: str, language: str) -> tuple[bool, float | str]:
    """Validate positive number input."""
    from utils.default_symbols import get_prompt

    try:
        num = float(value)
        if num > 0:
            return True, num
        return False, get_prompt(language, "invalid_threshold")
    except ValueError:
        return False, get_prompt(language, "invalid_number")


def get_validated_input(prompt: str, default: str, validator, language: str, secret: bool = False) -> str:
    """Get user input with validation."""
    while True:
        value = get_user_input(prompt, default=default, secret=secret)
        if not value and default:
            value = default
        valid, result = validator(value, language)
        if valid:
            return result
        print(f"❌ {result}")


def ask_yes_no(prompt: str, language: str, default: bool = False) -> bool:
    """Ask a yes/no question."""
    from utils.default_symbols import get_prompt

    hint = get_prompt(language, "yes_no_hint")
    default_str = "y" if default else "n"
    response = get_user_input(f"{prompt} {hint}", default=default_str).lower().strip()
    return response in ("y", "yes", "是")


def interactive_config():
    """Interactive configuration setup with language selection and default symbols."""
    from utils.default_symbols import get_prompt

    # Language selection
    print("\n" + "=" * 60)
    print("Please select language / 请选择语言")
    print("=" * 60)
    print("1. English")
    print("2. 中文")
    print()

    lang_choice = input("Enter option [1]: ").strip() or "1"
    language = "en" if lang_choice == "1" else "zh"

    # Welcome message
    print("\n" + "=" * 60)
    print(f"🚀 {get_prompt(language, 'welcome')}")
    print("=" * 60)

    config = {}

    # ==================== Exchange Selection ====================
    print_section(get_prompt(language, "exchange_prompt"))
    print_help(get_prompt(language, "exchange_help"))

    config["exchange"] = get_validated_input(
        get_prompt(language, "exchange_prompt"),
        default="okx",
        validator=validate_exchange,
        language=language,
    )

    # ==================== Timeframe Selection ====================
    print_section(get_prompt(language, "timeframe_prompt"))
    print_help(get_prompt(language, "timeframe_help"))
    print(f"   {get_prompt(language, 'timeframe_options')}\n")

    config["defaultTimeframe"] = get_validated_input(
        get_prompt(language, "timeframe_prompt"),
        default="5m",
        validator=validate_timeframe,
        language=language,
    )

    # ==================== Check Interval ====================
    print_section(get_prompt(language, "check_interval_prompt"))
    print_help(get_prompt(language, "check_interval_help"))
    print(f"   {get_prompt(language, 'timeframe_options')}\n")

    config["checkInterval"] = get_validated_input(
        get_prompt(language, "check_interval_prompt"),
        default="1m",
        validator=validate_timeframe,
        language=language,
    )

    # ==================== Threshold ====================
    print_section(get_prompt(language, "threshold_prompt"))
    print_help(get_prompt(language, "threshold_help"))
    print(get_prompt(language, "threshold_examples"))
    print()

    config["defaultThreshold"] = get_validated_input(
        get_prompt(language, "threshold_prompt"),
        default="1",
        validator=validate_positive_number,
        language=language,
    )

    # ==================== Timezone ====================
    config["notificationChannels"] = ["telegram"]
    config["notificationTimezone"] = get_user_input(get_prompt(language, "timezone_prompt"), default="Asia/Shanghai")

    # ==================== Trading Pairs ====================
    print_section(get_prompt(language, "symbols_prompt"))
    print_help(get_prompt(language, "symbols_mode_help"))
    print(f"   {get_prompt(language, 'symbols_format_help')}\n")

    symbols_input = input("[auto]: ").strip()

    if not symbols_input or symbols_input.lower() == "auto":
        config["notificationSymbols"] = "auto"
        print(f"✅ {get_prompt(language, 'using_auto_mode')}")
    elif symbols_input.lower() == "default":
        config["notificationSymbols"] = "default"
        print(f"✅ {get_prompt(language, 'using_default_symbols')}")
    else:
        config["notificationSymbols"] = [
            s.strip() + (":USDT" if ":" not in s else "") for s in symbols_input.split(",") if s.strip()
        ]

    # ==================== Telegram Configuration ====================
    print_section(get_prompt(language, "telegram_section"))
    print_help(get_prompt(language, "telegram_token_help"))

    telegram = {}
    telegram["token"] = get_user_input(get_prompt(language, "telegram_token_prompt"), secret=True)

    print()
    print_help(get_prompt(language, "telegram_chatid_help"))
    print(f"   {get_prompt(language, 'telegram_chatid_optional')}\n")

    telegram["chatId"] = get_user_input(get_prompt(language, "telegram_chatid_prompt"), default="")
    config["telegram"] = telegram

    # ==================== Chart Settings (defaults) ====================
    config["attachChart"] = True
    config["chartTimeframe"] = "5m"
    config["chartLookbackMinutes"] = 500
    config["chartTheme"] = "dark"
    config["chartImageWidth"] = 1600
    config["chartImageHeight"] = 1200
    config["chartImageScale"] = 2

    # ==================== Advanced Configuration (Optional) ====================
    print_section(get_prompt(language, "advanced_config_prompt"))
    print(f"   {get_prompt(language, 'advanced_config_hint')}\n")

    if ask_yes_no(get_prompt(language, "advanced_config_prompt"), language, default=False):
        # Notification Cooldown
        print()
        print_help(get_prompt(language, "cooldown_help"))
        cooldown_input = get_user_input(get_prompt(language, "cooldown_prompt"), default="300")
        try:
            config["notificationCooldown"] = int(cooldown_input)
        except ValueError:
            config["notificationCooldown"] = 300

        # Priority Thresholds
        print()
        print_help(get_prompt(language, "priority_help"))

        priority_thresholds = {}
        low_input = get_user_input(get_prompt(language, "priority_low_prompt"), default="0.5")
        medium_input = get_user_input(get_prompt(language, "priority_medium_prompt"), default="1")
        high_input = get_user_input(get_prompt(language, "priority_high_prompt"), default="3")

        try:
            priority_thresholds["low"] = float(low_input)
            priority_thresholds["medium"] = float(medium_input)
            priority_thresholds["high"] = float(high_input)
            config["priorityThresholds"] = priority_thresholds
        except ValueError:
            pass

        # Chart detailed settings
        print()
        print_section(get_prompt(language, "chart_section"))

        chart_theme = get_user_input("Chart theme (dark/light)", default="dark")
        if chart_theme.lower() in ("dark", "light"):
            config["chartTheme"] = chart_theme.lower()

        chart_lookback = get_user_input("Chart lookback minutes", default="500")
        try:
            config["chartLookbackMinutes"] = int(chart_lookback)
        except ValueError:
            pass

    print("\n" + "=" * 60)
    print(f"✅ {get_prompt(language, 'config_complete')}")
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
        yaml.safe_dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

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
            logging.info(f"Successfully updated markets for: {', '.join(sorted(refreshed))}")
            return True
        else:
            logging.warning("No market data received")
            return False
    except Exception as e:
        logging.warning(f"Failed to update markets: {e}")
        logging.warning(
            f"You can try updating markets manually with: uv run python tools/update_markets.py --exchanges {exchange}"
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
            logging.warning(f"Failed to update markets for {exchange}. Please run update_markets.py manually:")
            logging.info(f"  uv run python tools/update_markets.py --exchanges {exchange}")
            return False
    else:
        import json

        with supported_markets_file.open("r") as f:
            markets_data = json.load(f)

        if exchange not in markets_data or not markets_data[exchange]:
            logging.info(f"No market data for {exchange}, updating now...")
            success = update_markets(config)
            if not success:
                logging.warning(f"Failed to update markets for {exchange}. Please run update_markets.py manually:")
                logging.info(f"  uv run python tools/update_markets.py --exchanges {exchange}")
                return False

    logging.info(f"Market data verified for {exchange}")
    return True


async def run_monitoring():
    """Run price monitoring service."""
    from core.sentry import PriceSentry
    from notifications.telegram_bot_service import TelegramBotService
    from utils.setup_logging import setup_logging

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
        raise FileNotFoundError(f"Configuration file not found: {config_path}\nPlease create config file manually.")

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
            logging.info("   1. 手动运行: uv run python tools/update_markets.py --exchanges <exchange>")
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
