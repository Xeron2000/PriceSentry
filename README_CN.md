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

<h3 align="center">轻量级加密货币期货价格监控工具 🚨</h3>
<h4 align="center" style="color: #666;">追踪 · 分析 · 保持敏锐</h4>

<p align="center">
  <a href="README.md">English</a> |
  <a href="README_CN.md">简体中文</a>
</p>

---

## 📖 目录

- [项目起源](#项目起源)
- [核心特性](#核心特性)
- [快速开始](#快速开始)
  - [一键安装（推荐）](#一键安装推荐)
  - [手动安装](#手动安装)
- [配置指南](#配置指南)
  - [推荐：手动配置](#推荐手动配置)
  - [获取市场数据](#获取市场数据)
  - [交互式配置](#交互式配置)
  - [重要注意事项](#重要注意事项)
  - [高级配置](#高级配置)
- [常用命令](#常用命令)
- [故障排除](#故障排除)
- [截图展示](#截图展示)
- [项目结构](#项目结构)
- [技术栈](#技术栈)
- [开发指南](#开发指南)
- [常见问题](#常见问题)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

---

## 项目起源

作为一名专注短线交易的期货交易者,我大部分时间都在盯着缺乏波动的市场,这极大地消耗了我的精力。但当真正的市场行情来临时,我希望能第一时间捕捉到这些机会。市面上的工具要么订阅费用高昂,要么缺少实际交易场景所需的功能,因此我决定构建一个自动化的监控解决方案。

PriceSentry 应运而生——专为面临类似挑战的短线期货交易者设计,完全开源且免费,让你的精力专注于决策,将重复性的监控工作交给程序。

---

## 核心特性

- ✅ 支持 Binance、OKX 和 Bybit 期货价格监控,可自定义交易对
- ✅ Telegram 消息推送价格变动和健康检查,支持多用户绑定
- ✅ YAML 驱动的配置管理,内置验证和缓存机制
- ✅ 性能监控、熔断保护和指数退避重试机制,确保稳定性
- ✅ 可选的 K 线图表附件,直观展示价格走势
- ✅ 灵活的通知过滤器,只推送你关心的交易对

> 想先试用一下？订阅 [PriceSentry 期货监控](https://t.me/pricesentry) 频道获取即时推送通知。

---

## 快速开始

### 一键安装（推荐）

使用 `uvx` 一键安装并运行:

```bash
uvx --from git+https://github.com/Xeron2000/PriceSentry.git pricesentry
```

**首次运行步骤：**
1. 交互式配置或手动编辑 `config/config.yaml`
2. 设置 Telegram Bot Token（从 [@BotFather](https://t.me/botfather) 获取）
3. 设置 Telegram Chat ID（通过 [@userinfobot](https://t.me/userinfobot) 获取）
4. **推荐使用 OKX 或 Bybit 交易所**（Binance 在某些地区有限制）
5. 程序会自动更新市场数据并启动监控

**文件保存位置：**
```
当前目录/
├── config/
│   ├── config.yaml              # 配置文件
│   └── supported_markets.json   # 市场数据（自动获取）
```

### 手动安装

```bash
# 克隆仓库
git clone https://github.com/Xeron2000/PriceSentry.git
cd PriceSentry

# 安装依赖
uv sync

# 1. 创建配置文件
uv run python tools/init_config.py

# 2. 编辑配置
vi config/config.yaml

# 3. 运行市场数据更新（使用脚本获取真实数据）
uv run python tools/update_markets.py

# 4. 启动监控
uv run python -m app.cli
```

---

## 配置指南

### 推荐：手动配置

编辑 `config/config.yaml`（推荐方式）：

```yaml
# 使用 OKX 或 Bybit 避免地区限制
exchange: "okx"  # okx, bybit, binance

# 默认时间周期（K 线聚合窗口）
defaultTimeframe: "5m"  # 1m, 5m, 15m, 1h, 1d

# 监控任务检查频率
checkInterval: "1m"

# 价格变化阈值（百分比）
defaultThreshold: 1

# 通知渠道
notificationChannels:
  - "telegram"

# 通知交易对（留空表示推送所有监控到的合约交易对）
notificationSymbols:
  - "BTC/USDT:USDT"
  - "ETH/USDT:USDT"
  - "SOL/USDT:USDT"

# Telegram 机器人配置
telegram:
  # 从 @BotFather 获取，格式: 数字:字符
  token: "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
  # 从 @userinfobot 获取，纯数字
  chatId: "123456789"

# 通知时区
notificationTimezone: "Asia/Shanghai"

# 是否在通知中附带价格图表
attachChart: true

# 图表渲染设置（attachChart 为 true 时生效）
chartTimeframe: "5m"
chartLookbackMinutes: 500
chartTheme: "dark"          # "dark" | "light"
chartImageWidth: 1600
chartImageHeight: 1200
chartImageScale: 2
```

### 获取市场数据

使用 `tools/update_markets.py` 脚本获取真实的交易对数据：

```bash
# 更新单个交易所的市场数据
uv run python tools/update_markets.py --exchanges okx

# 更新多个交易所的市场数据
uv run python tools/update_markets.py --exchanges okx bybit

# 更新所有支持交易所的市场数据
uv run python tools/update_markets.py
```

**注意：**
- 脚本会从交易所 API 获取最新的交易对列表
- 数据会保存到 `config/supported_markets.json`
- OKX/Bybit 没有地区限制,可以正常获取
- Binance 在某些地区可能需要代理

### 交互式配置

首次运行 `pricesentry` 命令时,如果配置文件不存在,会自动进入配置向导,然后自动获取市场数据。

**注意：** 由于交互式配置在非交互式环境（如 shell 脚本）可能有问题，**推荐手动编辑配置文件**。

### 重要注意事项

1. **Binance 地区限制：**
   - Binance API 在某些地区（如中国）可能被限制
   - **推荐使用 OKX 或 Bybit**

2. **Telegram Token 格式：**
   - 必须是 `数字:字符` 格式
   - 示例：`123456789:ABCdefGHIjklMNOpqrsTUVwxyz`
   - ❌ 错误：`my_token_123`
   - ✅ 正确：`123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

3. **Chat ID 格式：**
   - 必须是纯数字
   - 通过 [@userinfobot](https://t.me/userinfobot) 获取

4. **交易对格式：**
   - OKX/Bybit 使用 `BTC/USDT:USDT` 格式
   - Binance 使用 `BTC/USDT:USDT` 格式
   - 确保格式与交易所匹配

### 高级配置

使用配置初始化工具进行高级配置:

```bash
uv run python tools/init_config.py
```

支持的参数:
- `--force`: 覆盖现有配置
- `--non-interactive`: 直接复制模板

---

## 常用命令

| 功能 | 命令 |
| --- | --- |
| 启动监控 | `uv run python -m app.cli` 或 `pricesentry` |
| 编辑配置 | `vi config/config.yaml` |
| 重新配置 | `rm config/config.yaml && pricesentry` |
| 更新市场数据 | `uv run python tools/update_markets.py` |
| 更新指定交易所 | `uv run python tools/update_markets.py --exchanges okx` |
| 运行测试 | `uv run pytest` |
| 运行代码检查 | `uv run ruff check src/` |
| 代码格式化 | `uv run ruff format src/` |

---

## 故障排除

### 1. 启动报错：`No valid notification symbols`

**原因：** 配置的交易对格式不正确或市场数据未更新

**解决方案：**
```bash
# 1. 检查配置文件中的交易对格式
vi config/config.yaml

# 2. 确保格式为 "BTC/USDT:USDT"（注意冒号）

# 3. 更新市场数据
uv run python tools/update_markets.py --exchanges okx

# 4. 重新启动
uv run python -m app.cli
```

### 2. 启动报错：`'PriceSentry' object has no attribute 'matched_symbols'`

**原因：** 这是旧版本的 bug，已在最新版本中修复

**解决方案：**
```bash
# 拉取最新代码
git pull origin main

# 重新安装
uv sync

# 重新启动
uv run python -m app.cli
```

### 3. Binance API 连接超时

**原因：** Binance API 在某些地区被限制

**解决方案：**
```yaml
# 修改 config/config.yaml
exchange: "okx"  # 或 "bybit"
```

### 4. Telegram 消息未收到

**检查清单：**
- ✅ Token 格式是否正确（`数字:字符`）
- ✅ Chat ID 是否正确（纯数字）
- ✅ 是否向机器人发送过 `/start` 命令
- ✅ 网络是否正常（某些地区需要代理）

---

## 截图展示

<div align="center">
  <img src="https://raw.githubusercontent.com/Xeron2000/PriceSentry/refs/heads/main/img/tg.jpg" alt="Telegram Notification Example" width="520">
</div>

---

## 项目结构

```
PriceSentry/
├── src/
│   ├── app/              # 应用入口（CLI）
│   │   ├── cli.py        # 命令行接口
│   │   └── runner.py     # 运行器
│   ├── core/             # 核心逻辑
│   │   ├── config_manager.py  # 配置管理
│   │   ├── notifier.py        # 通知分发器
│   │   └── sentry.py          # 监控引擎
│   ├── exchanges/        # 交易所适配器
│   │   ├── base.py       # 基类
│   │   ├── binance.py    # Binance 实现
│   │   ├── okx.py        # OKX 实现
│   │   └── bybit.py      # Bybit 实现
│   ├── notifications/    # 通知渠道
│   │   ├── telegram.py             # Telegram 通知器
│   │   └── telegram_bot_service.py # Telegram Bot 服务
│   ├── utils/            # 工具库
│   │   ├── cache_manager.py        # 缓存管理
│   │   ├── error_handler.py        # 错误处理
│   │   ├── performance_monitor.py  # 性能监控
│   │   ├── chart.py                # 图表生成
│   │   └── config_validator.py     # 配置验证
│   └── config/           # 配置模块
├── tests/                # 测试
│   ├── unit/             # 单元测试
│   └── integration/      # 集成测试
├── tools/                # 工具脚本
│   ├── init_config.py    # 配置初始化
│   └── update_markets.py # 市场数据更新
└── config/               # 配置文件目录
    ├── config.yaml.example         # 配置模板
    └── supported_markets.json      # 市场数据
```

---

## 技术栈

**核心依赖：**
- **CCXT**: 加密货币交易所统一 API 库
- **Python-Telegram-Bot**: Telegram Bot API 封装
- **WebSockets**: WebSocket 连接管理
- **Matplotlib + mplfinance**: K 线图表生成
- **PyYAML**: 配置文件解析
- **ExpiringDict**: 过期缓存管理

**开发工具：**
- **Pytest**: 单元测试框架
- **Ruff**: 代码格式化和 Linting
- **Bandit + Safety**: 安全审计工具
- **uv**: 现代 Python 包管理器

---

## 开发指南

### 环境设置

```bash
# 克隆仓库
git clone https://github.com/Xeron2000/PriceSentry.git
cd PriceSentry

# 安装依赖（包括开发依赖）
uv sync --all-extras

# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate     # Windows
```

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行单个测试文件
uv run pytest tests/test_core_sentry.py

# 运行带覆盖率报告的测试
uv run pytest --cov=src --cov-report=html

# 运行特定测试
uv run pytest tests/test_core_sentry.py::TestPriceSentry::test_init_basic
```

### 代码质量检查

```bash
# 运行 Ruff 检查
uv run ruff check src/

# 自动修复可修复的问题
uv run ruff check src/ --fix

# 代码格式化
uv run ruff format src/

# 安全审计
uv run bandit -r src/
uv run pip-audit
```

### 添加新的交易所支持

1. 在 `src/exchanges/` 目录下创建新文件（如 `new_exchange.py`）
2. 继承 `BaseExchange` 类并实现所有抽象方法
3. 在 `src/utils/get_exchange.py` 中注册新交易所
4. 更新 `tools/update_markets.py` 以支持获取新交易所的市场数据
5. 添加相应的测试用例

示例:

```python
# src/exchanges/new_exchange.py
from .base import BaseExchange

class NewExchange(BaseExchange):
    def __init__(self):
        super().__init__("new_exchange")

    # 实现所有抽象方法
    # ...
```

---

## 常见问题

### Q1: PriceSentry 支持哪些交易所？

A: 目前支持 Binance、OKX 和 Bybit。推荐使用 OKX 或 Bybit，因为它们没有地区限制。

### Q2: 如何添加更多交易对？

A: 编辑 `config/config.yaml` 文件，在 `notificationSymbols` 列表中添加交易对:

```yaml
notificationSymbols:
  - "BTC/USDT:USDT"
  - "ETH/USDT:USDT"
  - "SOL/USDT:USDT"
  - "XRP/USDT:USDT"
```

### Q3: 如何修改价格变动阈值？

A: 编辑 `config/config.yaml` 文件中的 `defaultThreshold` 值:

```yaml
defaultThreshold: 2  # 设置为 2% 的价格变动阈值
```

### Q4: 可以同时监控多个交易所吗？

A: 目前不支持同时监控多个交易所。如需监控多个交易所，可以运行多个 PriceSentry 实例，每个实例使用不同的配置文件。

### Q5: 图表功能可以关闭吗？

A: 可以。在 `config/config.yaml` 中设置:

```yaml
attachChart: false
```

### Q6: 如何获取 Telegram Bot Token？

A:
1. 在 Telegram 中搜索 [@BotFather](https://t.me/botfather)
2. 发送 `/newbot` 命令创建新机器人
3. 按照提示设置机器人名称和用户名
4. BotFather 会返回你的 Token

### Q7: 如何获取 Telegram Chat ID？

A:
1. 在 Telegram 中搜索 [@userinfobot](https://t.me/userinfobot)
2. 发送任意消息
3. 机器人会返回你的 Chat ID

### Q8: 程序占用资源多吗？

A: PriceSentry 非常轻量级，平均内存占用约 50-100MB，CPU 占用几乎可以忽略不计。

---

## 贡献指南

欢迎贡献！我们遵循以下流程：

1. **Fork 仓库**
2. **创建特性分支**: `git checkout -b feature/amazing-feature`
3. **提交变更**: `git commit -m 'feat: add amazing feature'`
4. **推送分支**: `git push origin feature/amazing-feature`
5. **提交 Pull Request**

### 提交消息规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

- `feat:` 新功能
- `fix:` 错误修复
- `docs:` 文档更新
- `style:` 代码格式调整（不影响代码逻辑）
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建/工具相关

### 代码规范

- 遵循 PEP 8 规范
- 使用 Ruff 进行代码检查和格式化
- 为新功能添加测试
- 更新相关文档

---

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

<div align="center">
  <p>如果这个项目对你有帮助，请给它一个 ⭐️！</p>
  <p>有问题？欢迎提交 <a href="https://github.com/Xeron2000/PriceSentry/issues">Issue</a></p>
</div>
