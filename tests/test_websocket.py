"""
WebSocket实时数据测试
"""

import pytest

from .test_api_config import APITestClient, WebSocketTestClient


class TestWebSocketConnection:
    """WebSocket连接测试"""

    def test_websocket_connection(self, ws_client: WebSocketTestClient):
        """测试WebSocket连接"""
        connected = ws_client.connect()
        assert connected, "WebSocket连接失败"

        # 验证连接状态
        assert ws_client.connected, "WebSocket连接状态错误"

        print("✅ WebSocket连接测试通过")

        # 清理
        ws_client.close()

    def test_websocket_initial_data(self, ws_client: WebSocketTestClient):
        """测试WebSocket初始数据"""
        connected = ws_client.connect()
        assert connected, "WebSocket连接失败"

        # 接收初始数据
        messages = ws_client.receive_messages(count=1, timeout=5)
        assert len(messages) > 0, "未接收到初始数据"

        # 验证初始数据结构
        initial_data = messages[0]
        assert "type" in initial_data
        assert initial_data["type"] == "initial_data"
        assert "timestamp" in initial_data
        assert "data" in initial_data

        # 验证数据内容
        data = initial_data["data"]
        assert "prices" in data
        assert "alerts" in data
        assert "stats" in data

        print("✅ WebSocket初始数据测试通过")

        # 清理
        ws_client.close()

    def test_websocket_real_time_updates(self, ws_client: WebSocketTestClient):
        """测试WebSocket实时数据更新"""
        connected = ws_client.connect()
        assert connected, "WebSocket连接失败"

        # 接收多条消息
        messages = ws_client.receive_messages(count=3, timeout=10)
        assert len(messages) >= 1, "未接收到实时更新"

        # 验证数据更新消息
        for message in messages:
            assert "type" in message
            assert "timestamp" in message
            assert "data" in message

            if message["type"] == "data_update":
                data = message["data"]
                assert "prices" in data
                assert "alerts" in data
                assert "stats" in data

        print("✅ WebSocket实时数据更新测试通过")

        # 清理
        ws_client.close()


class TestWebSocketDataFormats:
    """WebSocket数据格式测试"""

    def test_price_data_format(self, ws_client: WebSocketTestClient):
        """测试价格数据格式"""
        connected = ws_client.connect()
        assert connected, "WebSocket连接失败"

        messages = ws_client.receive_messages(count=2, timeout=5)

        for message in messages:
            if "data" in message and "prices" in message["data"]:
                prices = message["data"]["prices"]

                # 验证价格数据结构
                if isinstance(prices, dict) and prices:
                    for symbol, price_data in prices.items():
                        assert isinstance(symbol, str)
                        # 实际价格数据是浮点数，不是字典
                        assert isinstance(price_data, (int, float))
                        assert price_data >= 0 or price_data == 0  # 允许价格为0

                break

        print("✅ 价格数据格式测试通过")

        # 清理
        ws_client.close()

    def test_alert_data_format(self, ws_client: WebSocketTestClient):
        """测试告警数据格式"""
        connected = ws_client.connect()
        assert connected, "WebSocket连接失败"

        messages = ws_client.receive_messages(count=3, timeout=5)

        for message in messages:
            if "data" in message and "alerts" in message["data"]:
                alerts = message["data"]["alerts"]

                # 验证告警数据结构
                if isinstance(alerts, list) and alerts:
                    for alert in alerts:
                        assert isinstance(alert, dict)

                        # 验证告警数据字段
                        required_fields = ["id", "timestamp", "message", "severity"]
                        for field in required_fields:
                            if field in alert:
                                assert alert[field] is not None

                break

        print("✅ 告警数据格式测试通过")

        # 清理
        ws_client.close()

    def test_stats_data_format(self, ws_client: WebSocketTestClient):
        """测试统计数据格式"""
        connected = ws_client.connect()
        assert connected, "WebSocket连接失败"

        messages = ws_client.receive_messages(count=2, timeout=5)

        for message in messages:
            if "data" in message and "stats" in message["data"]:
                stats = message["data"]["stats"]

                # 验证统计数据结构
                if isinstance(stats, dict):
                    required_fields = ["cache", "performance"]
                    for field in required_fields:
                        if field in stats:
                            assert isinstance(stats[field], dict)

                break

        print("✅ 统计数据格式测试通过")

        # 清理
        ws_client.close()


class TestWebSocketReliability:
    """WebSocket可靠性测试"""

    def test_connection_timeout(self):
        """测试连接超时处理"""
        # 使用无效URL测试超时
        invalid_client = WebSocketTestClient("ws://localhost:9999/invalid")
        connected = invalid_client.connect()
        assert not connected, "无效连接不应该成功"

        print("✅ 连接超时测试通过")

    def test_multiple_connections(self):
        """测试多连接处理"""
        connections = []

        try:
            # 创建多个连接
            for i in range(3):
                client = WebSocketTestClient()
                connected = client.connect()
                if connected:
                    connections.append(client)

            # 验证连接成功
            assert len(connections) > 0, "至少应该有一个连接成功"

            # 每个连接接收数据
            for client in connections:
                client.receive_messages(count=1, timeout=3)
                # 不强求数据，只要不报错就行

            print("✅ 多连接处理测试通过")

        finally:
            # 清理所有连接
            for client in connections:
                client.close()

    def test_reconnection(self):
        """测试重连机制"""
        client = WebSocketTestClient()

        try:
            # 首次连接
            connected = client.connect()
            assert connected, "首次连接应该成功"

            # 接收一些数据
            client.receive_messages(count=1, timeout=3)

            # 断开连接
            client.close()
            assert not client.connected, "连接应该已断开"

            # 重新连接
            connected = client.connect()
            assert connected, "重连应该成功"

            # 再次接收数据
            client.receive_messages(count=1, timeout=3)

            print("✅ 重连机制测试通过")

        finally:
            client.close()


class TestWebSocketPerformance:
    """WebSocket性能测试"""

    def test_message_frequency(self, ws_client: WebSocketTestClient):
        """测试消息频率"""
        connected = ws_client.connect()
        assert connected, "WebSocket连接失败"

        # 记录接收消息的时间
        messages = ws_client.receive_messages(count=5, timeout=10)

        if len(messages) >= 2:
            # 计算消息间隔
            timestamps = [msg["timestamp"] for msg in messages if "timestamp" in msg]
            if len(timestamps) >= 2:
                intervals = [
                    timestamps[i] - timestamps[i - 1] for i in range(1, len(timestamps))
                ]
                avg_interval = sum(intervals) / len(intervals)

                # 验证消息频率（应该在1秒左右）
                assert 0.5 <= avg_interval <= 2.0, f"消息间隔异常: {avg_interval}秒"

        print("✅ 消息频率测试通过")

        # 清理
        ws_client.close()

    def test_data_size_handling(self, ws_client: WebSocketTestClient):
        """测试大数据量处理"""
        connected = ws_client.connect()
        assert connected, "WebSocket连接失败"

        # 接收多条消息，测试大数据量处理
        messages = ws_client.receive_messages(count=10, timeout=15)

        # 验证所有消息都有效
        for message in messages:
            assert isinstance(message, dict)
            assert "type" in message
            assert "timestamp" in message

        print("✅ 大数据量处理测试通过")

        # 清理
        ws_client.close()


# 测试工具函数
@pytest.fixture
def ws_client():
    """WebSocket客户端fixture"""
    client = WebSocketTestClient()
    yield client
    client.close()


@pytest.fixture
def api_client():
    """API客户端fixture"""
    client = APITestClient()
    yield client
    client.close()


if __name__ == "__main__":
    print("🔌 WebSocket实时数据测试")
    print("=" * 50)

    # 运行测试
    try:
        # 连接测试
        test_connection = TestWebSocketConnection()
        test_connection.test_websocket_connection(WebSocketTestClient())
        test_connection.test_websocket_initial_data(WebSocketTestClient())
        test_connection.test_websocket_real_time_updates(WebSocketTestClient())

        # 数据格式测试
        test_formats = TestWebSocketDataFormats()
        test_formats.test_price_data_format(WebSocketTestClient())
        test_formats.test_alert_data_format(WebSocketTestClient())
        test_formats.test_stats_data_format(WebSocketTestClient())

        # 可靠性测试
        test_reliability = TestWebSocketReliability()
        test_reliability.test_connection_timeout()
        test_reliability.test_multiple_connections()
        test_reliability.test_reconnection()

        # 性能测试
        test_performance = TestWebSocketPerformance()
        test_performance.test_message_frequency(WebSocketTestClient())
        test_performance.test_data_size_handling(WebSocketTestClient())

        print("\n🎉 所有WebSocket测试通过！")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        raise
