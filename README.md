<p align="center">
  <span style="font-size: 5rem; background-color: #ffffff; padding: 20px; border-radius: 15px; color: #007bff; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">📈</span>
</p>

<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=34&pause=1000&center=true&vCenter=true&width=435&lines=PriceSentry" alt="Typing SVG">
</p>

<p align="center">
  <a href="README.md" style="font-size: 1.2rem;; margin-right: 20px;">English</a>
  <a href="README_zh.md" style="font-size: 1.2rem; ;">中文</a>
</p>

<p align="center">
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-3.6%2B-blue?logo=python&logoColor=white" alt="Python 3.6+">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT">
  </a>
  <a href="https://github.com/Xeron2000/PriceSentry/stargazers">
    <img src="https://img.shields.io/github/stars/Xeron2000/PriceSentry?style=social" alt="Star on GitHub">
  </a>
</p>
</div><h3 align="center">A lightweight cryptocurrency contract price monitoring tool built for traders and enthusiasts🚨</h3> <h4 align="center" style="color: #666;">Track. Analyze. Stay Informed.</h4>

---

## 🌟 Features

- 🔔 Multi-channel smart alerts (Telegram & DingDing)
- 🌐 Support for Binance and OKX exchanges
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

### 1. Install Dependencies
```bash
sudo apt update && sudo apt install -y python3 python3-pip
```

### 2. Clone Repository
```bash
git clone https://github.com/Xeron2000/PriceSentry.git
cd PriceSentry
```

### 3. Install Packages
```bash
pip install -r requirements.txt
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

## ⚙️ Configuration File (`config/config.yaml`)

```yaml
# Configuration for the exchange and default behavior
# The name of the exchange to connect to.
# Possible values: "binance", "okx"
exchange: "okx"  # Example: "binance"

# The default timeframe (frequency of data retrieval).
# Possible values: "1m", "5m", "15m", "1h", "1d".
defaultTimeframe: "1d"  # Example: "5m", 

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
# The token used to connect to the Telegram bot.
telegram:
  token: ""  # Example: "your_telegram_bot_token"
  
  # The Telegram chat ID where notifications will be sent.
  chatId: ""  # Example: "your_chat_id"

# DingDing robot configuration
# The DingDing robot webhook URL for sending notifications.
dingding:
  webhook: ""  # Example: "https://oapi.dingtalk.com/robot/send?access_token=your_access_token"
  
  # The DingDing robot secret used to generate the signature for secure notifications.
  secret: ""  # Example: "your_sign_secret"

# Timezone for notification messages.
# Default is Asia/Shanghai
notificationTimezone: "Asia/Shanghai" # Example: "America/New_York"

```

---

## 🔔 Alert Examples

<div style="text-align: center;">
  <img src="./img/tg.png" alt="Alert Examples">
</div>

---

## 🕒 Cron Job Setup

```bash
# Edit cron jobs
crontab -e

# Add line (runs every 5 minutes)
*/5 * * * * /usr/bin/python3 /path/to/PriceSentry/main.py >> /path/to/logs.txt 2>&1
```

---

## 📜 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

---

<p align="center">
  <em>Made with ❤️ by Xeron</em><br>
  <a href="https://github.com/Xeron2000/PriceSentry/issues">Report Bug</a>
</p>

