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

## 功能一览

- 追踪 Binance、OKX、Bybit 合约价格并支持自定义交易对
- Telegram 推送价格波动与健康检查，内置机器人支持多用户绑定
- Dashboard 实时查看消息推送历史，可按收件人检查发送结果并预览图片
- YAML 配置驱动，内置校验与智能缓存机制
- 性能监控、熔断与指数退避重试保障稳定性

## 快速开始

```bash
git clone https://github.com/Xeron2000/PriceSentry.git
cd PriceSentry
uv sync && uv pip install -e .
uv run python -m app.runner
```

## 配置说明

1. 复制 `config/config.yaml.example` 为 `config/config.yaml`
2. 设置目标交易所、通知渠道与阈值
3. 在配置中填写 Telegram Bot Token，运行控制面板添加接收人

### Telegram 通知绑定流程

1. 在 Dashboard「通知渠道」页启用 Telegram，并保存包含 `telegram.token` 的配置。
2. 切换到新增加的「Telegram 接收人」标签，输入用户名生成绑定令牌。
3. 让目标用户与机器人对话并发送 `/bind <token>`，机器人会自动确认并加入通知列表。
4. 如需兼容旧流程，可在配置中保留 `telegram.chatId`，消息会优先发送至该 chat，再广播至所有绑定用户。

更多选项可参考示例文件注释，或运行 `uv run python tools/update_markets.py` 更新支持的市场列表。


## 常用命令

```bash
uv run python -m app.runner           # 启动监控
uv run pytest                          # 运行测试
uv run python tools/update_markets.py  # 刷新交易对数据
```



## 可用脚本

| 功能 | 命令 |
| --- | --- |
| 启动监控 | `uv run python -m app.runner` |
| 简化配置检查 | `uv run python -m app.config_check` |
| 交互配置生成 | `uv run python -m app.config_generator` |
| 监控仪表板 | `uv run python -m app.dashboard` |
| 生成监控报告 | `uv run python -m app.monitoring_report` |
| 更新交易对列表 | `uv run python tools/update_markets.py` |
| 启动快速测试 | `uv run python tests/quick_test.py` |
| 运行 API 端点手测 | `uv run python tools/manual_tests/api_endpoints.py` |

启动脚本 `./start.sh` 会自动调用上述命令组合完成环境检测与运行。

## Docker 部署

PriceSentry 提供基于 Docker Compose 的部署方式，后端服务默认启用，Dashboard 前端可按需加载。

### 构建与启动

```bash
# 构建镜像并启动后端
docker compose up -d backend

# 若需要同时启用 Dashboard
docker compose --profile dashboard up -d
```

默认情况下后端监听宿主机 `10080` 端口，Dashboard 监听 `13080` 端口，可通过环境变量调整映射（见下表）。

### 常用环境变量

| 变量 | 说明 | 默认值 |
| --- | --- | --- |
| `PRICESENTRY_EXCHANGE` | 指定默认交易所 | `okx` |
| `PRICESENTRY_TELEGRAM_TOKEN` | Telegram Bot Token | *(空)* |
| `PRICESENTRY_TELEGRAM_CHAT_ID` | Telegram 默认接收人 chatId | *(空)* |
| `PRICESENTRY_LOG_LEVEL` | 应用日志级别 | `INFO` |
| `PRICESENTRY_DASHBOARD_ACCESS_KEY` | Dashboard 访问密钥 | `pricesentry` |
| `PRICESENTRY_BACKEND_PORT` | 宿主机暴露的后端端口 | `10080` |
| `PRICESENTRY_DASHBOARD_PORT` | 宿主机暴露的 Dashboard 端口 | `13080` |
| `PRICESENTRY_PUBLIC_API_BASE_URL` | Dashboard 在构建期注入的后端访问地址（浏览器可访问） | `http://localhost:8000` |

建议基于仓库中的 `.env.example` 复制生成 `.env` 文件后再执行 `docker compose` 命令，以便在服务器环境中集中管理。

### 运行流程

1. `docker/backend/Dockerfile` 基于 `uv` 构建 Python 环境，并在启动时自动从示例配置生成 `config/config.yaml`；若提供上述环境变量会写入对应配置项。
2. `docker/dashboard/Dockerfile` 构建 Next.js Dashboard 的生产版本，通过 `pnpm start` 提供服务。
3. `docker-compose.yml` 默认只启动 `backend` 服务，执行 `docker compose --profile dashboard up` 时会同时拉起 `dashboard` 并依赖后端。

部署完成后，可在服务器上访问 `http://服务器IP:10080` 使用后端 API；若启用了 Dashboard，则访问 `http://服务器IP:13080` 并使用 `PRICESENTRY_DASHBOARD_ACCESS_KEY` 登录。
## 项目结构

```
PriceSentry/
├── core/           核心流程与调度
├── exchanges/      交易所接入实现
├── notifications/  推送渠道适配
├── utils/          缓存、告警、校验等工具
└── tests/          单元与集成测试
```

## 许可

项目以 MIT 许可证开源，详见 `LICENSE`。
