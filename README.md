<div align="center">
  <img src="./img/logo.svg" width="100" alt="Project Logo">
</div>

<div align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=34&pause=1000&center=true&vCenter=true&width=435&lines=PriceSentry" alt="Typing SVG">
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

<h3 align="center">为交易者和爱好者打造的轻量级加密货币合约价格监控工具🚨</h3>
<h4 align="center" style="color: #666;">追踪·分析·保持敏锐</h4>

---

## 🌟 核心功能

- 🔔 多渠道智能提醒（Telegram & 钉钉）
- 🌐 支持 Binance、OKX 和 Bybit 交易所
- 📆 时区感知通知
- 🔒 使用 YAML 文件安全配置

---

## 🛠 系统要求

| 组件           | 要求                  |
|----------------|----------------------|
| Python         | 3.6 或更高版本       |
| 内存           | 512MB 以上           |
| 存储空间       | 100MB 可用空间       |
| 网络           | 稳定互联网连接       |

---

## 🚀 快速安装

### 1. 克隆仓库
```bash
git clone https://github.com/Xeron2000/PriceSentry.git
cd PriceSentry
```

### 2. 创建虚拟环境并安装依赖
```bash
# 安装 uv (如果尚未安装)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境
uv venv

# 激活虚拟环境
# 在 Linux/macOS 上
source .venv/bin/activate
# 在 Windows 上
.venv\Scripts\activate

# 安装依赖
uv sync
```

---

## 🔧 配置指南

### 🤖 Telegram 设置
1. 通过 [@BotFather](https://t.me/BotFather) **创建机器人**
2. **获取 Chat ID**：
   ```bash
   curl https://api.telegram.org/bot<你的TOKEN>/getUpdates | jq
   ```

### 📟 钉钉设置
1. 创建群机器人并选择**自定义安全设置**
2. 启用签名验证并保存：
   - Webhook地址（`https://oapi.dingtalk.com/robot/...`）
   - 加签密钥

---

## ⚙️ 配置文件

将示例配置文件 `config/config.yaml.example` 复制一份并重命名为 `config/config.yaml`，然后根据您的需求进行修改。下面是一个配置示例：

```yaml
# 交易所和默认行为配置
# 要连接的交易所名称
# 可选值："binance", "okx", "bybit"
exchange: "okx"  # 示例："binance"

# 要获取市场数据的交易所列表。
# `tools/update_markets.py` 脚本会使用此列表。
exchanges:
  - "binance"
  - "okx"
  - "bybit"

# 默认时间周期（数据获取频率）
# 可选值："1m", "5m", "15m", "1h", "1d"
defaultTimeframe: "5m"  # 示例："5m"

# 默认价格变化阈值，仅超过该值的交易对会触发通知
defaultThreshold: 0.01  # 示例：1

# 交易对文件路径，留空则自动获取
symbolsFilePath: "config/symbols.txt"  # 示例："config/symbols.txt"

# 通知渠道配置
# 当前支持 Telegram 和钉钉
notificationChannels: 
  - "telegram"
  # - "dingding"

# Telegram 机器人配置
telegram:
  token: "YOUR_TELEGRAM_BOT_TOKEN"  # 示例："你的机器人令牌"
  chatId: "YOUR_CHAT_ID"  # 示例："你的聊天ID"

# 钉钉机器人配置
dingding:
  webhook: ""  # 示例："https://oapi.dingtalk.com/robot/send?access_token=你的访问令牌"
  secret: ""  # 示例："你的签名密钥"

# 通知时区配置
# 默认亚洲/上海时间
notificationTimezone: "Asia/Shanghai" # 示例："America/New_York"

# 应用程序的日志级别
# 可选值: "DEBUG", "INFO", "WARNING", "ERROR"
logLevel: "INFO" # 默认: "INFO"

# 图表附件配置（可选）
# 启用后，Telegram 提醒将包含最近的价格图表图片
attachChart: true

# 图表渲染设置
chartTimeframe: "1m"           # K线图时间周期
chartLookbackMinutes: 60        # 包含的历史数据分钟数
chartTheme: "dark"              # "dark" | "light"
chartIncludeMA: [7, 25]         # 移动平均线窗口；空列表则禁用
chartImageWidth: 1600           # 复合图表图片宽度（像素）
chartImageHeight: 1200          # 图片高度（像素）
chartImageScale: 2              # 像素比例倍数（2 = Retina 级别）
```

## 🔔 通知示例

<div style="text-align: center;">
  <img src="./img/tg.png" alt="Alert Examples">
</div>

---

## 🎨 代码风格

本项目使用 [Ruff](https://github.com/astral-sh/ruff) 进行代码格式化和质量检查。在提交代码前，请运行以下命令以确保您的代码符合风格指南：

```bash
# 格式化代码
ruff format .

# 检查代码并自动修复问题
ruff check --fix .
```

---

## 🛠️ 工具

### 更新支持的市场

`tools/update_markets.py` 脚本用于从 `config/config.yaml` 中定义的交易所获取最新的支持交易对列表。这可以确保应用程序拥有最新的可用市场列表以进行交易对匹配。

**用法:**

要更新 `config.yaml` 中列出的所有交易所的市场：

```bash
python tools/update_markets.py
```

要更新特定交易所的市场，您可以将其名称作为参数传递：

```bash
python tools/update_markets.py --exchanges binance okx bybit
```

该脚本将使用获取的数据创建或更新 `config/supported_markets.json` 文件。

---
## 📜 开源协议

本项目采用 MIT 开源协议，详见 [LICENSE](LICENSE)。

---

<p align="center">
  <em>由 Xeron 用心制作 ❤️</em><br>
  <a href="https://github.com/Xeron2000/PriceSentry/issues">报告问题</a>
</p>
