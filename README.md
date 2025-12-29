<div align="center">
  <img src="./img/logo.svg" width="100" alt="Project Logo">
</div>

<div align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=34&pause=1000&center=true&vCenter=true&width=435&lines=PriceSentry" alt="Typing SVG">
</div>

<br>
<div align="center">
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT">
  </a>
  <a href="https://github.com/Xeron2000/PriceSentry/stargazers">
    <img src="https://img.shields.io/github/stars/Xeron2000/PriceSentry?style=social" alt="Star on GitHub">
  </a>
</div>

<h3 align="center">Lightweight Cryptocurrency Futures Price Monitoring Tool 🚨</h3>
<h4 align="center" style="color: #666;">Track · Analyze · Stay Sharp</h4>

<p align="center">
  <a href="README.md">English</a> |
  <a href="README_CN.md">简体中文</a>
</p>

---

## 📖 Table of Contents

- [Origin Story](#origin-story)
- [Features](#features)
- [Quick Start](#quick-start)
  - [One-Command Setup (Recommended)](#one-command-setup-recommended)
  - [Manual Installation](#manual-installation)
- [Configuration](#configuration)
  - [Recommended: Manual Configuration](#recommended-manual-configuration)
  - [Get Market Data](#get-market-data)
  - [Interactive Setup](#interactive-setup)
  - [Important Notes](#important-notes)
  - [Advanced Configuration](#advanced-configuration)
- [Common Commands](#common-commands)
- [Troubleshooting](#troubleshooting)
- [Screenshots](#screenshots)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Development Guide](#development-guide)
- [FAQ](#faq)
- [Contributing](#contributing)
- [License](#license)

---

## Origin Story

As a futures trader focusing on short-term opportunities, I spend most of my time in a market that lacks volatility, and constantly watching the charts drains my energy. Yet when there's real market movement, I want to capture the momentum immediately. Available tools either have high subscription costs or lack practical features for real trading scenarios, so I decided to build an automated monitoring solution.

PriceSentry was born—designed for short-term futures traders facing similar challenges, completely open-source and free, leaving your energy for decision-making and delegating repetitive monitoring to the program.

---

## Features

- ✅ Support for Binance, OKX, and Bybit futures price monitoring with customizable trading pairs
- ✅ Telegram notifications for price movements and health checks, with multi-user binding support
- ✅ YAML-driven configuration with built-in validation and caching mechanisms
- ✅ Performance monitoring, circuit breaking, and exponential backoff retry for stability
- ✅ Optional candlestick chart attachments for visual price trend analysis
- ✅ Flexible notification filters to only push pairs you care about

> Want to try it first? Subscribe to [PriceSentry Futures Monitor](https://t.me/pricesentry) channel for instant push notifications.

---

## Quick Start

### One-Command Setup (Recommended)

```bash
uvx --from git+https://github.com/Xeron2000/PriceSentry.git pricesentry
```

**First Run Steps:**
1. Interactive configuration or manually edit `config/config.yaml`
2. Set Telegram Bot Token (get from [@BotFather](https://t.me/botfather))
3. Set Telegram Chat ID (get from [@userinfobot](https://t.me/userinfobot))
4. **Recommended: Use OKX or Bybit** (Binance has regional restrictions)
5. The program will automatically update market data and start monitoring

**File Locations:**
```
current_directory/
├── config/
│   ├── config.yaml              # Configuration file
│   └── supported_markets.json   # Market data (auto-fetched)
```

### Manual Installation

```bash
# Clone repository
git clone https://github.com/Xeron2000/PriceSentry.git
cd PriceSentry

# Install dependencies
uv sync

# 1. Create configuration file
uv run python tools/init_config.py

# 2. Edit configuration
vi config/config.yaml

# 3. Update market data (fetch real data using script)
uv run python tools/update_markets.py

# 4. Start monitoring
uv run python -m app.cli
```

---

## Configuration

### Recommended: Manual Configuration

Edit `config/config.yaml` (recommended):

```yaml
# Use OKX or Bybit to avoid regional restrictions
exchange: "okx"  # okx, bybit, binance

# Default timeframe (candlestick aggregation window)
defaultTimeframe: "5m"  # 1m, 5m, 15m, 1h, 1d

# Monitoring task check frequency
checkInterval: "1m"

# Price change threshold (percentage)
defaultThreshold: 1

# Notification channels
notificationChannels:
  - "telegram"

# Notification symbols (leave empty to push all monitored contract pairs)
notificationSymbols:
  - "BTC/USDT:USDT"
  - "ETH/USDT:USDT"
  - "SOL/USDT:USDT"

# Telegram bot configuration
telegram:
  # Get from @BotFather, format: numbers:characters
  token: "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
  # Get from @userinfobot, pure numbers
  chatId: "123456789"

# Notification timezone
notificationTimezone: "Asia/Shanghai"

# Attach price chart in notifications
attachChart: true

# Chart rendering settings (effective when attachChart is true)
chartTimeframe: "5m"
chartLookbackMinutes: 500
chartTheme: "dark"          # "dark" | "light"
chartImageWidth: 1600
chartImageHeight: 1200
chartImageScale: 2
```

### Get Market Data

Use the `tools/update_markets.py` script to fetch real trading pair data:

```bash
# Update market data for a single exchange
uv run python tools/update_markets.py --exchanges okx

# Update market data for multiple exchanges
uv run python tools/update_markets.py --exchanges okx bybit

# Update market data for all supported exchanges
uv run python tools/update_markets.py
```

**Notes:**
- The script fetches the latest trading pair list from exchange APIs
- Data is saved to `config/supported_markets.json`
- OKX/Bybit have no regional restrictions and can be accessed normally
- Binance may require a proxy in some regions

### Interactive Setup

When running the `pricesentry` command for the first time, if the configuration file doesn't exist, it will automatically enter the configuration wizard and then fetch market data.

**Note:** Interactive configuration may have issues in non-interactive environments (like shell scripts), so **manual editing of the configuration file is recommended**.

### Important Notes

1. **Binance Regional Restrictions:**
   - Binance API may be restricted in some regions (e.g., China)
   - **Recommended: Use OKX or Bybit**

2. **Telegram Token Format:**
   - Must be in `numbers:characters` format
   - Example: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`
   - ❌ Wrong: `my_token_123`
   - ✅ Correct: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

3. **Chat ID Format:**
   - Must be pure numbers
   - Get from [@userinfobot](https://t.me/userinfobot)

4. **Trading Pair Format:**
   - OKX/Bybit use `BTC/USDT:USDT` format
   - Binance uses `BTC/USDT:USDT` format
   - Ensure format matches the exchange

### Advanced Configuration

For advanced configuration options:
```bash
uv run python tools/init_config.py
```

Supported parameters:
- `--force`: Overwrite existing configuration
- `--non-interactive`: Copy template directly

---

## Common Commands

| Function | Command |
| --- | --- |
| Start monitoring | `uv run python -m app.cli` or `pricesentry` |
| Edit config | `vi config/config.yaml` |
| Re-configure | `rm config/config.yaml && pricesentry` |
| Update markets | `uv run python tools/update_markets.py` |
| Update specific exchange | `uv run python tools/update_markets.py --exchanges okx` |
| Run tests | `uv run pytest` |
| Run linter | `uv run ruff check src/` |
| Format code | `uv run ruff format src/` |

---

## Troubleshooting

### 1. Error: `No valid notification symbols`

**Cause:** Trading pair format is incorrect or market data hasn't been updated

**Solution:**
```bash
# 1. Check trading pair format in configuration file
vi config/config.yaml

# 2. Ensure format is "BTC/USDT:USDT" (note the colon)

# 3. Update market data
uv run python tools/update_markets.py --exchanges okx

# 4. Restart
uv run python -m app.cli
```

### 2. Error: `'PriceSentry' object has no attribute 'matched_symbols'`

**Cause:** This is a bug in older versions, fixed in the latest version

**Solution:**
```bash
# Pull latest code
git pull origin main

# Reinstall
uv sync

# Restart
uv run python -m app.cli
```

### 3. Binance API Connection Timeout

**Cause:** Binance API is restricted in some regions

**Solution:**
```yaml
# Modify config/config.yaml
exchange: "okx"  # or "bybit"
```

### 4. Telegram Messages Not Received

**Checklist:**
- ✅ Is token format correct (`numbers:characters`)
- ✅ Is Chat ID correct (pure numbers)
- ✅ Have you sent `/start` command to the bot
- ✅ Is network working (some regions require proxy)

---

## Screenshots

<div align="center">
  <img src="https://raw.githubusercontent.com/Xeron2000/PriceSentry/refs/heads/main/img/tg.jpg" alt="Telegram Notification Example" width="520">
</div>

---

## Project Structure

```
PriceSentry/
├── src/
│   ├── app/              # Application entry (CLI)
│   │   ├── cli.py        # Command-line interface
│   │   └── runner.py     # Runner
│   ├── core/             # Core logic
│   │   ├── config_manager.py  # Configuration management
│   │   ├── notifier.py        # Notification dispatcher
│   │   └── sentry.py          # Monitoring engine
│   ├── exchanges/        # Exchange adapters
│   │   ├── base.py       # Base class
│   │   ├── binance.py    # Binance implementation
│   │   ├── okx.py        # OKX implementation
│   │   └── bybit.py      # Bybit implementation
│   ├── notifications/    # Notification channels
│   │   ├── telegram.py             # Telegram notifier
│   │   └── telegram_bot_service.py # Telegram Bot service
│   ├── utils/            # Utilities
│   │   ├── cache_manager.py        # Cache management
│   │   ├── error_handler.py        # Error handling
│   │   ├── performance_monitor.py  # Performance monitoring
│   │   ├── chart.py                # Chart generation
│   │   └── config_validator.py     # Configuration validation
│   └── config/           # Configuration module
├── tests/                # Tests
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── tools/                # Tool scripts
│   ├── init_config.py    # Configuration initialization
│   └── update_markets.py # Market data update
└── config/               # Configuration files directory
    ├── config.yaml.example         # Configuration template
    └── supported_markets.json      # Market data
```

---

## Tech Stack

**Core Dependencies:**
- **CCXT**: Unified cryptocurrency exchange API library
- **Python-Telegram-Bot**: Telegram Bot API wrapper
- **WebSockets**: WebSocket connection management
- **Matplotlib + mplfinance**: Candlestick chart generation
- **PyYAML**: Configuration file parsing
- **ExpiringDict**: Expiring cache management

**Development Tools:**
- **Pytest**: Unit testing framework
- **Ruff**: Code formatting and linting
- **Bandit + Safety**: Security audit tools
- **uv**: Modern Python package manager

---

## Development Guide

### Environment Setup

```bash
# Clone repository
git clone https://github.com/Xeron2000/PriceSentry.git
cd PriceSentry

# Install dependencies (including dev dependencies)
uv sync --all-extras

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_core_sentry.py

# Run tests with coverage report
uv run pytest --cov=src --cov-report=html

# Run specific test
uv run pytest tests/test_core_sentry.py::TestPriceSentry::test_init_basic
```

### Code Quality Checks

```bash
# Run Ruff check
uv run ruff check src/

# Auto-fix fixable issues
uv run ruff check src/ --fix

# Code formatting
uv run ruff format src/

# Security audit
uv run bandit -r src/
uv run pip-audit
```

### Adding New Exchange Support

1. Create a new file in `src/exchanges/` directory (e.g., `new_exchange.py`)
2. Inherit from `BaseExchange` class and implement all abstract methods
3. Register the new exchange in `src/utils/get_exchange.py`
4. Update `tools/update_markets.py` to support fetching market data for the new exchange
5. Add corresponding test cases

Example:

```python
# src/exchanges/new_exchange.py
from .base import BaseExchange

class NewExchange(BaseExchange):
    def __init__(self):
        super().__init__("new_exchange")

    # Implement all abstract methods
    # ...
```

---

## FAQ

### Q1: Which exchanges does PriceSentry support?

A: Currently supports Binance, OKX, and Bybit. OKX or Bybit are recommended as they have no regional restrictions.

### Q2: How to add more trading pairs?

A: Edit the `config/config.yaml` file and add trading pairs to the `notificationSymbols` list:

```yaml
notificationSymbols:
  - "BTC/USDT:USDT"
  - "ETH/USDT:USDT"
  - "SOL/USDT:USDT"
  - "XRP/USDT:USDT"
```

### Q3: How to modify the price change threshold?

A: Edit the `defaultThreshold` value in the `config/config.yaml` file:

```yaml
defaultThreshold: 2  # Set to 2% price change threshold
```

### Q4: Can I monitor multiple exchanges simultaneously?

A: Currently doesn't support monitoring multiple exchanges simultaneously. To monitor multiple exchanges, you can run multiple PriceSentry instances, each with a different configuration file.

### Q5: Can chart functionality be disabled?

A: Yes. Set in `config/config.yaml`:

```yaml
attachChart: false
```

### Q6: How to get Telegram Bot Token?

A:
1. Search for [@BotFather](https://t.me/botfather) in Telegram
2. Send `/newbot` command to create a new bot
3. Follow prompts to set bot name and username
4. BotFather will return your Token

### Q7: How to get Telegram Chat ID?

A:
1. Search for [@userinfobot](https://t.me/userinfobot) in Telegram
2. Send any message
3. Bot will return your Chat ID

### Q8: Does the program consume many resources?

A: PriceSentry is very lightweight, with an average memory usage of about 50-100MB, and CPU usage is almost negligible.

---

## Contributing

Contributions are welcome! We follow this workflow:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'feat: add amazing feature'`
4. **Push branch**: `git push origin feature/amazing-feature`
5. **Submit Pull Request**

### Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation update
- `style:` Code format adjustment (no logic impact)
- `refactor:` Code refactoring
- `test:` Test-related
- `chore:` Build/tool-related

### Code Standards

- Follow PEP 8 specification
- Use Ruff for code checking and formatting
- Add tests for new features
- Update relevant documentation

---

## License

MIT License - See [LICENSE](LICENSE) for details

---

<div align="center">
  <p>If this project helps you, please give it a ⭐️!</p>
  <p>Questions? Feel free to submit an <a href="https://github.com/Xeron2000/PriceSentry/issues">Issue</a></p>
</div>
