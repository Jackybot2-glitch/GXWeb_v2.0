"""
交易信号模块

生成和分发交易信号
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from backend.log import logger


class SignalType(Enum):
    """信号类型"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"


class SignalSource(Enum):
    """信号来源"""
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    AI_MODEL = "ai_model"
    STRATEGY = "strategy"
    MANUAL = "manual"


@dataclass
class TradeSignal:
    """交易信号"""
    signal_type: str
    symbol: str
    source: str
    confidence: float
    message: str
    price_target: Optional[float] = None
    stop_loss: Optional[float] = None
    timestamp: str = ""
    metadata: Optional[Dict] = None


class SignalGenerator:
    """
    信号生成器

    从多种来源生成交易信号
    """

    def __init__(self):
        """初始化信号生成器"""
        self.signals: List[TradeSignal] = []
        self.signal_subscribers: List = []
        logger.info("信号生成器初始化完成")

    def generate_signal(
        self,
        symbol: str,
        signal_type: str,
        source: str,
        confidence: float,
        message: str,
        price_target: Optional[float] = None,
        stop_loss: Optional[float] = None,
        metadata: Optional[Dict] = None
    ) -> TradeSignal:
        """
        生成信号

        Args:
            symbol: 股票代码
            signal_type: 信号类型
            source: 信号来源
            confidence: 置信度
            message: 信号消息
            price_target: 目标价
            stop_loss: 止损价
            metadata: 元数据

        Returns:
            TradeSignal: 交易信号
        """
        signal = TradeSignal(
            signal_type=signal_type,
            symbol=symbol,
            source=source,
            confidence=confidence,
            message=message,
            price_target=price_target,
            stop_loss=stop_loss,
            timestamp=datetime.now().isoformat(),
            metadata=metadata
        )

        self.signals.append(signal)
        logger.info(f"生成信号: {symbol} {signal_type} ({confidence:.0%})")

        # 通知订阅者
        self._notify_subscribers(signal)

        return signal

    def subscribe(self, callback):
        """
        订阅信号

        Args:
            callback: 回调函数
        """
        self.signal_subscribers.append(callback)
        logger.info("信号订阅者已添加")

    def _notify_subscribers(self, signal: TradeSignal):
        """
        通知订阅者

        Args:
            signal: 交易信号
        """
        for callback in self.signal_subscribers:
            try:
                callback(signal)
            except Exception as e:
                logger.error(f"信号通知失败: {e}")

    def get_recent_signals(
        self,
        symbol: Optional[str] = None,
        signal_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        获取最近信号

        Args:
            symbol: 股票代码
            signal_type: 信号类型
            limit: 数量限制

        Returns:
            List: 信号列表
        """
        signals = self.signals

        if symbol:
            signals = [s for s in signals if s.symbol == symbol]

        if signal_type:
            signals = [s for s in signals if s.signal_type == signal_type]

        return [
            {
                "type": s.signal_type,
                "symbol": s.symbol,
                "source": s.source,
                "confidence": s.confidence,
                "message": s.message,
                "price_target": s.price_target,
                "stop_loss": s.stop_loss,
                "timestamp": s.timestamp
            }
            for s in signals[-limit:]
        ]


# 单例模式
_signal_generator: Optional[SignalGenerator] = None


def get_signal_generator() -> SignalGenerator:
    """获取信号生成器单例"""
    global _signal_generator
    if _signal_generator is None:
        _signal_generator = SignalGenerator()
    return _signal_generator
