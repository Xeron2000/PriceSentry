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

**首次运行步骤：**
1. 交互式配置或手动编辑 `config/config.yaml`
2. 设置 Telegram Bot Token（从 [@BotFather](https://t.me/botfather) 获取）
3. 设置 Telegram Chat ID（通过 [@userinfobot](https://t.me/userinfobot) 获取）
4. 推荐使用 **OKX** 或 **Bybit** 交易所（Binance 有地区限制）
5. 运行命令后自动更新市场数据并启动监控

**文件保存位置：**
```
当前目录/
├── config/
│   ├── config.yaml              # 配置文件
│   └── supported_markets.json   # 市场数据
```

### Manual Installation

```bash
git clone https://github.com/Xeron2000/PriceSentry.git
cd PriceSentry
uv sync
# 1. 创建配置文件
uv run python tools/init_config.py
# 2. 编辑配置
vi config/config.yaml
# 3. 运行
uv run python -m app.cli
```

## Configuration

### Recommended: Manual Configuration

编辑 `config/config.yaml`（推荐）：

```yaml
# 使用 OKX 或 Bybit 避免地区限制
exchange: "okx"  # okx, bybit, binance

notificationSymbols:
  - "BTC/USDT:USDT"
  - "ETH/USDT:USDT"

telegram:
  # 从 @BotFather 获取，格式: 数字:字符
  token: "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
  # 从 @userinfobot 获取，纯数字
  chatId: "123456789"
```

### Interactive Setup

首次运行 `pricesentry` 命令时，如果配置文件不存在，会自动进入配置向导。

**注意：** 由于交互式配置在非交互式环境可能有问题，**推荐手动编辑配置文件**。

### Important Notes

1. **Binance 地区限制：**
   - Binance API 在某些地区可能被限制
   - **推荐使用 OKX 或 Bybit**

2. **Telegram Token 格式：**
   - 必须是 `数字:字符` 格式
   - 示例：`123456789:ABCdefGHIjklMNOpqrsTUVwxyz`
   - ❌ 错误：`my_token_123`
   - ✅ 正确：`123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

3. **Chat ID 格式：**
   - 必须是纯数字
   - 通过 [@userinfobot](https://t.me/userinfobot) 获取

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
| Edit config | `vi config/config.yaml` |
| Re-configure | `rm config/config.yaml && pricesentry` |
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
