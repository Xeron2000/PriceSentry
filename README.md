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
- Web Dashboard for real-time viewing of notification history and charts
- YAML-driven configuration with built-in validation and caching mechanisms
- Performance monitoring, circuit breaking, and exponential backoff retry for stability

> Want to try it first? Subscribe to [PriceSentry Futures Monitor](https://t.me/pricesentry) channel for instant push notifications.

## Quick Start

### Docker Deployment (Recommended)

```bash
git clone https://github.com/Xeron2000/PriceSentry.git
cd PriceSentry
cp .env.example .env  # Edit environment variables (see instructions below)

docker compose pull
docker compose run --rm backend python tools/init_config.py
docker compose up -d
```

After startup, visit:
- Backend API: `http://localhost:18000`
- Dashboard: `http://localhost:13000`

### Manual Deployment

```bash
git clone https://github.com/Xeron2000/PriceSentry.git
cd PriceSentry
uv sync && uv pip install -e .
uv run python tools/init_config.py
uv run python -m app.runner

# (Optional) Start Dashboard
cd dashboard
pnpm install && pnpm build && pnpm start
```

## Configuration

### Initialize Configuration

```bash
uv run python tools/init_config.py
# or docker compose exec backend python tools/init_config.py
```

Follow the prompts to set up exchanges, notification channels, and thresholds. Supported parameters:
- `--force`: Overwrite existing configuration
- `--non-interactive`: Copy template directly

### Telegram Binding Process

1. Enable Telegram in Dashboard "Notification Channels", save `telegram.token`
2. Enter username in "Telegram Recipients" tab to generate binding token
3. User sends `/bind <token>` to bot to complete binding

### Environment Variable Configuration

Copy `.env.example` to `.env` and adjust:

**Docker Deployment Example:**
```env
NEXT_PUBLIC_API_BASE=
BACKEND_INTERNAL_URL=http://backend:8000
PRICESENTRY_ALLOWED_ORIGINS=http://frontend:3000
```

**Manual Deployment Example:**
```env
NEXT_PUBLIC_API_BASE=https://api.example.com
BACKEND_INTERNAL_URL=http://127.0.0.1:8000
PRICESENTRY_ALLOWED_ORIGINS=https://app.example.com
```

**Variable Descriptions:**
- `NEXT_PUBLIC_API_BASE`: Public address for frontend to access backend (leave empty to use Next.js proxy)
- `BACKEND_INTERNAL_URL`: Internal address for Dashboard to access backend
- `PRICESENTRY_ALLOWED_ORIGINS`: Allowed frontend addresses for CORS (comma-separated)

## Common Commands

| Function | Command |
| --- | --- |
| Initialize config | `uv run python tools/init_config.py` |
| Start monitoring | `uv run python -m app.runner` |
| Update trading pairs | `uv run python tools/update_markets.py` |
| Run tests | `uv run pytest` |

## Screenshots

<table align="center">
  <tr>
    <td align="center" valign="middle">
      <img src="https://raw.githubusercontent.com/Xeron2000/PriceSentry/refs/heads/main/img/web.jpg" alt="Dashboard Screenshot" width="520">
    </td>
    <td align="center" valign="middle">
      <img src="https://raw.githubusercontent.com/Xeron2000/PriceSentry/refs/heads/main/img/tg.jpg" alt="Telegram Notification Example" width="520">
    </td>
  </tr>
</table>

## Project Structure

```
PriceSentry/
├── src/
│   ├── core/          Core processes and scheduling
│   ├── exchanges/     Exchange integration implementations
│   ├── notifications/ Notification channel adapters
│   └── utils/         Utilities for caching, alerts, validation, etc.
├── dashboard/         Next.js frontend
├── tests/             Unit and integration tests
└── config/            Configuration file directory
```

## Documentation

- [Configuration Guide](docs/CONFIG.md)
- [配置指南（中文）](docs/CONFIG_CN.md)

## License

MIT License - See [LICENSE](LICENSE) for details
