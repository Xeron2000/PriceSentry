"""Default trading symbols based on market cap top 50 (excluding stablecoins)."""

# Market cap top 50 cryptocurrency trading pairs (USDT quoted, excluding stablecoins)
# Format: Symbol/USDT:USDT (for perpetual futures)
DEFAULT_TOP50_SYMBOLS = [
    "BTC/USDT:USDT",    # Bitcoin
    "ETH/USDT:USDT",    # Ethereum
    "BNB/USDT:USDT",    # BNB
    "XRP/USDT:USDT",    # XRP
    "SOL/USDT:USDT",    # Solana
    "DOGE/USDT:USDT",   # Dogecoin
    "ADA/USDT:USDT",    # Cardano
    "TRX/USDT:USDT",    # TRON
    "HYPE/USDT:USDT",   # Hyperliquid
    "SUI/USDT:USDT",    # Sui
    "BCH/USDT:USDT",    # Bitcoin Cash
    "LINK/USDT:USDT",   # Chainlink
    "ZEC/USDT:USDT",    # Zcash
    "HBAR/USDT:USDT",   # Hedera
    "XLM/USDT:USDT",    # Stellar
    "XMR/USDT:USDT",    # Monero
    "AVAX/USDT:USDT",   # Avalanche
    "SHIB/USDT:USDT",   # Shiba Inu
    "LEO/USDT:USDT",    # UNUS SED LEO
    "DOT/USDT:USDT",    # Polkadot
    "LTC/USDT:USDT",    # Litecoin
    "UNI/USDT:USDT",    # Uniswap
    "NEAR/USDT:USDT",   # NEAR Protocol
    "APT/USDT:USDT",    # Aptos
    "ICP/USDT:USDT",    # Internet Computer
    "PEPE/USDT:USDT",   # Pepe
    "KAS/USDT:USDT",    # Kaspa
    "RENDER/USDT:USDT", # Render
    "ARB/USDT:USDT",    # Arbitrum
    "OP/USDT:USDT",     # Optimism
    "INJ/USDT:USDT",    # Injective
    "VET/USDT:USDT",    # VeChain
    "ETC/USDT:USDT",    # Ethereum Classic
    "OKB/USDT:USDT",    # OKB
    "CRO/USDT:USDT",    # Cronos
    "FIL/USDT:USDT",    # Filecoin
    "MNT/USDT:USDT",    # Mantle
    "IMX/USDT:USDT",    # Immutable
    "STX/USDT:USDT",    # Stacks
    "TIA/USDT:USDT",    # Celestia
    "SEI/USDT:USDT",    # Sei
    "BONK/USDT:USDT",   # Bonk
    "WIF/USDT:USDT",    # dogwifhat
    "FLOKI/USDT:USDT",  # Floki
    "FET/USDT:USDT",    # Artificial Superintelligence Alliance
    "AAVE/USDT:USDT",   # Aave
    "QNT/USDT:USDT",    # Quant
    "FTM/USDT:USDT",    # Fantom / Sonic
    "ALGO/USDT:USDT",   # Algorand
    "THETA/USDT:USDT",  # Theta Network
]

# Language-specific prompts
PROMPTS = {
    "zh": {
        "language_select": "请选择语言 / Please select language:",
        "language_options": "1. 中文\n2. English",
        "welcome": "欢迎使用 PriceSentry 配置向导",
        "exchange_prompt": "选择交易所 (推荐: okx 或 bybit)",
        "timeframe_prompt": "默认时间周期",
        "check_interval_prompt": "监控检查间隔",
        "threshold_prompt": "价格变化阈值 (%)",
        "timezone_prompt": "通知时区",
        "symbols_prompt": "监控交易对",
        "symbols_hint": "输入 'default' 使用市值前50币种，或手动输入（逗号分隔）",
        "telegram_section": "Telegram 配置",
        "telegram_token_prompt": "Telegram Bot Token (从 @BotFather 获取)",
        "telegram_chatid_prompt": "Telegram Chat ID (从 @userinfobot 获取)",
        "chart_section": "图表设置",
        "config_complete": "配置完成!",
        "using_default_symbols": "使用默认市值前50币种",
    },
    "en": {
        "language_select": "请选择语言 / Please select language:",
        "language_options": "1. 中文\n2. English",
        "welcome": "Welcome to PriceSentry Configuration Wizard",
        "exchange_prompt": "Select exchange (recommended: okx or bybit)",
        "timeframe_prompt": "Default timeframe",
        "check_interval_prompt": "Check interval",
        "threshold_prompt": "Price change threshold (%)",
        "timezone_prompt": "Notification timezone",
        "symbols_prompt": "Trading pairs to monitor",
        "symbols_hint": "Enter 'default' for top 50 by market cap, or input manually (comma-separated)",
        "telegram_section": "Telegram Configuration",
        "telegram_token_prompt": "Telegram Bot Token (get from @BotFather)",
        "telegram_chatid_prompt": "Telegram Chat ID (get from @userinfobot)",
        "chart_section": "Chart Settings",
        "config_complete": "Configuration complete!",
        "using_default_symbols": "Using default top 50 symbols by market cap",
    },
}


def get_default_symbols(exchange: str) -> list[str]:
    """
    Get default symbols based on exchange format.

    Args:
        exchange: Exchange name (okx, bybit, binance)

    Returns:
        List of default symbols in the correct format for the exchange
    """
    # All exchanges use the same format: SYMBOL/USDT:USDT
    return DEFAULT_TOP50_SYMBOLS.copy()


def get_prompt(language: str, key: str) -> str:
    """
    Get localized prompt text.

    Args:
        language: Language code ('zh' or 'en')
        key: Prompt key

    Returns:
        Localized prompt text
    """
    lang = language if language in PROMPTS else "en"
    return PROMPTS[lang].get(key, PROMPTS["en"][key])
