"""
FastAPI数据转发层
为PriceSentry提供REST API和WebSocket实时数据推送
"""

import asyncio
import hmac
import json
import logging
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Header,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 导入现有模块
from core.config_manager import ManagerUpdateResult, config_manager
from notifications.telegram import send_telegram_message
from utils.cache_manager import alert_cache, price_cache
from utils.performance_monitor import performance_monitor
from utils.telegram_recipient_store import (
    TelegramRecipient,
    TelegramRecipientStore,
)

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


class ConfigUpdatePayload(BaseModel):
    config: Dict[str, Any]


class ConfigUpdateResult(BaseModel):
    success: bool
    errors: List[str] = []
    warnings: List[str] = []
    message: Optional[str] = None


class VerifyKeyPayload(BaseModel):
    key: Optional[str] = None


class VerifyKeyResponse(BaseModel):
    valid: bool


class ChartMetadata(BaseModel):
    symbols: List[str] = []
    timeframe: Optional[str] = None
    lookbackMinutes: Optional[int] = None
    theme: Optional[str] = None
    generatedAt: float


class ChartImageResponse(BaseModel):
    hasImage: bool
    imageBase64: Optional[str] = None
    metadata: Optional[ChartMetadata] = None


class HealthResponse(BaseModel):
    status: str
    timestamp: float
    version: str
    python_backend: str
    websocket_connections: int
    prices_count: int


class TelegramRecipientPayload(BaseModel):
    id: int
    username: str
    token: str
    userId: Optional[int] = None
    status: str
    createdAt: float
    updatedAt: float


class TelegramRecipientListResponse(BaseModel):
    success: bool
    recipients: List[TelegramRecipientPayload]


class CreateRecipientRequest(BaseModel):
    username: str


class CreateRecipientResponse(BaseModel):
    success: bool
    token: str
    recipient: TelegramRecipientPayload


class DeleteRecipientResponse(BaseModel):
    success: bool


# 全局数据存储
class APIDataStore:
    def __init__(self):
        self.current_prices: Dict[str, Any] = {}
        self.system_stats: Dict[str, Any] = {}
        self.exchange_instance = None
        self.sentry_instance = None
        self.latest_chart: Optional[Dict[str, Any]] = None
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

    def set_latest_chart(self, chart_info: Dict[str, Any]):
        """记录最新的K线图像快照"""
        self.latest_chart = chart_info
        self.logger.debug("Updated latest chart snapshot")

    def get_latest_chart(self) -> Optional[Dict[str, Any]]:
        """返回最新的K线图像快照"""
        return self.latest_chart

    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的告警"""
        return alert_cache.get_recent_alerts(limit)

    def get_alerts_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取告警历史"""
        return alert_cache.get_alerts_history(limit)


# 全局数据存储实例
data_store = APIDataStore()
recipient_store = TelegramRecipientStore()


def _recipient_to_payload(recipient: TelegramRecipient) -> Dict[str, Any]:
    return {
        "id": recipient.id,
        "username": recipient.username,
        "token": recipient.token,
        "userId": recipient.user_id,
        "status": recipient.status,
        "createdAt": recipient.created_at,
        "updatedAt": recipient.updated_at,
    }


def _load_telegram_config() -> Dict[str, Any]:
    try:
        config = config_manager.get_config(copy_result=False)
    except Exception:
        return {}
    return config.get("telegram", {}) if isinstance(config, dict) else {}


def _verify_webhook_secret(request: Request, telegram_config: Dict[str, Any]) -> None:
    secret = telegram_config.get("webhookSecret")
    if not secret:
        return

    provided = (
        request.headers.get("X-Telegram-Token")
        or request.headers.get("X-Telegram-Secret")
        or request.query_params.get("secret")
    )
    if not provided or not hmac.compare_digest(str(provided), str(secret)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook secret",
        )


def _build_recipient_payload(recipient: TelegramRecipient) -> TelegramRecipientPayload:
    return TelegramRecipientPayload(**_recipient_to_payload(recipient))


def _reply_via_bot(chat_id: int, text: str, telegram_config: Dict[str, Any]) -> None:
    bot_token = telegram_config.get("token")
    if not bot_token:
        logging.warning("Telegram bot token missing; cannot reply to webhook user.")
        return
    send_telegram_message(text, bot_token, str(chat_id))


def _load_dashboard_access_key() -> Tuple[Optional[str], bool]:
    """读取dashboard访问密钥以及是否强制要求"""
    try:
        config = config_manager.get_config()
    except Exception:
        return None, False
    security_cfg = config.get("security", {}) if isinstance(config, dict) else {}
    key = security_cfg.get("dashboardAccessKey")
    require_key = bool(security_cfg.get("requireDashboardKey", False))

    if not key:
        key = config.get("dashboardAccessKey") if isinstance(config, dict) else None
        require_key = bool(config.get("requireDashboardKey", False))

    # 如果未提供密钥则无法强制要求
    if not key:
        require_key = False

    return key, require_key


def require_dashboard_key(x_dashboard_key: Optional[str] = Header(None)) -> None:
    """FastAPI依赖: 验证请求头中的Dashboard密钥"""
    expected_key, require_key = _load_dashboard_access_key()

    if not require_key:
        # 未强制要求密钥，直接放行（但允许客户端自愿携带）
        return None

    if not expected_key or not x_dashboard_key or x_dashboard_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid dashboard key",
        )


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


@app.post("/api/auth/verify", response_model=VerifyKeyResponse)
async def verify_dashboard_key(payload: VerifyKeyPayload):
    """校验Dashboard访问密钥是否正确"""
    expected, _ = _load_dashboard_access_key()
    if expected:
        return VerifyKeyResponse(valid=(payload.key or "") == expected)
    return VerifyKeyResponse(valid=True)


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
        config = config_manager.get_config()

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


@app.get("/api/config/full")
async def get_full_config(_: None = Depends(require_dashboard_key)):
    """获取完整配置（含敏感字段，需密钥访问）"""
    try:
        config = config_manager.get_config()
        return {"success": True, "data": config, "timestamp": time.time()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/config", response_model=ConfigUpdateResult)
async def update_system_config_payload(
    payload: ConfigUpdatePayload, _key_ok: None = Depends(require_dashboard_key)
):
    """更新系统配置文件"""
    if not isinstance(payload.config, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Config payload must be an object",
        )
    try:
        update_result: ManagerUpdateResult = config_manager.update_config(
            payload.config
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to update config: {exc}"
        ) from exc

    if not update_result.success:
        return ConfigUpdateResult(
            success=False,
            errors=update_result.errors,
            warnings=update_result.warnings,
            message=update_result.message,
        )

    return ConfigUpdateResult(
        success=True,
        warnings=update_result.warnings,
        message=update_result.message,
        errors=[],
    )


@app.get(
    "/api/telegram/recipients",
    response_model=TelegramRecipientListResponse,
)
async def list_telegram_recipients(_key_ok: None = Depends(require_dashboard_key)):
    recipients = [_build_recipient_payload(rec) for rec in recipient_store.list_all()]
    return TelegramRecipientListResponse(success=True, recipients=recipients)


@app.post(
    "/api/telegram/recipients",
    response_model=CreateRecipientResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_telegram_recipient(
    payload: CreateRecipientRequest, _key_ok: None = Depends(require_dashboard_key)
):
    token = recipient_store.add_pending(payload.username)
    created = next(
        (rec for rec in recipient_store.list_all() if rec.token == token),
        None,
    )
    if created is None:
        raise HTTPException(status_code=500, detail="Failed to create recipient")
    return CreateRecipientResponse(
        success=True,
        token=token,
        recipient=_build_recipient_payload(created),
    )


@app.delete(
    "/api/telegram/recipients/{recipient_id}",
    response_model=DeleteRecipientResponse,
)
async def delete_telegram_recipient(
    recipient_id: int, _key_ok: None = Depends(require_dashboard_key)
):
    deleted = recipient_store.delete(recipient_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found"
        )
    return DeleteRecipientResponse(success=True)


@app.post("/api/telegram/webhook")
async def telegram_webhook(request: Request, payload: Dict[str, Any]):
    telegram_config = _load_telegram_config()
    _verify_webhook_secret(request, telegram_config)

    message = payload.get("message") or payload.get("edited_message")
    if not isinstance(message, dict):
        return {"ok": True}

    text = (message.get("text") or "").strip()
    if not text.lower().startswith("/bind"):
        return {"ok": True}

    parts = text.split()
    if len(parts) < 2:
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        if isinstance(chat_id, int):
            _reply_via_bot(chat_id, "格式错误，请使用 /bind <token>", telegram_config)
        return {"ok": True}

    token = parts[1]
    sender = message.get("from") or {}
    user_id = sender.get("id")
    username = sender.get("username")
    chat = message.get("chat") or {}
    chat_id = chat.get("id") or user_id

    if not isinstance(user_id, int) or not isinstance(chat_id, int):
        return {"ok": True}

    status = recipient_store.confirm_binding(token, user_id, username)

    if status == "confirmed":
        _reply_via_bot(chat_id, "绑定成功喵！后续会收到通知~", telegram_config)
    elif status == "already_active":
        _reply_via_bot(chat_id, "已经绑定过了喵~", telegram_config)
    else:
        _reply_via_bot(chat_id, "令牌无效，请确认后重试", telegram_config)

    return {"ok": True}


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


@app.get("/api/charts/latest", response_model=ChartImageResponse)
async def get_latest_chart_image(_: None = Depends(require_dashboard_key)):
    """获取最近推送的K线图像"""
    chart = data_store.get_latest_chart()
    if not chart:
        return ChartImageResponse(hasImage=False, imageBase64=None, metadata=None)
    metadata = chart.get("metadata")
    image_base64 = chart.get("imageBase64")
    if not image_base64:
        return ChartImageResponse(hasImage=False, imageBase64=None, metadata=metadata)
    return ChartImageResponse(
        hasImage=True, imageBase64=image_base64, metadata=metadata
    )


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
def update_api_data(prices=None, alerts=None, stats=None, chart_image=None, sentry_instance=None):
    """更新API数据（供现有系统调用）"""
    try:
        if prices is not None:
            data_store.update_prices(prices)

        if alerts is not None:
            data_store.add_alert(alerts)

        if stats is not None:
            data_store.update_stats(stats)

        if chart_image is not None:
            data_store.set_latest_chart(chart_image)

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
