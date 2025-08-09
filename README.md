<div align="center">
  <img src="./img/logo.svg" width="100" alt="Project Logo">
</div>

<div align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=34&pause=1000&center=true&vCenter=true&width=435&lines=PriceSentry" alt="Typing SVG">
</div>

<div align="center">
  <a href="README.md">English</a> | <a href="README_zh.md">中文</a>
</div>
<br>
<div align="center">
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-3.6%2B-blue?logo=python&logoColor=white" alt="Python 3.6+">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT">
  </a>
  <a href="https://github.com/Xeron2000/PriceSentry/stargazers">
    <img src="https://img.shields.io/github/stars/Xeron2000/PriceSentry?style=social" alt="Star on GitHub">
  </a>
</div>

<h3 align="center">A lightweight cryptocurrency contract price monitoring tool built for traders and enthusiasts🚨</h3>
<h4 align="center" style="color: #666;">Track. Analyze. Stay Informed.</h4>

---

## 🌟 Features

- 🔔 Multi-channel smart alerts (Telegram & DingDing)
- 🌐 Support for Binance, OKX, and Bybit exchanges
- 📆 Timezone-aware notifications
- 🔒 Secure configuration with YAML files

---

## 🛠 System Requirements

| Component       | Requirement              |
|-----------------|--------------------------|
| Python          | 3.6 or higher            |
| RAM             | 512MB+                   |
| Storage         | 100MB available space    |
| Network         | Stable internet connection |

---

## 🚀 Quick Installation

### 1. Clone Repository
```bash
git clone https://github.com/Xeron2000/PriceSentry.git
cd PriceSentry
```

### 2. Create Virtual Environment and Install Dependencies
```bash
# Install uv (if you haven't already)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create a virtual environment
uv venv

# Activate the virtual environment
# On Linux/macOS
source .venv/bin/activate
# On Windows
.venv\Scripts\activate

# Install dependencies
uv sync
```

---

## 🔧 Configuration Guide

### 🤖 Telegram Setup
1. **Create Bot** via [@BotFather](https://t.me/BotFather)
2. **Get Chat ID**:
   ```bash
   curl https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates | jq
   ```

### 📟 DingDing Setup
1. Create group robot with **Custom Security Settings**
2. Enable signature verification and save:
   - Webhook URL (`https://oapi.dingtalk.com/robot/...`)
   - Secret Key

---

## ⚙️ Configuration File

First, copy the example configuration file `config/config.yaml.example` to `config/config.yaml`. Then, modify `config/config.yaml` according to your needs.

Here is an example configuration:

```yaml
# Configuration for the exchange and default behavior
# The name of the exchange to connect to.
# Possible values: "binance", "okx", "bybit"
exchange: "bybit"  # Example: "binance"

# A list of exchanges to fetch market data from.
# This is used by the `tools/update_markets.py` script.
exchanges:
  - "binance"
  - "okx"
  - "bybit"

# The default timeframe (frequency of data retrieval).
# Possible values: "1m", "5m", "15m", "1h", "1d".
defaultTimeframe: "1d"  # Example: "5m"

# The default price change threshold. Only pairs exceeding this value will be notified.
defaultThreshold: 1  # Example: 1

# The file path containing trading pair symbols. If empty, pairs will be auto-retrieved.
symbolsFilePath: "config/symbols.txt"  # Example: "config/symbols.txt"

# Notification channels and configuration
# The channels for receiving notifications. Currently supports Telegram and DingDing.
notificationChannels:
  - "telegram"
  - "dingding"

# Telegram bot configuration
telegram:
  token: ""  # Example: "your_telegram_bot_token"
  chatId: ""  # Example: "your_chat_id"

# DingDing robot configuration
dingding:
  webhook: ""  # Example: "https://oapi.dingtalk.com/robot/send?access_token=your_access_token"
  secret: ""  # Example: "your_sign_secret"

# Timezone for notification messages.
# Default is Asia/Shanghai
notificationTimezone: "Asia/Shanghai" # Example: "America/New_York"

# Log level for the application.
# Possible values: "DEBUG", "INFO", "WARNING", "ERROR"
logLevel: "INFO" # Default: "INFO"
```

---

## 🔔 Alert Examples

<div style="text-align: center;">
  <img src="./img/tg.png" alt="Alert Examples">
</div>

---

## 🎨 Code Style

This project uses [Ruff](https://github.com/astral-sh/ruff) to format and lint the code. Before committing, please run the following commands to ensure your code adheres to the style guide:

```bash
# Format the code
ruff format .

# Lint the code and automatically fix issues
ruff check --fix .
```
---

## 🛠️ Tools

### Update Supported Markets

The `tools/update_markets.py` script is used to fetch the latest list of supported trading pairs from the exchanges defined in your `config/config.yaml`. This ensures that the application has an up-to-date list of available markets for symbol matching.

**Usage:**

To update the markets for all exchanges listed in your `config.yaml`:

```bash
python tools/update_markets.py
```

To update the markets for specific exchanges, you can pass their names as arguments:

```bash
python tools/update_markets.py --exchanges binance okx bybit
```

The script will create or update the `config/supported_markets.json` file with the fetched data.

---
## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <em>Made with ❤️ by Xeron</em><br>
  <a href="https://github.com/Xeron2000/PriceSentry/issues">Report Bug</a>
</p>

