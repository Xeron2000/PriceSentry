#!/usr/bin/env python3
"""
简化的配置检查工具
用于快速验证配置文件的基本格式和必需字段
"""

import os
from pathlib import Path

import yaml


def check_config_file():
    """检查配置文件是否存在"""
    config_path = Path("config/config.yaml")
    if not config_path.exists():
        print("❌ 配置文件不存在: config/config.yaml")
        return False
    return True


def check_yaml_syntax():
    """检查YAML语法"""
    try:
        with open("config/config.yaml", "r", encoding="utf-8") as f:
            yaml.safe_load(f)
        print("✅ YAML语法正确")
        return True
    except yaml.YAMLError as e:
        print(f"❌ YAML语法错误: {e}")
        return False


def check_basic_fields():
    """检查基本字段"""
    try:
        with open("config/config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        required_fields = [
            "exchange",
            "defaultTimeframe",
            "defaultThreshold",
            "notificationChannels",
        ]

        missing_fields = []
        for field in required_fields:
            if field not in config:
                missing_fields.append(field)

        if missing_fields:
            print(f"❌ 缺少必需字段: {', '.join(missing_fields)}")
            return False

        print("✅ 基本字段完整")
        return True
    except Exception as e:
        print(f"❌ 检查基本字段时出错: {e}")
        return False


def check_exchange_config():
    """检查交易所配置"""
    try:
        with open("config/config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        exchange = config.get("exchange", "")
        if exchange not in ["binance", "okx", "bybit"]:
            print(f"❌ 无效的交易所: {exchange}")
            return False

        print(f"✅ 交易所配置正确: {exchange}")
        return True
    except Exception as e:
        print(f"❌ 检查交易所配置时出错: {e}")
        return False


def check_telegram_config():
    """检查Telegram配置"""
    try:
        with open("config/config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if "telegram" in config and "telegram" in config.get(
            "notificationChannels", []
        ):
            telegram = config.get("telegram", {})
            token = telegram.get("token", "")
            chat_id = telegram.get("chatId", "")

            if not token or not chat_id:
                print("❌ Telegram配置不完整")
                return False

            # 简单的token格式检查
            if ":" not in token:
                print("❌ Telegram token格式错误")
                return False

            print("✅ Telegram配置正确")
        return True
    except Exception as e:
        print(f"❌ 检查Telegram配置时出错: {e}")
        return False


def check_directory_structure():
    """检查目录结构"""
    required_dirs = ["config", "logs"]
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            print(f"❌ 缺少目录: {dir_name}")
            os.makedirs(dir_name)
            print(f"✅ 已创建目录: {dir_name}")
        else:
            print(f"✅ 目录存在: {dir_name}")
    return True


def check_symbols_file():
    """检查交易对文件"""
    symbols_path = Path("config/symbols.txt")
    if not symbols_path.exists():
        print("⚠️  交易对文件不存在: config/symbols.txt")
        print("   系统将自动获取交易对列表")
        return True

    try:
        with open(symbols_path, "r", encoding="utf-8") as f:
            symbols = [line.strip() for line in f.readlines() if line.strip()]

        if len(symbols) == 0:
            print("⚠️  交易对文件为空")
            return True

        print(f"✅ 交易对文件存在，包含 {len(symbols)} 个交易对")
        return True
    except Exception as e:
        print(f"❌ 检查交易对文件时出错: {e}")
        return False


def show_config_summary():
    """显示配置摘要"""
    try:
        with open("config/config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        print("\n📋 配置摘要:")
        print(f"   交易所: {config.get('exchange', 'N/A')}")
        print(f"   时间周期: {config.get('defaultTimeframe', 'N/A')}")
        print(f"   阈值: {config.get('defaultThreshold', 'N/A')}%")
        print(f"   通知渠道: {', '.join(config.get('notificationChannels', []))}")
        cache_enabled = config.get("cache", {}).get("enabled", False)
        print(f"   缓存: {'启用' if cache_enabled else '禁用'}")

        perf_monitoring_enabled = config.get("performance_monitoring", {}).get(
            "enabled", False
        )
        print(f"   性能监控: {'启用' if perf_monitoring_enabled else '禁用'}")
        print(f"   图表: {'启用' if config.get('attachChart', False) else '禁用'}")

    except Exception as e:
        print(f"❌ 显示配置摘要时出错: {e}")


def main():
    """主函数"""
    print("🔍 PriceSentry 配置检查 (简化版)")
    print("=" * 50)

    checks = [
        ("配置文件存在", check_config_file),
        ("YAML语法", check_yaml_syntax),
        ("基本字段", check_basic_fields),
        ("交易所配置", check_exchange_config),
        ("Telegram配置", check_telegram_config),
        ("目录结构", check_directory_structure),
        ("交易对文件", check_symbols_file),
    ]

    all_passed = True

    for check_name, check_func in checks:
        print(f"\n📋 {check_name}:")
        if not check_func():
            all_passed = False

    print("\n" + "=" * 50)

    if all_passed:
        print("🎉 所有检查通过！配置文件已就绪。")
        show_config_summary()
        print("\n🚀 启动应用:")
        print("   python3 -m app.runner")
        print("\n📊 查看配置:")
        print("   cat config/config.yaml")
        print("\n🔧 生成配置:")
        print("   python3 -m app.config_generator")
    else:
        print("❌ 检查失败，请修复上述问题后重试。")
        print("\n💡 帮助:")
        print("   - 查看配置文档: docs/CONFIG.md")
        print("   - 查看示例配置: config/config.yaml.example")
        print("   - 使用配置生成器: python3 -m app.config_generator")
        print("   - 提交问题: https://github.com/Xeron2000/PriceSentry/issues")

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
