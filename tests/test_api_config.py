"""
FastAPI测试套件 - 确保所有API端点正常工作
"""

import json
import time
from typing import Any, Dict, List

import requests
import websocket

# API配置
BASE_URL = "http://localhost:8000"
API_BASE_URL = f"{BASE_URL}/api"
WS_URL = "ws://localhost:8000/ws"

# 测试配置
TEST_CONFIG = {
    "timeout": 30,
    "retry_attempts": 3,
    "retry_delay": 1,
    "test_symbols": ["BTC/USDT:USDT", "ETH/USDT:USDT"],
}


class APITestClient:
    """API测试客户端"""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "PriceSentry-API-Test/1.0"})

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """GET请求"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        return self._make_request("GET", url, **kwargs)

    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """POST请求"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        return self._make_request("POST", url, **kwargs)

    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """带重试的请求"""
        kwargs.setdefault("timeout", 10)

        for attempt in range(TEST_CONFIG["retry_attempts"]):
            try:
                response = self.session.request(method, url, **kwargs)
                return response
            except requests.exceptions.RequestException:
                if attempt == TEST_CONFIG["retry_attempts"] - 1:
                    raise
                time.sleep(TEST_CONFIG["retry_delay"])

    def close(self):
        """关闭会话"""
        self.session.close()


class WebSocketTestClient:
    """WebSocket测试客户端"""

    def __init__(self, url: str = WS_URL):
        self.url = url
        self.ws = None
        self.messages = []
        self.connected = False

    def connect(self) -> bool:
        """连接WebSocket"""
        try:
            self.ws = websocket.create_connection(
                self.url, timeout=TEST_CONFIG["timeout"]
            )
            self.connected = True
            return True
        except Exception as e:
            print(f"WebSocket连接失败: {e}")
            return False

    def receive_messages(self, count: int = 5, timeout: int = 10) -> List[Dict]:
        """接收消息"""
        messages = []
        start_time = time.time()

        while len(messages) < count and (time.time() - start_time) < timeout:
            try:
                message = self.ws.recv()
                if message:
                    data = json.loads(message)
                    messages.append(data)
            except Exception as e:
                print(f"接收消息失败: {e}")
                break

        return messages

    def close(self):
        """关闭连接"""
        if self.ws:
            self.ws.close()
        self.connected = False


def validate_json_response(response: requests.Response) -> Dict[str, Any]:
    """验证JSON响应"""
    assert response.status_code == 200, f"状态码错误: {response.status_code}"
    assert response.headers.get("content-type", "").startswith("application/json"), (
        f"Content-Type错误: {response.headers.get('content-type')}"
    )

    data = response.json()
    assert isinstance(data, dict), "响应必须是JSON对象"
    return data


def validate_success_response(data: Dict[str, Any]) -> Any:
    """验证成功响应格式"""
    assert "success" in data, "响应缺少success字段"
    assert data["success"] is True, f"请求失败: {data.get('message', '未知错误')}"
    assert "data" in data, "响应缺少data字段"
    assert "timestamp" in data, "响应缺少timestamp字段"
    return data["data"]


def price_data_generator():
    """生成测试价格数据"""
    import random

    return {
        "BTC/USDT:USDT": 50000.0 + random.uniform(-1000, 1000),
        "ETH/USDT:USDT": 3000.0 + random.uniform(-100, 100),
    }


def alert_data_generator():
    """生成测试告警数据"""
    import random

    symbols = ["BTC/USDT:USDT", "ETH/USDT:USDT"]
    return {
        "symbol": random.choice(symbols),
        "message": f"测试告警 - 价格变动 {random.uniform(-5, 5):.2f}%",
        "severity": random.choice(["info", "warning", "error"]),
        "price": 50000.0 + random.uniform(-1000, 1000),
        "change": random.uniform(-5, 5),
        "threshold": 1.0,
        "minutes": 5,
    }


# 测试数据
TEST_PRICE_DATA = price_data_generator()
TEST_ALERT_DATA = alert_data_generator()

print("🧪 API测试套件初始化完成")
print(f"📡 API基础URL: {API_BASE_URL}")
print(f"🔌 WebSocket URL: {WS_URL}")
print(f"📊 测试价格数据: {TEST_PRICE_DATA}")
print(f"🚨 测试告警数据: {TEST_ALERT_DATA}")
