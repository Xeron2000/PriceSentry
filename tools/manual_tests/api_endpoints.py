#!/usr/bin/env python3
"""
测试FastAPI API端点的功能
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests

# Add project root and src to path so imports work when run manually
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent.parent
SRC_DIR = ROOT_DIR / 'src'
for candidate in (SRC_DIR, ROOT_DIR):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)


def test_api_endpoints():
    """测试所有API端点"""
    base_url = "http://localhost:8000"

    endpoints = [
        ("/api/health", "健康检查"),
        ("/api/prices", "获取所有价格"),
        ("/api/alerts", "获取告警历史"),
        ("/api/stats", "获取系统统计"),
        ("/api/config", "获取系统配置"),
        ("/api/exchanges", "获取支持的交易所"),
        ("/api/symbols", "获取监控的交易对"),
        ("/api/docs", "API文档"),
    ]

    print("🧪 开始测试API端点...\n")

    for endpoint, description in endpoints:
        try:
            url = base_url + endpoint
            print(f"🔍 测试 {description}: {url}")

            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                print(f"✅ {description} - 成功")
                if endpoint not in ["/api/docs"]:
                    try:
                        data = response.json()
                        json_str = json.dumps(data, indent=2, ensure_ascii=False)
                        print(f"   数据: {json_str[:150]}...")
                    except Exception:
                        print(f"   响应: {response.text[:200]}...")
            else:
                print(f"❌ {description} - 失败 (状态码: {response.status_code})")

        except requests.exceptions.RequestException as e:
            print(f"❌ {description} - 连接错误: {e}")

        print("-" * 50)

    print("\n🎯 API端点测试完成！")


def start_pricesentry():
    """启动PriceSentry服务"""
    print("🚀 启动PriceSentry服务...")

    # 激活虚拟环境并启动服务
    cmd = [f"{os.getcwd()}/.venv/bin/python", "-m", "app.runner"]

    try:
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.getcwd()
        )

        # 等待服务启动
        print("⏳ 等待服务启动...")
        time.sleep(10)

        return process
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return None


def main():
    """主函数"""
    print("🎯 PriceSentry API 测试工具")
    print("=" * 50)

    # 启动服务
    process = start_pricesentry()

    if process is None:
        print("❌ 无法启动服务，测试终止")
        return

    try:
        # 测试API端点
        test_api_endpoints()

    finally:
        # 停止服务
        print("\n🛑 停止PriceSentry服务...")
        process.terminate()
        try:
            process.wait(timeout=5)
            print("✅ 服务已停止")
        except subprocess.TimeoutExpired:
            process.kill()
            print("✅ 服务已强制停止")


if __name__ == "__main__":
    main()
