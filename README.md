# PriceSentry

Cryptocurrency futures price monitoring with Telegram alerts.

## Quick Start

```bash
uvx --from git+https://github.com/Xeron2000/PriceSentry.git pricesentry
```

First run will guide you through setup:
1. Get Bot Token from [@BotFather](https://t.me/botfather)
2. Get Chat ID from [@userinfobot](https://t.me/userinfobot)
3. Select exchange (okx/bybit/binance)
4. Press Enter for auto mode (monitors top 20 by volume)

## Configuration

Edit `config/config.yaml`:

```yaml
exchange: "okx"
defaultTimeframe: "5m"
checkInterval: "1m"
defaultThreshold: 1

# Auto mode: monitors top 20 symbols by 24h volume (refreshes every 4h)
notificationSymbols: "auto"

# Or specify manually:
# notificationSymbols:
#   - "BTC/USDT:USDT"
#   - "ETH/USDT:USDT"

telegram:
  token: "your-bot-token"
  chatId: "your-chat-id"
```

## Commands

| Action | Command |
|--------|---------|
| Start | `pricesentry` |
| Update markets | `uv run python tools/update_markets.py` |

## License

MIT
