# PriceSentry

加密货币期货价格监控，支持 Telegram 推送。

## 快速开始

```bash
uvx --from git+https://github.com/Xeron2000/PriceSentry.git pricesentry
```

首次运行会引导配置：
1. 从 [@BotFather](https://t.me/botfather) 获取 Bot Token
2. 从 [@userinfobot](https://t.me/userinfobot) 获取 Chat ID
3. 选择交易所 (okx/bybit/binance)
4. 直接回车使用 auto 模式（监控成交量前20）

## 配置

编辑 `config/config.yaml`：

```yaml
exchange: "okx"
defaultTimeframe: "5m"
checkInterval: "1m"
defaultThreshold: 1

# Auto 模式：监控24h成交量前20的交易对（每4小时刷新）
notificationSymbols: "auto"

# 或手动指定：
# notificationSymbols:
#   - "BTC/USDT:USDT"
#   - "ETH/USDT:USDT"

telegram:
  token: "your-bot-token"
  chatId: "your-chat-id"
```

## 命令

| 操作 | 命令 |
|------|------|
| 启动 | `pricesentry` |
| 更新市场数据 | `uv run python tools/update_markets.py` |

## 许可证

MIT
