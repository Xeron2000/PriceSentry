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
- Telegram、钉钉双通道推送价格波动与健康检查
- YAML 配置驱动，内置校验与智能缓存机制
- 性能监控、熔断与指数退避重试保障稳定性

## 快速开始

```bash
git clone https://github.com/Xeron2000/PriceSentry.git
cd PriceSentry
uv sync
uv run python -m app.runner
```

## 配置说明

1. 复制 `config/config.yaml.example` 为 `config/config.yaml`
2. 设置目标交易所、通知渠道与阈值
3. 填写 Telegram 机器人凭据

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
