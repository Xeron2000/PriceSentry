<div align="center">
  <img src="./img/logo.svg" width="100" alt="Project Logo">
</div>

<div align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=34&pause=1000&center=true&vCenter=true&width=435&lines=PriceSentry" alt="Typing SVG">
</div>

<br>
<div align="center">
  <a href="https://nextjs.org/">
    <img src="https://img.shields.io/badge/Next.js-13+-000000?logo=next.js&logoColor=white" alt="Next.js 13+">
  </a>
  <a href="https://fastapi.tiangolo.com/">
    <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white" alt="FastAPI 0.100+">
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

<p align="center">
  <a href="README.md">English</a> | 
  <a href="README_CN.md">简体中文</a>
</p>

---

## 项目起因

我是一名专注短线机会的合约交易员。多数时间市场缺乏波动、一直盯盘耗费精力；真正有行情时却又想第一时间捕捉节奏。市面上可选的工具要么付费门槛高，要么功能单薄、不贴合实战需求，于是便决定自研一套自动化监控方案。PriceSentry 因此诞生——面向有同样困境的短线合约交易者，完全开源、免费，把精力留给决策本身，把重复监控交给程序。

## 功能特性

- 支持 Binance、OKX、Bybit 合约价格监控，可自定义交易对
- Telegram 推送价格波动与健康检查，支持多用户绑定
- Web Dashboard 实时查看推送历史与图表
- YAML 配置驱动，内置校验与缓存机制
- 性能监控、熔断与指数退避重试保障稳定性

> 想先体验？订阅 [PriceSentry合约监控](https://t.me/pricesentry) 频道获取即时推送。

## 快速开始

### Docker 部署（推荐）

```bash
git clone https://github.com/Xeron2000/PriceSentry.git
cd PriceSentry
cp .env.example .env  # 编辑环境变量（见下方说明）

docker compose pull
docker compose run --rm backend python tools/init_config.py
docker compose up -d
```

启动后访问：
- 后端 API：`http://localhost:18000`
- Dashboard：`http://localhost:13000`

### 手动部署

```bash
git clone https://github.com/Xeron2000/PriceSentry.git
cd PriceSentry
uv sync && uv pip install -e .
uv run python tools/init_config.py
uv run python -m app.runner

# （可选）启动 Dashboard
cd dashboard
pnpm install && pnpm build && pnpm start
```

## 配置说明

### 初始化配置

```bash
uv run python tools/init_config.py
# 或 docker compose exec backend python tools/init_config.py
```

按提示设置交易所、通知渠道与阈值。支持参数：
- `--force`：覆盖现有配置
- `--non-interactive`：直接复制模板

### Telegram 绑定流程

1. 在 Dashboard「通知渠道」启用 Telegram，保存 `telegram.token`
2. 在「Telegram 接收人」标签输入用户名生成绑定令牌
3. 用户与机器人对话发送 `/bind <token>` 完成绑定

### 环境变量配置

复制 `.env.example` 为 `.env` 后调整：

**Docker 部署示例：**
```env
NEXT_PUBLIC_API_BASE=
BACKEND_INTERNAL_URL=http://backend:8000
PRICESENTRY_ALLOWED_ORIGINS=http://frontend:3000
```

**手动部署示例：**
```env
NEXT_PUBLIC_API_BASE=https://api.example.com
BACKEND_INTERNAL_URL=http://127.0.0.1:8000
PRICESENTRY_ALLOWED_ORIGINS=https://app.example.com
```

**变量说明：**
- `NEXT_PUBLIC_API_BASE`：前端访问后端的公网地址（留空时使用 Next.js 代理）
- `BACKEND_INTERNAL_URL`：Dashboard 内部访问后端的地址
- `PRICESENTRY_ALLOWED_ORIGINS`：允许跨域的前端地址（逗号分隔）

## 常用命令

| 功能 | 命令 |
| --- | --- |
| 初始化配置 | `uv run python tools/init_config.py` |
| 启动监控 | `uv run python -m app.runner` |
| 更新交易对 | `uv run python tools/update_markets.py` |
| 运行测试 | `uv run pytest` |

## 运行截图

<table align="center">
  <tr>
    <td align="center" valign="middle">
      <img src="https://raw.githubusercontent.com/Xeron2000/PriceSentry/refs/heads/main/img/web.jpg" alt="Dashboard 运行截图" width="520">
    </td>
    <td align="center" valign="middle">
      <img src="https://raw.githubusercontent.com/Xeron2000/PriceSentry/refs/heads/main/img/tg.jpg" alt="Telegram 推送示例" width="520">
    </td>
  </tr>
</table>

## 项目结构

```
PriceSentry/
├── src/
│   ├── core/          核心流程与调度
│   ├── exchanges/     交易所接入实现
│   ├── notifications/ 推送渠道适配
│   └── utils/         缓存、告警、校验等工具
├── dashboard/         Next.js 前端
├── tests/             单元与集成测试
└── config/            配置文件目录
```

## 文档

- [配置指南（中文）](docs/CONFIG_CN.md)
- [Configuration Guide (English)](docs/CONFIG.md)

## 许可协议

MIT License - 详见 [LICENSE](LICENSE)
