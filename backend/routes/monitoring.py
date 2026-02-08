"""
监控路由模块

提供市场监控和通知接口
"""

from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend.monitoring.market_monitor import get_monitor
from backend.monitoring.signal_generator import get_signal_generator
from backend.monitoring.notification import get_notification_manager
from backend.log import logger


# FastAPI 应用
app = FastAPI(
    title="GX量化监控服务",
    description="提供市场监控、信号生成和通知的 API 服务",
    version="1.0.0"
)


# ========== Pydantic Models ==========

class WatchlistRequest(BaseModel):
    """观察列表请求"""
    symbols: List[str]


class AlertResponse(BaseModel):
    """警报响应"""
    type: str
    symbol: str
    message: str
    severity: str
    timestamp: str


class SignalRequest(BaseModel):
    """生成信号请求"""
    symbol: str
    signal_type: str
    source: str
    confidence: float
    message: str
    price_target: Optional[float] = None
    stop_loss: Optional[float] = None


class NotificationRequest(BaseModel):
    """发送通知请求"""
    notification_type: str
    title: str
    content: str
    priority: str = "normal"


# ========== API Endpoints ==========

@app.get("/", summary="根路径")
async def root():
    """服务根路径"""
    return {
        "service": "GX量化监控服务",
        "version": "1.0.0",
        "status": "running"
    }


@app.post("/watchlist", summary="更新观察列表")
async def update_watchlist(request: WatchlistRequest, action: str = "add"):
    """
    添加或移除观察列表

    - **symbols**: 股票代码列表
    - **action**: add/remove
    """
    monitor = get_monitor()

    if action == "add":
        monitor.add_to_watchlist(request.symbols)
    elif action == "remove":
        monitor.remove_from_watchlist(request.symbols)
    else:
        raise HTTPException(status_code=400, detail="无效操作")

    return {
        "action": action,
        "watchlist_count": len(monitor.watchlist),
        "watchlist": monitor.watchlist
    }


@app.get("/watchlist", summary="获取观察列表")
async def get_watchlist():
    """获取当前观察列表"""
    monitor = get_monitor()
    return {
        "watchlist": monitor.watchlist,
        "count": len(monitor.watchlist)
    }


@app.post("/market/scan", summary="扫描市场")
async def scan_market():
    """
    扫描市场并返回警报

    返回所有价格异动和成交量异动警报
    """
    try:
        monitor = get_monitor()
        alerts = monitor.scan_market()

        return {
            "alerts_count": len(alerts),
            "alerts": [
                {
                    "type": a.alert_type,
                    "symbol": a.symbol,
                    "message": a.message,
                    "severity": a.severity,
                    "timestamp": a.timestamp,
                    "data": a.data
                }
                for a in alerts
            ]
        }

    except Exception as e:
        logger.error(f"市场扫描失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/alerts", summary="获取警报")
async def get_alerts(
    alert_type: Optional[str] = None,
    limit: int = 50
):
    """
    获取最近警报

    - **alert_type**: 警报类型过滤
    - **limit**: 数量限制
    """
    monitor = get_monitor()
    alerts = monitor.get_recent_alerts(alert_type=alert_type, limit=limit)

    return {
        "alerts": alerts,
        "count": len(alerts)
    }


@app.post("/signal", summary="生成交易信号")
async def generate_signal(request: SignalRequest):
    """
    生成交易信号

    - **symbol**: 股票代码
    - **signal_type**: 信号类型 (buy/sell/hold)
    - **source**: 信号来源
    - **confidence**: 置信度
    - **message**: 信号消息
    - **price_target**: 目标价
    - **stop_loss**: 止损价
    """
    generator = get_signal_generator()

    signal = generator.generate_signal(
        symbol=request.symbol,
        signal_type=request.signal_type,
        source=request.source,
        confidence=request.confidence,
        message=request.message,
        price_target=request.price_target,
        stop_loss=request.stop_loss
    )

    return {
        "signal": {
            "type": signal.signal_type,
            "symbol": signal.symbol,
            "confidence": signal.confidence,
            "message": signal.message,
            "price_target": signal.price_target,
            "stop_loss": signal.stop_loss,
            "timestamp": signal.timestamp
        }
    }


@app.get("/signals", summary="获取交易信号")
async def get_signals(
    symbol: Optional[str] = None,
    signal_type: Optional[str] = None,
    limit: int = 50
):
    """
    获取最近交易信号

    - **symbol**: 股票代码过滤
    - **signal_type**: 信号类型过滤
    - **limit**: 数量限制
    """
    generator = get_signal_generator()
    signals = generator.get_recent_signals(
        symbol=symbol,
        signal_type=signal_type,
        limit=limit
    )

    return {
        "signals": signals,
        "count": len(signals)
    }


@app.post("/notification", summary="发送通知")
async def send_notification(request: NotificationRequest):
    """
    发送通知

    - **notification_type**: 通知类型
    - **title**: 标题
    - **content**: 内容
    - **priority**: 优先级
    """
    manager = get_notification_manager()
    success = manager.send(
        notification_type=request.notification_type,
        title=request.title,
        content=request.content,
        priority=request.priority
    )

    return {
        "success": success
    }


@app.get("/notification/history", summary="获取通知历史")
async def get_notification_history(
    notification_type: Optional[str] = None,
    limit: int = 100
):
    """
    获取通知历史

    - **notification_type**: 通知类型过滤
    - **limit**: 数量限制
    """
    manager = get_notification_manager()
    history = manager.get_history(notification_type, limit)

    return {
        "history": history,
        "count": len(history)
    }


# ========== 启动服务 ==========

if __name__ == "__main__":
    import uvicorn

    logger.info("启动监控服务...")
    uvicorn.run(app, host="0.0.0.0", port=8005)
