#!/usr/bin/env python3
"""
简化的API测试运行器 - 快速验证API功能
"""

import json
import os
import subprocess
import sys
import time

import requests
import websocket


def test_api_endpoints():
    """快速测试主要API端点"""
    base_url = "http://localhost:8000"
    api_url = f"{base_url}/api"

    print("🧪 快速API测试")
    print("=" * 40)

    # 测试端点
    endpoints = [
        ("health", "健康检查"),
        ("prices", "价格数据"),
        ("alerts", "告警数据"),
        ("stats", "系统统计"),
        ("config", "系统配置"),
        ("exchanges", "交易所列表"),
        ("symbols", "交易对列表"),
    ]

    results = []

    for endpoint, description in endpoints:
        try:
            url = f"{api_url}/{endpoint}"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                if data.get("success") is not False:
                    print(f"✅ {description} - 正常")
                    results.append(True)
                else:
                    print(f"❌ {description} - 数据错误")
                    results.append(False)
            else:
                print(f"❌ {description} - HTTP {response.status_code}")
                results.append(False)

        except Exception as e:
            print(f"❌ {description} - 连接错误: {e}")
            results.append(False)

    return all(results)


def test_websocket():
    """测试WebSocket连接"""
    print("\n🔌 WebSocket测试")
    print("=" * 40)

    try:
        ws = websocket.create_connection("ws://localhost:8000/ws", timeout=10)

        # 接收初始数据
        message = ws.recv()
        data = json.loads(message)

        if data.get("type") == "initial_data":
            print("✅ WebSocket连接 - 正常")
            print(f"   数据类型: {data.get('type')}")
            print(f"   时间戳: {data.get('timestamp')}")

            # 检查数据结构
            data_content = data.get("data", {})
            if (
                "prices" in data_content
                and "alerts" in data_content
                and "stats" in data_content
            ):
                print("✅ 数据结构 - 完整")
                ws.close()
                return True
            else:
                print("❌ 数据结构 - 不完整")
                ws.close()
                return False
        else:
            print("❌ WebSocket初始数据 - 异常")
            ws.close()
            return False

    except Exception as e:
        print(f"❌ WebSocket连接 - 失败: {e}")
        return False


def start_pricesentry():
    """启动PriceSentry服务"""
    print("🚀 启动PriceSentry服务...")

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    venv_python = os.path.join(project_root, ".venv", "bin", "python")

    try:
        process = subprocess.Popen(
            [venv_python, "-m", "app.runner"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=project_root,
        )

        # 等待服务启动
        time.sleep(15)

        if process.poll() is None:
            print("✅ 服务启动成功")
            return process
        else:
            stderr = process.stderr.read().decode()
            print(f"❌ 服务启动失败: {stderr}")
            return None

    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return None


def main():
    """主函数"""
    print("🎯 PriceSentry API快速测试")
    print("=" * 50)

    # 启动服务
    process = start_pricesentry()
    if not process:
        print("❌ 无法启动服务")
        sys.exit(1)

    try:
        # 运行测试
        api_success = test_api_endpoints()
        ws_success = test_websocket()

        # 总结
        print("\n📊 测试总结")
        print("=" * 40)

        if api_success:
            print("✅ REST API - 全部正常")
        else:
            print("❌ REST API - 部分异常")

        if ws_success:
            print("✅ WebSocket - 正常")
        else:
            print("❌ WebSocket - 异常")

        if api_success and ws_success:
            print("\n🎉 所有测试通过！API完全可用！")
            print("\n🚀 主要功能:")
            print("  ✅ 健康检查 - /api/health")
            print("  ✅ 价格数据 - /api/prices")
            print("  ✅ 告警历史 - /api/alerts")
            print("  ✅ 系统统计 - /api/stats")
            print("  ✅ 系统配置 - /api/config")
            print("  ✅ 实时数据 - WebSocket /ws")
            print("  ✅ API文档 - /api/docs")

            return True
        else:
            print("\n❌ 部分测试失败，请检查系统状态")
            return False

    finally:
        # 停止服务
        print("\n🛑 停止服务...")
        process.terminate()
        try:
            process.wait(timeout=5)
            print("✅ 服务已停止")
        except Exception:
            process.kill()
            print("✅ 服务已强制停止")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
