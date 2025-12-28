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

<h3 align="center">Lightweight Cryptocurrency Futures Price Monitoring Tool for Traders and Enthusiasts🚨</h3>
<h4 align="center" style="color: #666;">Track · Analyze · Stay Sharp</h4>

<p align="center">
  <a href="README.md">English</a> | 
  <a href="README_CN.md">简体中文</a>
</p>

---

## Origin Story

As a futures trader focusing on short-term opportunities, I spend most of my time in a market that lacks volatility, and constantly watching the charts drains my energy. Yet when there's real market movement, I want to capture the momentum immediately. Available tools either have high subscription costs or lack practical features for real trading scenarios, so I decided to build an automated monitoring solution. PriceSentry was born—designed for short-term futures traders facing similar challenges, completely open-source and free, leaving your energy for decision-making and delegating repetitive monitoring to the program.

## Features

- Support for Binance, OKX, and Bybit futures price monitoring with customizable trading pairs
- Telegram notifications for price movements and health checks, with multi-user binding support
- YAML-driven configuration with built-in validation and caching mechanisms
- Performance monitoring, circuit breaking, and exponential backoff retry for stability

> Want to try it first? Subscribe to [PriceSentry Futures Monitor](https://t.me/pricesentry) channel for instant push notifications.

## Quick Start

### One-Command Setup (Recommended)

```bash
uvx --from git+https://github.com/Xeron2000/PriceSentry.git pricesentry
```

This command will automatically:
1. Create `config/config.yaml` from template
2. Update supported markets for your exchange
3. Start the monitoring service

Edit `config/config.yaml` to configure:
- `telegram.token`: Your Telegram bot token
- `telegram.chatId`: Your Telegram chat ID
- `exchange`: Exchange name (binance/okx/bybit)
- `notificationSymbols`: Trading pairs to monitor

### Manual Installation

```bash
git clone https://github.com/Xeron2000/PriceSentry.git
cd PriceSentry
uv sync
uv run python -m app.cli
```

## Configuration

### Quick Configuration

After the first run, edit `config/config.yaml`:

```yaml
exchange: "okx"
notificationSymbols:
  - "BTC/USDT:USDT"
  - "ETH/USDT:USDT"
telegram:
  token: "YOUR_TELEGRAM_BOT_TOKEN"
  chatId: "YOUR_CHAT_ID"
```

### Advanced Configuration

For advanced configuration options:
```bash
uv run python tools/init_config.py
```

Supported parameters:
- `--force`: Overwrite existing configuration
- `--non-interactive`: Copy template directly

## Common Commands

| Function | Command |
| --- | --- |
| Start monitoring | `uv run python -m app.cli` or `pricesentry` |
| Initialize config | `uv run python tools/init_config.py` |
| Update markets | `uv run python tools/update_markets.py` |
| Run tests | `uv run pytest` |

## Screenshots

<div align="center">
  <img src="https://raw.githubusercontent.com/Xeron2000/PriceSentry/refs/heads/main/img/tg.jpg" alt="Telegram Notification Example" width="520">
</div>

## Project Structure

```
PriceSentry/
├── src/
│   ├── core/          Core processes and scheduling
│   ├── exchanges/     Exchange integration implementations
│   ├── notifications/ Notification channel adapters
│   └── utils/         Utilities for caching, alerts, validation, etc.
├── tests/             Unit and integration tests
└── config/            Configuration file directory
```

## License

MIT License - See [LICENSE](LICENSE) for details
