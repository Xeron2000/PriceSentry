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
cp config/config.yaml.example config/config.yaml
# 更新 config/config.yaml 后再启动服务，避免缺失配置导致报错
uv run python -m app.runner

# （可选）启动前端 Dashboard 以图形化管理配置
cd dashboard
pnpm install
pnpm build
pnpm start
```

> 如果只运行后端，通过编辑 `config/config.yaml` 即可完成全部功能；前端 Dashboard 提供可视化体验但并非必需。

## 配置说明

1. 复制 `config/config.yaml.example` 为 `config/config.yaml`
2. 设置目标交易所、通知渠道与阈值
3. 在配置中填写 Telegram Bot Token 和 ChatID ，并且可以在控制面板添加多个接收人

> 注意：若未按上述步骤复制并完善配置文件，直接运行程序会因缺失配置而报错。

### Telegram 通知绑定流程

1. 在 Dashboard「通知渠道」页启用 Telegram，并保存包含 `telegram.token` 的配置。
2. 切换到新增加的「Telegram 接收人」标签，输入用户名生成绑定令牌。
3. 让目标用户与机器人对话并发送 `/bind <token>`，机器人会自动确认并加入通知列表。
4. 如需兼容旧流程，可在配置中保留 `telegram.chatId`，消息会优先发送至该 chat，再广播至所有绑定用户。

更多选项可参考示例文件注释，或运行 `uv run python tools/update_markets.py` 更新支持的市场列表。

## 可用脚本

| 功能 | 命令 |
| --- | --- |
| 启动监控 | `uv run python -m app.runner` |
| 刷新交易对列表 | `uv run python tools/update_markets.py` |
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
├── core/           核心流程与调度
├── exchanges/      交易所接入实现
├── notifications/  推送渠道适配
├── utils/          缓存、告警、校验等工具
└── tests/          单元与集成测试
```

## 许可

项目以 MIT 许可证开源，详见 `LICENSE`。
