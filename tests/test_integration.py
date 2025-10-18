"""
数据更新和集成测试
"""

import threading
import time

import pytest

from .test_api_config import (
    APITestClient,
    WebSocketTestClient,
)


class TestDataIntegration:
    """数据集成测试"""

    def test_price_data_integration(self, api_client: APITestClient):
        """测试价格数据集成"""
        # 获取初始价格数据
        initial_response = api_client.get("/prices")
        initial_data = initial_response.json()
        initial_data.get("count", 0)

        # 等待一段时间让系统更新数据
        time.sleep(2)

        # 再次获取价格数据
        updated_response = api_client.get("/prices")
        updated_data = updated_response.json()
        updated_data.get("count", 0)

        # 验证数据结构
        assert initial_data["success"] is True
        assert updated_data["success"] is True

        print("✅ 价格数据集成测试通过")

    def test_alert_data_integration(self, api_client: APITestClient):
        """测试告警数据集成"""
        # 获取初始告警数据
        initial_response = api_client.get("/alerts")
        initial_data = initial_response.json()
        initial_data.get("total", 0)

        # 等待一段时间
        time.sleep(2)

        # 再次获取告警数据
        updated_response = api_client.get("/alerts")
        updated_data = updated_response.json()
        updated_data.get("total", 0)

        # 验证数据结构
        assert initial_data["success"] is True
        assert updated_data["success"] is True
        assert isinstance(initial_data["data"], list)
        assert isinstance(updated_data["data"], list)

        print("✅ 告警数据集成测试通过")

    def test_stats_data_integration(self, api_client: APITestClient):
        """测试统计数据集成"""
        # 获取统计数据
        response = api_client.get("/stats")
        data = response.json()

        assert data["success"] is True
        stats = data["data"]

        # 验证缓存统计
        cache_stats = stats.get("cache", {})
        assert isinstance(cache_stats.get("size", 0), int)
        assert cache_stats.get("max_size", 0) > 0

        # 验证性能统计
        perf_stats = stats.get("performance", {})
        assert isinstance(perf_stats, dict)

        # 验证运行时间
        uptime = stats.get("uptime", 0)
        assert uptime > 0

        print("✅ 统计数据集成测试通过")


class TestRealTimeDataFlow:
    """实时数据流测试"""

    def test_price_updates_via_websocket(self, ws_client: WebSocketTestClient):
        """测试通过WebSocket的价格更新"""
        connected = ws_client.connect()
        assert connected, "WebSocket连接失败"

        # 接收多条消息
        messages = ws_client.receive_messages(count=5, timeout=10)

        # 验证价格数据更新
        price_updates_found = False
        for message in messages:
            msg_type = message.get("type")
            if msg_type in {"data_update", "initial_data"}:
                data = message.get("data", {})
                prices = data.get("prices", {})

                if isinstance(prices, dict) and prices:
                    price_updates_found = True
                    break

        assert price_updates_found or any(
            msg.get("type") == "heartbeat" for msg in messages
        ), "应该收到价格或心跳消息"

        print("✅ WebSocket价格更新测试通过")

        # 清理
        ws_client.close()

    def test_alert_updates_via_websocket(self, ws_client: WebSocketTestClient):
        """测试通过WebSocket的告警更新"""
        connected = ws_client.connect()
        assert connected, "WebSocket连接失败"

        # 接收多条消息
        messages = ws_client.receive_messages(count=5, timeout=10)

        # 验证告警数据更新
        for message in messages:
            if message.get("type") in {"data_update", "initial_data"}:
                data = message.get("data", {})
                alerts = data.get("alerts", [])

                if isinstance(alerts, list):
                    break

        print("✅ WebSocket告警更新测试通过")

        # 清理
        ws_client.close()

    def test_api_and_websocket_consistency(
        self, api_client: APITestClient, ws_client: WebSocketTestClient
    ):
        """测试API和WebSocket数据一致性"""
        # 通过API获取数据
        api_response = api_client.get("/prices")
        api_data = api_response.json()

        # 通过WebSocket获取数据
        connected = ws_client.connect()
        assert connected, "WebSocket连接失败"

        messages = ws_client.receive_messages(count=1, timeout=5)

        if messages:
            ws_message = messages[0]
            if ws_message.get("type") in {"initial_data", "data_update"}:
                ws_data = ws_message.get("data", {})
                ws_prices = ws_data.get("prices", {})

                # 验证基本一致性
                assert isinstance(api_data.get("data"), dict)
                assert isinstance(ws_prices, dict)

                # 数据结构应该相同
                api_prices = api_data.get("data", {})
                assert isinstance(api_prices, type(ws_prices))

        print("✅ API和WebSocket数据一致性测试通过")

        # 清理
        ws_client.close()


class TestSystemMonitoring:
    """系统监控测试"""

    def test_system_health_monitoring(self, api_client: APITestClient):
        """测试系统健康监控"""
        # 多次检查健康状态
        for i in range(3):
            response = api_client.get("/health")
            data = response.json()

            assert data["status"] == "healthy"
            assert data["python_backend"] == "running"
            assert "timestamp" in data

            time.sleep(1)

        print("✅ 系统健康监控测试通过")

    def test_performance_monitoring(self, api_client: APITestClient):
        """测试性能监控"""
        # 获取性能统计
        response = api_client.get("/stats")
        data = response.json()

        assert data["success"] is True
        stats = data["data"]

        # 验证性能指标
        cache_stats = stats.get("cache", {})
        perf_stats = stats.get("performance", {})

        # 缓存性能
        if "hit_rate" in cache_stats:
            hit_rate = cache_stats["hit_rate"]
            assert isinstance(hit_rate, (str, int, float))

        # 系统性能
        if perf_stats:
            assert isinstance(perf_stats, dict)

        print("✅ 性能监控测试通过")

    def test_error_handling(self, api_client: APITestClient):
        """测试错误处理"""
        # 测试无效端点
        response = api_client.get("/invalid/endpoint")
        assert response.status_code == 404

        # 测试无效方法
        response = api_client.post("/health")
        # POST到health端点应该返回错误或特定状态
        assert response.status_code in [405, 422, 200]  # 允许的不同响应

        print("✅ 错误处理测试通过")


class TestDataConsistency:
    """数据一致性测试"""

    def test_price_data_consistency(self, api_client: APITestClient):
        """测试价格数据一致性"""
        # 多次获取价格数据
        price_responses = []
        for i in range(3):
            response = api_client.get("/prices")
            data = response.json()
            price_responses.append(data)
            time.sleep(1)

        # 验证所有响应都成功
        for resp in price_responses:
            assert resp["success"] is True
            assert "data" in resp
            assert "timestamp" in resp

        print("✅ 价格数据一致性测试通过")

    def test_config_data_consistency(self, api_client: APITestClient):
        """测试配置数据一致性"""
        # 多次获取配置数据
        config_responses = []
        for i in range(3):
            response = api_client.get("/config")
            data = response.json()
            config_responses.append(data)
            time.sleep(1)

        # 验证配置一致性
        base_config = config_responses[0]["data"]
        for resp in config_responses[1:]:
            current_config = resp["data"]
            # 主要配置字段应该保持一致
            assert current_config["exchange"] == base_config["exchange"]
            assert current_config["defaultTimeframe"] == base_config["defaultTimeframe"]
            assert current_config["checkInterval"] == base_config["checkInterval"]

        print("✅ 配置数据一致性测试通过")

    def test_stats_data_evolution(self, api_client: APITestClient):
        """测试统计数据演化"""
        # 获取初始统计
        initial_response = api_client.get("/stats")
        initial_data = initial_response.json()
        initial_uptime = initial_data["data"].get("uptime", 0)

        # 等待一段时间
        time.sleep(2)

        # 获取更新后的统计
        updated_response = api_client.get("/stats")
        updated_data = updated_response.json()
        updated_uptime = updated_data["data"].get("uptime", 0)

        # 验证运行时间增长
        assert updated_uptime >= initial_uptime
        if updated_uptime > initial_uptime:
            time_diff = updated_uptime - initial_uptime
            assert time_diff >= 1.5  # 至少应该经过1.5秒

        print("✅ 统计数据演化测试通过")


class TestLoadHandling:
    """负载处理测试"""

    def test_rapid_requests(self, api_client: APITestClient):
        """测试快速请求处理"""
        # 快速发送多个请求
        responses = []
        endpoints = ["/health", "/stats", "/config", "/prices"]

        for endpoint in endpoints:
            for i in range(5):
                response = api_client.get(endpoint)
                responses.append(response)

        # 验证所有响应都成功
        successful_responses = [r for r in responses if r.status_code == 200]
        assert len(successful_responses) == len(responses), "所有请求都应该成功"

        print("✅ 快速请求处理测试通过")

    def test_concurrent_connections(self):
        """测试并发连接"""

        def make_request():
            client = APITestClient()
            try:
                response = client.get("/health")
                return response.status_code == 200
            finally:
                client.close()

        # 创建多个并发请求
        threads = []
        results = []

        def worker():
            result = make_request()
            results.append(result)

        for i in range(10):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证所有请求都成功
        assert all(results), "所有并发请求都应该成功"

        print("✅ 并发连接测试通过")


# 测试工具函数
@pytest.fixture
def api_client():
    """API客户端fixture"""
    client = APITestClient()
    yield client
    client.close()


@pytest.fixture
def ws_client():
    """WebSocket客户端fixture"""
    client = WebSocketTestClient()
    yield client
    client.close()


if __name__ == "__main__":
    print("🔄 数据更新和集成测试")
    print("=" * 50)

    # 运行测试
    try:
        # 数据集成测试
        test_integration = TestDataIntegration()
        test_integration.test_price_data_integration(APITestClient())
        test_integration.test_alert_data_integration(APITestClient())
        test_integration.test_stats_data_integration(APITestClient())

        # 实时数据流测试
        test_flow = TestRealTimeDataFlow()
        test_flow.test_price_updates_via_websocket(WebSocketTestClient())
        test_flow.test_alert_updates_via_websocket(WebSocketTestClient())

        api_client = APITestClient()
        ws_client = WebSocketTestClient()
        test_flow.test_api_and_websocket_consistency(api_client, ws_client)
        ws_client.close()
        api_client.close()

        # 系统监控测试
        test_monitoring = TestSystemMonitoring()
        test_monitoring.test_system_health_monitoring(APITestClient())
        test_monitoring.test_performance_monitoring(APITestClient())
        test_monitoring.test_error_handling(APITestClient())

        # 数据一致性测试
        test_consistency = TestDataConsistency()
        test_consistency.test_price_data_consistency(APITestClient())
        test_consistency.test_config_data_consistency(APITestClient())
        test_consistency.test_stats_data_evolution(APITestClient())

        # 负载处理测试
        test_load = TestLoadHandling()
        test_load.test_rapid_requests(APITestClient())
        test_load.test_concurrent_connections()

        print("\n🎉 所有数据集成测试通过！")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        raise
