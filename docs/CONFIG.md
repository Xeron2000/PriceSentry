# PriceSentry Configuration Guide

<p align="right">
  <a href="CONFIG.md">English</a> | 
  <a href="CONFIG_CN.md">简体中文</a>
</p>

This guide explains how to configure PriceSentry based on the latest streamlined template. The configuration file is located at `config/config.yaml` by default. You can edit it manually based on the example file or configure it through the Dashboard.

---

## Quick Start

```bash
uv run python tools/init_config.py
# Complete interactive initialization following the prompts, or use --non-interactive to skip Q&A
uv run python -m app.runner                # Start service
```

> If you want to use the Dashboard, also set its environment variables
>
> ```bash
> # dashboard/.env.local
> NEXT_PUBLIC_API_BASE=http://localhost:8000
> BACKEND_INTERNAL_URL=http://localhost:8000
> ```
>
> `NEXT_PUBLIC_API_BASE` points to the FastAPI backend root address. If left empty with Next.js proxy enabled, requests will be forwarded through the Dashboard. `BACKEND_INTERNAL_URL` is used for internal access in proxy mode, typically set to `http://backend:8000` in Docker environments.
>
> If the Dashboard image is built and pushed by CI/CD, pass `BACKEND_INTERNAL_URL=http://backend:8000` during the build stage. For local manual builds, provide the same build arg to ensure the proxy target is correct.

---

## Required Configuration

```yaml
exchange: "okx"
defaultTimeframe: "5m"
checkInterval: "1m"
defaultThreshold: 1
notificationChannels:
  - "telegram"
telegram:
  token: "YOUR_TELEGRAM_BOT_TOKEN"
notificationTimezone: "Asia/Shanghai"
```

- **exchange**: Primary exchange, supports `binance` / `okx` / `bybit`.
- **defaultTimeframe**: K-line window for market monitoring, common values: `1m`, `5m`, `15m`, `1h`, `1d`.
- **checkInterval**: Scheduling frequency for monitoring tasks, e.g., setting it to `1m` means checking latest K-line every minute. If omitted, automatically falls back to `defaultTimeframe`.
- **defaultThreshold**: Price change percentage to trigger alerts.
- **notificationChannels**: Currently only supports `telegram`.
- **notificationSymbols**: Specifies the list of futures trading pairs that need alert notifications. If omitted or removed, all monitored trading pairs will be notified.
- **telegram.token**: Bot token. Required when Telegram notifications are enabled.
- **notificationTimezone**: Timezone for alert messages. If not configured or empty, the system falls back to `Asia/Shanghai`.

> By default, the system monitors supported USDT futures trading pairs. If you only want to push certain trading pairs to Telegram, list the required symbols in `notificationSymbols`. If the field is omitted or empty, all pairs will be pushed.

---

## Additional Telegram Options

```yaml
telegram:
  token: "YOUR_TELEGRAM_BOT_TOKEN"
  chatId: "123456789"        # Optional: Fallback notification target
  # webhookSecret: "secret"    # Optional: Webhook validation secret
```

- **chatId**: Fallback target for compatibility with old workflows. Used when no users are bound.
- **webhookSecret**: Only needed when using Telegram Webhook source validation. Leave empty or remove this field to indicate it's not configured. If filled, recommend length ≥6.

> It's recommended to use the binding process in the Dashboard, letting users bind their notification targets themselves rather than relying on `chatId`.

---

## Chart Attachments (Optional)

When `attachChart: true` is set, alert messages will include multi-currency K-line charts. Optional parameters:

```yaml
attachChart: true
chartTimeframe: "5m"
chartLookbackMinutes: 500
chartTheme: "dark"          # "dark" | "light"
chartIncludeMA: [7, 25]     # Empty list means no moving averages
chartImageWidth: 1600
chartImageHeight: 1200
chartImageScale: 2          # 1/2/3
```

To disable chart functionality, simply set `attachChart: false` and remove other fields.

---

## Dashboard Access Control

```yaml
security:
  dashboardAccessKey: "pricesentry"
```

- **dashboardAccessKey**: Key for accessing sensitive endpoints (e.g., `/api/config/full`). All protected requests will force validation of the `X-Dashboard-Key` header.

The frontend automatically injects the key request header on all requests, sourced from the Dashboard login form. If using Next.js proxy, ensure `BACKEND_INTERNAL_URL` matches the backend container address. If accessing the backend directly, still need `NEXT_PUBLIC_API_BASE` to point to the correct address, otherwise 404 or CORS errors will occur.

---

## Features Enabled by Default

The following modules are enabled by default in the code and work without configuration:

- Caching system (based on built-in settings in `utils/cache_manager.py`)
- Error handling retry and circuit breaker logic
- Performance monitoring (automatically collects metrics and provides `/api/stats`)

---

## FAQ

1. **Which exchanges does `tools/update_markets.py` use?**  
   When the `--exchanges` parameter is not explicitly specified, the script reads the primary exchange `exchange` from the configuration file as the update target.

2. **How to only push certain trading pairs?**  
   List the futures trading pairs you want to push in `notificationSymbols`. If the field is omitted or removed, all monitored trading pairs will be pushed by default.

3. **How are trading pairs fetched on first startup?**  
   The backend automatically pulls USDT futures trading pairs when `config/supported_markets.json` is missing or when the corresponding exchange is not cached, and writes them to the file. You can also run `tools/update_markets.py` as needed to refresh periodically.

4. **What if Telegram is not configured but the channel is enabled?**  
   If `notificationChannels` includes `telegram`, `telegram.token` must be configured, otherwise the startup phase will report an error and refuse to run.

## Configuration Change Recommendations

- Only keep keys that are actually needed to avoid redundant fields interfering with maintenance.
- After editing the configuration, run `uv run python -m app.runner` directly to verify if the service starts normally.
- If modifying configuration through the Dashboard, the system will automatically validate and hot-update on success.

> This document stays in sync with `config/config.yaml.example`. If you find field mismatches during upgrades, prioritize the template.
