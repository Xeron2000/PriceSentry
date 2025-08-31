#!/usr/bin/env python3
"""
测试钉钉图片发送功能
"""

import base64
import os
import sys
from io import BytesIO

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from notifications.dingding import send_dingding_message, send_dingding_photo


def test_dingding_photo():
    """测试钉钉图片发送功能"""

    # 测试配置 - 请替换为实际的钉钉配置
    test_webhook = "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN"
    test_secret = "YOUR_SECRET"

    # 创建一个简单的测试图片（红色方块）
    from PIL import Image

    # 创建一个简单的测试图片
    img = Image.new("RGB", (200, 200), color="red")
    img_bytes = BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes = img_bytes.getvalue()

    # 将图片转换为 base64 并创建 data URL
    img_base64 = base64.b64encode(img_bytes).decode("utf-8")
    image_url = f"data:image/png;base64,{img_base64}"

    # 测试图片发送
    print("测试钉钉图片发送...")
    result = send_dingding_photo(
        caption="🔥 价格告警测试\n\n这是一个测试图片消息",
        webhook_url=test_webhook,
        secret=test_secret,
        image_bytes=img_bytes,
        image_url=image_url,
    )

    if result:
        print("✅ 钉钉图片发送测试成功")
    else:
        print("❌ 钉钉图片发送测试失败")

    return result


def test_dingding_text():
    """测试钉钉文本消息发送"""

    # 测试配置 - 请替换为实际的钉钉配置
    test_webhook = "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN"
    test_secret = "YOUR_SECRET"

    # 测试文本消息发送
    print("测试钉钉文本消息发送...")
    result = send_dingding_message(
        message="📢 价格告警测试\n\n这是一个测试文本消息",
        webhook_url=test_webhook,
        secret=test_secret,
    )

    if result:
        print("✅ 钉钉文本消息发送测试成功")
    else:
        print("❌ 钉钉文本消息发送测试失败")

    return result


if __name__ == "__main__":
    print("开始测试钉钉通知功能...\n")

    # 注意：请先替换上面的测试配置为实际的钉钉配置

    print("⚠️  请先在脚本中配置正确的钉钉 webhook 和 secret")
    print("测试配置：")
    print("- webhook: 钉钉机器人的 webhook URL")
    print("- secret: 钉钉机器人的签名密钥（如果启用了签名验证）")
    print()

    # 取消注释以进行实际测试
    # test_dingding_text()
    # test_dingding_photo()

    print("测试脚本已准备就绪。请配置测试参数后取消注释测试代码。")
