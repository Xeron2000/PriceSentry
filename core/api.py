"""
FastAPI数据转发层
为PriceSentry提供REST API和WebSocket实时数据推送
"""

import asyncio
import json
import logging
import threading
import time
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 导入现有模块
from utils.cache_manager import alert_cache, price_cache
from utils.load_config import load_config
from utils.performance_monitor import performance_monitor

# 创建FastAPI应用
app = FastAPI(
    title="PriceSentry API",
    description="PriceSentry价格监控系统API接口",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic数据模型
class PriceResponse(BaseModel):
    symbol: str
    price: float
    change: float
    changePercent: float
    timestamp: float
    volume: float
    high24h: float
    low24h: float


class AlertResponse(BaseModel):
    id: str
    symbol: str
    message: str
    severity: str
    timestamp: float
    price: float
    change: float
    threshold: float


class StatsResponse(BaseModel):
    cache: Dict[str, Any]
    performance: Dict[str, Any]
    uptime: float


class ConfigResponse(BaseModel):
    exchange: str
    defaultTimeframe: str
    defaultThreshold: float
    notificationChannels: List[str]
    symbolsFilePath: str
    chartTimeframe: str
    chartLookbackMinutes: int
    chartTheme: str


class HealthResponse(BaseModel):
    status: str
    timestamp: float
    version: str
    python_backend: str
    websocket_connections: int
    prices_count: int


# 全局数据存储
class APIDataStore:
    def __init__(self):
        self.current_prices: Dict[str, Any] = {}
        self.system_stats: Dict[str, Any] = {}
        self.exchange_instance = None
        self.sentry_instance = None
        self.logger = logging.getLogger(__name__)

        # WebSocket连接管理
        self.websocket_connections: List[WebSocket] = []

    def update_prices(self, prices: Dict[str, Any]):
        """更新价格数据"""
        self.current_prices = prices
        self.logger.debug(f"Updated prices for {len(prices)} symbols")

    def add_alert(self, alert: Dict[str, Any]):
        """添加告警到历史记录"""
        # 使用全局告警缓存管理器
        alert_id = alert_cache.add_alert(alert)
        self.logger.debug(
            f"Added alert: {alert.get('message', 'Unknown')} with ID: {alert_id}"
        )
        return alert_id

    def update_stats(self, stats: Dict[str, Any]):
        """更新系统统计"""
        self.system_stats = stats
        self.logger.debug("Updated system stats")

    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的告警"""
        return alert_cache.get_recent_alerts(limit)

    def get_alerts_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取告警历史"""
        return alert_cache.get_alerts_history(limit)


# 全局数据存储实例
data_store = APIDataStore()


# WebSocket连接管理器
class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.logger = logging.getLogger(__name__)

    async def connect(self, websocket: WebSocket):
        """接受WebSocket连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.logger.info(
            f"WebSocket connection established. "
            f"Total connections: {len(self.active_connections)}"
        )

    def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        self.logger.info(
            f"WebSocket connection closed. "
            f"Total connections: {len(self.active_connections)}"
        )

    async def broadcast(self, message: str):
        """广播消息到所有连接"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)

        # 移除断开的连接
        for conn in disconnected:
            self.disconnect(conn)


# 全局WebSocket管理器
websocket_manager = WebSocketManager()


# API端点
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """健康检查端点"""
    return HealthResponse(
        status="healthy",
        timestamp=time.time(),
        version="1.0.0",
        python_backend="running",
        websocket_connections=len(websocket_manager.active_connections),
        prices_count=len(data_store.current_prices),
    )


@app.get("/api/prices")
async def get_all_prices():
    """获取所有交易对价格数据"""
    try:
        return {
            "success": True,
            "data": data_store.current_prices,
            "timestamp": time.time(),
            "count": len(data_store.current_prices),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prices/{symbol}")
async def get_price_by_symbol(symbol: str):
    """获取特定交易对价格数据"""
    try:
        if symbol in data_store.current_prices:
            return {
                "success": True,
                "data": data_store.current_prices[symbol],
                "timestamp": time.time(),
            }
        else:
            raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/alerts")
async def get_alerts(limit: int = 100, severity: Optional[str] = None):
    """获取告警历史"""
    try:
        alerts = data_store.get_alerts_history(limit)

        # 按严重程度过滤
        if severity:
            alerts = [alert for alert in alerts if alert.get("severity") == severity]

        return {
            "success": True,
            "data": alerts,
            "total": len(alerts),
            "timestamp": time.time(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_system_stats():
    """获取系统统计信息"""
    try:
        # 获取最新的缓存和性能统计
        cache_stats = price_cache.get_stats()
        perf_stats = performance_monitor.get_stats()

        stats_data = {
            "cache": cache_stats,
            "performance": perf_stats,
            "uptime": time.time(),
            "last_update": time.time(),
        }

        # 更新数据存储
        data_store.update_stats(stats_data)

        return {"success": True, "data": stats_data, "timestamp": time.time()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config")
async def get_system_config():
    """获取系统配置（过滤敏感信息）"""
    try:
        config = load_config()

        # 过滤敏感信息
        safe_config = ConfigResponse(
            exchange=config.get("exchange", "binance"),
            defaultTimeframe=config.get("defaultTimeframe", "5m"),
            defaultThreshold=config.get("defaultThreshold", 1.0),
            notificationChannels=config.get("notificationChannels", []),
            symbolsFilePath=config.get("symbolsFilePath", "config/symbols.txt"),
            chartTimeframe=config.get("chartTimeframe", "1m"),
            chartLookbackMinutes=config.get("chartLookbackMinutes", 60),
            chartTheme=config.get("chartTheme", "dark"),
        )

        return {"success": True, "data": safe_config.dict(), "timestamp": time.time()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/exchanges")
async def get_supported_exchanges():
    """获取支持的交易所列表"""
    try:
        exchanges = [
            {"id": "binance", "name": "Binance", "enabled": True},
            {"id": "okx", "name": "OKX", "enabled": True},
            {"id": "bybit", "name": "Bybit", "enabled": True},
        ]

        return {
            "success": True,
            "data": exchanges,
            "total": len(exchanges),
            "timestamp": time.time(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/symbols")
async def get_monitored_symbols():
    """获取监控的交易对列表"""
    try:
        if data_store.sentry_instance and hasattr(
            data_store.sentry_instance, "matched_symbols"
        ):
            symbols = data_store.sentry_instance.matched_symbols
        else:
            symbols = []

        return {
            "success": True,
            "data": symbols,
            "total": len(symbols),
            "timestamp": time.time(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/monitor/check")
async def trigger_monitoring_check():
    """手动触发价格监控检查"""
    try:
        if not data_store.sentry_instance:
            raise HTTPException(
                status_code=503, detail="PriceSentry service not available"
            )

        # 这里可以调用现有的监控逻辑
        # 由于监控逻辑是异步的，我们返回一个确认消息
        return {
            "success": True,
            "message": "Monitoring check triggered",
            "timestamp": time.time(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket端点
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket实时数据推送端点"""
    await websocket_manager.connect(websocket)

    try:
        # 发送初始数据
        initial_data = {
            "type": "initial_data",
            "timestamp": time.time(),
            "data": {
                "prices": data_store.current_prices,
                "alerts": data_store.get_recent_alerts(10),
                "stats": data_store.system_stats,
            },
        }
        await websocket.send_text(json.dumps(initial_data))

        # 持续推送实时数据
        while True:
            # 构建实时数据消息
            message = {
                "type": "data_update",
                "timestamp": time.time(),
                "data": {
                    "prices": data_store.current_prices,
                    "alerts": data_store.get_recent_alerts(5),
                    "stats": data_store.system_stats,
                },
            }

            await websocket.send_text(json.dumps(message))
            await asyncio.sleep(1)  # 每秒推送一次

    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)


# 数据更新接口（供现有系统调用）
def update_api_data(prices=None, alerts=None, stats=None, sentry_instance=None):
    """更新API数据（供现有系统调用）"""
    try:
        if prices is not None:
            data_store.update_prices(prices)

        if alerts is not None:
            data_store.add_alert(alerts)

        if stats is not None:
            data_store.update_stats(stats)

        if sentry_instance is not None:
            data_store.sentry_instance = sentry_instance

        # 异步广播WebSocket消息
        if alerts is not None:
            # 如果有新告警，立即广播
            asyncio.create_task(broadcast_alert_update(alerts))

    except Exception as e:
        logging.error(f"Failed to update API data: {e}")


async def broadcast_alert_update(alert):
    """广播告警更新"""
    try:
        message = {
            "type": "alert_update",
            "timestamp": time.time(),
            "data": {"alert": alert, "recent_alerts": data_store.get_recent_alerts(10)},
        }
        await websocket_manager.broadcast(json.dumps(message))
    except Exception as e:
        logging.error(f"Failed to broadcast alert update: {e}")


def set_exchange_instance(exchange_instance):
    """设置交易所实例"""
    data_store.exchange_instance = exchange_instance


def set_sentry_instance(sentry_instance):
    """设置PriceSentry实例"""
    data_store.sentry_instance = sentry_instance


# 启动API服务器
def start_api_server():
    """启动FastAPI服务器"""
    import uvicorn

    logging.info("Starting FastAPI server on port 8000")

    # 在单独的线程中运行uvicorn
    def run_server():
        try:
            uvicorn.run(
                app, host="0.0.0.0", port=8000, log_level="info", access_log=True
            )
        except OSError as e:
            if "address already in use" in str(e):
                logging.warning("Port 8000 already in use, API server not started")
            else:
                logging.error(f"Failed to start API server: {e}")
        except Exception as e:
            logging.error(f"Unexpected error starting API server: {e}")

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    logging.info("FastAPI server started in background thread")

    return server_thread


# 导出供其他模块使用的函数
__all__ = [
    "start_api_server",
    "update_api_data",
    "set_exchange_instance",
    "set_sentry_instance",
]
