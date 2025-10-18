# PriceSentry 配置指南

本文介绍如何根据最新的精简模板配置 PriceSentry。配置文件默认位于 `config/config.yaml`，请基于示例文件手动编辑或通过 Dashboard 进行配置。

---

## 快速开始

```bash
uv run python tools/init_config.py
# 根据提示完成交互式初始化，或使用 --non-interactive 跳过问答
uv run python -m app.runner                # 启动服务
```

> 如果要使用 Dashboard，请同时设置其环境变量
>
> ```bash
> # dashboard/.env.local
> NEXT_PUBLIC_API_BASE=http://localhost:8000
> ```
>
> `NEXT_PUBLIC_API_BASE` 指向 FastAPI 后端根地址；未设置时默认使用 `http://localhost:8000`。

---

## 必需配置

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

- **exchange**：主交易所，支持 `binance` / `okx` / `bybit`。
- **defaultTimeframe**：行情监控的 K 线窗口，常用值 `1m`、`5m`、`15m`、`1h`、`1d`。
- **checkInterval**：监控任务的调度频率，例如设置为 `1m` 表示每分钟检查一次最新 K 线；若缺省则自动回退到 `defaultTimeframe`。
- **defaultThreshold**：触发告警的价格变动百分比。
- **notificationChannels**：当前仅支持 `telegram`。
- **notificationSymbols**：指定需要推送告警的合约交易对列表。缺省或移除字段表示推送所有监控到的交易对。
- **telegram.token**：机器人 Bot Token。启用 Telegram 通知时必须提供。
- **notificationTimezone**：告警消息的时区。未配置或为空时，系统会回退至 `Asia/Shanghai`。

> 默认情况下，系统会监控支持的 USDT 合约交易对。若希望仅向 Telegram 推送部分交易对，在 `notificationSymbols` 中列出所需的符号即可；字段缺省或为空值时视作推送全部。

---

## Telegram 额外选项

```yaml
telegram:
  token: "YOUR_TELEGRAM_BOT_TOKEN"
  chatId: "123456789"        # 可选：回退推送目标
  # webhookSecret: "secret"    # 可选：Webhook 校验密钥
```

- **chatId**：为兼容旧流程的回退目标。当未绑定任何用户时使用。
- **webhookSecret**：仅在使用 Telegram Webhook 校验来源时需要。留空或移除该字段即视为未配置；若填写，建议长度≥6。

> 建议搭配 Dashboard 中的绑定流程，让用户自行绑定通知目标，而不是依赖 `chatId`。

---

## 图表附件（可选）

设置 `attachChart: true` 时，告警消息会附带多币种 K 线图。可选参数如下：

```yaml
attachChart: true
chartTimeframe: "5m"
chartLookbackMinutes: 500
chartTheme: "dark"          # "dark" | "light"
chartIncludeMA: [7, 25]     # 为空列表则不绘制均线
chartImageWidth: 1600
chartImageHeight: 1200
chartImageScale: 2          # 1/2/3
```

若关闭图表功能，可简单地设置 `attachChart: false` 并移除其余字段。

---

## Dashboard 访问控制

```yaml
security:
  dashboardAccessKey: "pricesentry"
```

- **dashboardAccessKey**：访问敏感接口（例如 `/api/config/full`）时的密钥，所有受保护请求都会强制校验 `X-Dashboard-Key` 头部。

前端会自动在所有请求上注入密钥请求头，来源于 Dashboard 登录表单。确保 `NEXT_PUBLIC_API_BASE` 指向正确的后端，否则会出现 404 或跨域错误。

---

## 默认启用的特性

以下模块已经在代码中默认开启，无需配置项即可工作：

- 缓存系统（基于 `utils/cache_manager.py` 的内置设置）
- 错误处理重试与熔断逻辑
- 性能监控（自动收集指标并提供 `/api/stats`）

---

## 常见问题

1. **`tools/update_markets.py` 会使用哪些交易所？**  
   当未显式指定 `--exchanges` 参数时，脚本会读取配置文件中的主交易所 `exchange` 作为更新目标。

2. **如何仅推送部分交易对？**  
   在 `notificationSymbols` 中列出需要推送的合约交易对即可；字段缺省或被移除时默认推送全部监控到的交易对。

3. **首次启动时如何获取交易对？**  
   后端会在缺少 `config/supported_markets.json` 或未缓存对应交易所时自动拉取 USDT 合约交易对，并写入该文件。也可以按需运行 `tools/update_markets.py` 定期刷新。

4. **没有配置 Telegram 但启用了渠道？**  
   如果 `notificationChannels` 包含 `telegram`，`telegram.token` 必须配置，否则启动阶段会报错并拒绝运行。

## 配置变更建议

- 仅保留实际需要的键，避免冗余字段干扰维护。
- 编辑完配置后可直接运行 `uv run python -m app.runner` 验证服务是否能正常启动。
- 若通过 Dashboard 修改配置，系统会自动验证并在成功后热更新。

> 该文档与 `config/config.yaml.example` 保持同步。若在升级过程中发现字段不匹配，请优先以模板为准。
