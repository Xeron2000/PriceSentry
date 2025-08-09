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

<h3 align="center">为交易者和爱好者打造的轻量级加密货币合约价格监控工具🚨</h3>
<h4 align="center" style="color: #666;">追踪·分析·保持敏锐</h4>

---

## 🌟 核心功能

- 🔔 多渠道智能提醒（Telegram & 钉钉）
- 🌐 支持 Binance 和 OKX 交易所
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

默认配置文件位于`config/config.yaml`

---

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
python tools/update_markets.py --exchanges binance okx
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
