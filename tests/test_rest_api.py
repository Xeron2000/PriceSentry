"""
REST API端点测试
"""

import json

import pytest

from .test_api_config import (
    APITestClient,
    validate_json_response,
    validate_success_response,
)


class TestHealthEndpoints:
    """健康检查端点测试"""

    def test_health_check(self, api_client: APITestClient):
        """测试健康检查端点"""
        response = api_client.get("/health")
        data = validate_json_response(response)

        # 验证响应结构
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"
        assert data["python_backend"] == "running"
        assert "websocket_connections" in data
        assert "prices_count" in data

        print("✅ 健康检查测试通过")

    def test_api_docs_accessible(self, api_client: APITestClient):
        """测试API文档可访问"""
        response = api_client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

        print("✅ API文档访问测试通过")


class TestPriceEndpoints:
    """价格相关端点测试"""

    def test_get_all_prices(self, api_client: APITestClient):
        """测试获取所有价格"""
        response = api_client.get("/prices")
        data = validate_json_response(response)
        result = validate_success_response(data)

        # 验证数据结构
        assert isinstance(result, dict)
        assert "count" in data
        assert isinstance(data["count"], int)

        print("✅ 获取所有价格测试通过")

    def test_get_price_by_symbol(self, api_client: APITestClient):
        """测试获取特定交易对价格"""
        # 测试存在的交易对
        response = api_client.get("/prices/BTC/USDT:USDT")
        if response.status_code == 200:
            data = validate_json_response(response)
            result = validate_success_response(data)
            assert isinstance(result, dict)
            print("✅ 获取特定交易对价格测试通过")
        else:
            # 如果没有数据，404也是正常的
            assert response.status_code == 404
            print("✅ 获取特定交易对价格测试通过 (无数据)")

    def test_get_price_by_invalid_symbol(self, api_client: APITestClient):
        """测试获取不存在交易对价格"""
        response = api_client.get("/prices/INVALID/PAIR")
        assert response.status_code == 404

        print("✅ 获取不存在交易对价格测试通过")


class TestAlertEndpoints:
    """告警相关端点测试"""

    def test_get_alerts_no_filter(self, api_client: APITestClient):
        """测试获取告警列表（无过滤）"""
        response = api_client.get("/alerts")
        data = validate_json_response(response)
        result = validate_success_response(data)

        # 验证数据结构
        assert isinstance(result, list)
        assert "total" in data
        assert isinstance(data["total"], int)

        print("✅ 获取告警列表测试通过")

    def test_get_alerts_with_limit(self, api_client: APITestClient):
        """测试获取告警列表（带限制）"""
        response = api_client.get("/alerts?limit=5")
        data = validate_json_response(response)
        result = validate_success_response(data)

        assert len(result) <= 5

        print("✅ 获取告警列表（带限制）测试通过")

    def test_get_alerts_with_severity_filter(self, api_client: APITestClient):
        """测试按严重程度过滤告警"""
        response = api_client.get("/alerts?severity=warning")
        data = validate_json_response(response)

        if data["success"] and data["data"]:
            # 如果有数据，验证严重程度过滤
            for alert in data["data"]:
                assert alert.get("severity") == "warning"

        print("✅ 按严重程度过滤告警测试通过")

    def test_get_alerts_invalid_severity(self, api_client: APITestClient):
        """测试无效严重程度过滤"""
        response = api_client.get("/alerts?severity=invalid_severity")
        data = validate_json_response(response)
        # 无效过滤条件应该返回空列表或错误
        assert data["success"] is True

        print("✅ 无效严重程度过滤测试通过")


class TestStatsEndpoints:
    """统计信息端点测试"""

    def test_get_system_stats(self, api_client: APITestClient):
        """测试获取系统统计"""
        response = api_client.get("/stats")
        data = validate_json_response(response)
        result = validate_success_response(data)

        # 验证统计信息结构
        assert "cache" in result
        assert "performance" in result
        assert "uptime" in result

        # 验证缓存统计
        cache_stats = result["cache"]
        assert "size" in cache_stats
        assert "max_size" in cache_stats
        assert "hit_rate" in cache_stats

        print("✅ 获取系统统计测试通过")

    def test_cache_stats_structure(self, api_client: APITestClient):
        """测试缓存统计结构"""
        response = api_client.get("/stats")
        data = validate_json_response(response)
        result = validate_success_response(data)

        cache_stats = result["cache"]
        required_fields = [
            "size",
            "total_entries",
            "max_size",
            "strategy",
            "hit_count",
            "miss_count",
            "hit_rate",
            "evictions",
        ]

        for field in required_fields:
            assert field in cache_stats, f"缺少缓存统计字段: {field}"

        print("✅ 缓存统计结构测试通过")


class TestConfigEndpoints:
    """配置相关端点测试"""

    def test_get_system_config(self, api_client: APITestClient):
        """测试获取系统配置"""
        response = api_client.get("/config")
        data = validate_json_response(response)
        result = validate_success_response(data)

        # 验证配置结构
        required_fields = [
            "exchange",
            "defaultTimeframe",
            "checkInterval",
            "defaultThreshold",
            "notificationChannels",
            "symbolsFilePath",
        ]

        for field in required_fields:
            assert field in result, f"缺少配置字段: {field}"

        # 验证配置值
        assert result["exchange"] in ["binance", "okx", "bybit"]
        assert isinstance(result["notificationChannels"], list)
        assert result["defaultThreshold"] > 0

        print("✅ 获取系统配置测试通过")

    def test_config_no_sensitive_data(self, api_client: APITestClient):
        """测试配置不包含敏感数据"""
        response = api_client.get("/config")
        data = validate_json_response(response)
        result = validate_success_response(data)

        # 确保不包含敏感信息
        sensitive_fields = ["token", "secret", "password", "key", "webhook"]
        result_str = json.dumps(result).lower()

        for field in sensitive_fields:
            assert field not in result_str, f"配置包含敏感字段: {field}"

        print("✅ 配置敏感数据过滤测试通过")


class TestExchangeEndpoints:
    """交易所相关端点测试"""

    def test_get_supported_exchanges(self, api_client: APITestClient):
        """测试获取支持的交易所"""
        response = api_client.get("/exchanges")
        data = validate_json_response(response)
        result = validate_success_response(data)

        # 验证交易所列表
        assert isinstance(result, list)
        assert len(result) > 0

        for exchange in result:
            assert "id" in exchange
            assert "name" in exchange
            assert "enabled" in exchange
            assert isinstance(exchange["enabled"], bool)

        # 验证包含主要交易所
        exchange_ids = [e["id"] for e in result]
        assert "binance" in exchange_ids

        print("✅ 获取支持的交易所测试通过")

    def test_get_monitored_symbols(self, api_client: APITestClient):
        """测试获取监控的交易对"""
        response = api_client.get("/symbols")
        data = validate_json_response(response)
        result = validate_success_response(data)

        # 验证交易对列表
        assert isinstance(result, list)
        assert len(result) > 0

        # 验证交易对格式
        for symbol in result:
            assert isinstance(symbol, str)
            assert "/" in symbol  # 交易对格式

        print("✅ 获取监控的交易对测试通过")


class TestMonitorEndpoints:
    """监控相关端点测试"""

    def test_trigger_monitoring_check(self, api_client: APITestClient):
        """测试手动触发监控检查"""
        response = api_client.post("/monitor/check")
        data = validate_json_response(response)

        # 验证响应
        assert data["success"] is True
        assert "message" in data
        assert "timestamp" in data

        print("✅ 手动触发监控检查测试通过")


# 测试工具函数
@pytest.fixture
def api_client():
    """API客户端fixture"""
    client = APITestClient()
    yield client
    client.close()


if __name__ == "__main__":
    print("🧪 REST API端点测试")
    print("=" * 50)

    # 运行测试
    client = APITestClient()

    try:
        # 健康检查
        test_health = TestHealthEndpoints()
        test_health.test_health_check(client)
        test_health.test_api_docs_accessible(client)

        # 价格端点
        test_prices = TestPriceEndpoints()
        test_prices.test_get_all_prices(client)
        test_prices.test_get_price_by_symbol(client)
        test_prices.test_get_price_by_invalid_symbol(client)

        # 告警端点
        test_alerts = TestAlertEndpoints()
        test_alerts.test_get_alerts_no_filter(client)
        test_alerts.test_get_alerts_with_limit(client)
        test_alerts.test_get_alerts_with_severity_filter(client)
        test_alerts.test_get_alerts_invalid_severity(client)

        # 统计端点
        test_stats = TestStatsEndpoints()
        test_stats.test_get_system_stats(client)
        test_stats.test_cache_stats_structure(client)

        # 配置端点
        test_config = TestConfigEndpoints()
        test_config.test_get_system_config(client)
        test_config.test_config_no_sensitive_data(client)

        # 交易所端点
        test_exchanges = TestExchangeEndpoints()
        test_exchanges.test_get_supported_exchanges(client)
        test_exchanges.test_get_monitored_symbols(client)

        # 监控端点
        test_monitor = TestMonitorEndpoints()
        test_monitor.test_trigger_monitoring_check(client)

        print("\n🎉 所有REST API测试通过！")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        raise
    finally:
        client.close()
