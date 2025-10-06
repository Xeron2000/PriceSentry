#!/usr/bin/env python3
"""
PriceSentry 配置生成器
交互式生成配置文件
"""

from pathlib import Path

import yaml


def get_input(prompt, default=None, required=True):
    """获取用户输入"""
    if default:
        prompt = f"{prompt} (默认: {default}): "
    else:
        prompt = f"{prompt}: "

    while True:
        value = input(prompt).strip()
        if value:
            return value
        elif default is not None:
            return default
        elif not required:
            return None
        else:
            print("⚠️  此项为必填项，请输入值")


def generate_config():
    """生成配置文件"""
    print("🚀 PriceSentry 配置生成器")
    print("=" * 50)
    print("请回答以下问题来生成配置文件\n")

    config = {}

    # 基础配置
    print("📊 基础配置")
    print("-" * 30)

    exchanges = ["binance", "okx", "bybit"]
    print("可选交易所:", ", ".join(exchanges))

    config["exchange"] = get_input("选择主要交易所", "okx")

    print("选择要获取市场数据的交易所 (多选，用空格分隔)")
    for i, exchange in enumerate(exchanges):
        print(f"  {i + 1}. {exchange}")

    exchange_input = get_input("输入交易所编号 (如: 1 2 3)", "1 2 3")
    exchange_indices = [int(x.strip()) - 1 for x in exchange_input.split()]
    config["exchanges"] = [
        exchanges[i] for i in exchange_indices if 0 <= i < len(exchanges)
    ]

    timeframes = ["1m", "5m", "15m", "1h", "1d"]
    print(f"\n可选时间周期: {', '.join(timeframes)}")
    config["defaultTimeframe"] = get_input("选择默认时间周期", "5m")

    config["defaultThreshold"] = float(
        get_input("价格变化阈值 (如: 0.01 表示1%)", "0.01")
    )
    config["symbolsFilePath"] = get_input(
        "交易对文件路径 (留空自动获取)", "config/symbols.txt", False
    )

    # 通知配置
    print("\n📱 通知配置")
    print("-" * 30)

    notification_channels = []
    print("选择通知渠道:")
    print("  1. Telegram")
    print("  2. 不启用通知")

    notification_choice = get_input("输入选择 (1/2)", "1")
    if notification_choice == "1":
        notification_channels.append("telegram")

    config["notificationChannels"] = notification_channels

    if "telegram" in notification_channels:
        print("\n📱 Telegram 配置")
        telegram_token = get_input("Telegram Bot Token", required=False)
        telegram_chat_id = get_input("Telegram Chat ID", required=False)

        if telegram_token and telegram_chat_id:
            config["telegram"] = {"token": telegram_token, "chatId": telegram_chat_id}

    # 时区配置
    print("\n🌍 时区配置")
    config["notificationTimezone"] = get_input("通知时区", "Asia/Shanghai")

    # 日志配置
    print("\n📝 日志配置")
    log_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
    print(f"可选日志级别: {', '.join(log_levels)}")
    config["logLevel"] = get_input("选择日志级别", "INFO")

    # 高级配置
    print("\n⚙️  高级配置")
    print("-" * 30)

    enable_cache = get_input("启用缓存系统? (y/n)", "y").lower() == "y"
    if enable_cache:
        config["cache"] = {
            "enabled": True,
            "max_size": int(get_input("最大缓存条目数", "1000")),
            "default_ttl": int(get_input("缓存过期时间(秒)", "300")),
            "strategy": get_input("缓存策略 (lru/lfu/fifo/ttl)", "lru"),
        }

    enable_performance = get_input("启用性能监控? (y/n)", "y").lower() == "y"
    if enable_performance:
        config["performance_monitoring"] = {
            "enabled": True,
            "collect_interval": int(get_input("数据收集间隔(秒)", "60")),
            "log_performance": True,
            "alert_thresholds": {
                "cpu": float(get_input("CPU告警阈值(%)", "80.0")),
                "memory": float(get_input("内存告警阈值(%)", "80.0")),
                "response_time": float(get_input("响应时间告警阈值(秒)", "5.0")),
            },
        }

    # 图表配置
    print("\n📈 图表配置")
    enable_chart = get_input("启用价格图表? (y/n)", "y").lower() == "y"
    if enable_chart:
        config["attachChart"] = True
        config["chartTimeframe"] = get_input("图表时间周期", "1m")
        config["chartLookbackMinutes"] = int(get_input("历史数据分钟数", "60"))
        config["chartTheme"] = get_input("图表主题 (dark/light)", "dark")
        config["chartImageWidth"] = int(get_input("图表宽度(像素)", "1600"))
        config["chartImageHeight"] = int(get_input("图表高度(像素)", "1200"))
    else:
        config["attachChart"] = False

    return config


def save_config(config, filename="config/config.yaml"):
    """保存配置文件"""
    # 确保目录存在
    Path("config").mkdir(exist_ok=True)

    # 保存配置
    with open(filename, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)

    print(f"\n✅ 配置文件已保存到: {filename}")


def main():
    """主函数"""
    try:
        config = generate_config()

        print("\n" + "=" * 50)
        print("📋 生成的配置:")
        print(yaml.dump(config, default_flow_style=False, allow_unicode=True, indent=2))

        confirm = get_input("\n💾 保存配置文件? (y/n)", "y").lower() == "y"
        if confirm:
            save_config(config)
            print("\n🎉 配置文件生成完成！")
            print("\n📝 下一步:")
            print("   1. 运行配置检查: python check_config.py")
            print("   2. 启动应用: python -m app.runner")
            print("   3. 查看文档: docs/CONFIG.md")
        else:
            print("\n❌ 配置未保存")

    except KeyboardInterrupt:
        print("\n\n❌ 配置生成已取消")
    except Exception as e:
        print(f"\n❌ 配置生成失败: {e}")
        print("请检查输入并重试")


if __name__ == "__main__":
    main()
