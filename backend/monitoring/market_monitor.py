"""
市场监控模块

实时监控市场数据和交易信号
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import time

from backend.data_loader import get_data_loader
from backend.log import logger


class AlertType(Enum):
    """警报类型"""
    PRICE_SPIKE = "price_spike"
    VOLUME_SPIKE = "volume_spike"
    TECHNICAL_SIGNAL = "technical_signal"
    NEWS_EVENT = "news_event"
    CUSTOM = "custom"


@dataclass
class MarketAlert:
    """市场警报"""
    alert_type: str
    symbol: str
    message: str
    severity: str  # low/medium/high/critical
    timestamp: str
    data: Optional[Dict] = None


class MarketMonitor:
    """
    市场监控器

    实时监控市场数据并生成警报
    """

    def __init__(self, check_interval: int = 60):
        """
        初始化市场监控器

        Args:
            check_interval: 检查间隔（秒）
        """
        self.check_interval = check_interval
        self.data_loader = get_data_loader()
        self.alerts: List[MarketAlert] = []
        self.watchlist: List[str] = []
        self.alert_callbacks: List[Callable] = []

        self.price_spike_threshold = 0.05  # 5% 价格波动
        self.volume_spike_threshold = 2.0  # 2倍 成交量

        logger.info("市场监控器初始化完成")

    def add_to_watchlist(self, symbols: List[str]):
        """
        添加到观察列表

        Args:
            symbols: 股票代码列表
        """
        self.watchlist.extend(symbols)
        self.watchlist = list(set(self.watchlist))
        logger.info(f"观察列表已更新: {len(self.watchlist)} 只股票")

    def remove_from_watchlist(self, symbols: List[str]):
        """
        从观察列表移除

        Args:
            symbols: 股票代码列表
        """
        self.watchlist = [s for s in self.watchlist if s not in symbols]

    def check_price_spike(
        self,
        symbol: str,
        current_price: float,
        previous_price: float
    ) -> Optional[MarketAlert]:
        """
        检查价格异动

        Args:
            symbol: 股票代码
            current_price: 当前价格
            previous_price: 前期价格

        Returns:
            MarketAlert: 警报或 None
        """
        if previous_price == 0:
            return None

        change_pct = abs(current_price - previous_price) / previous_price

        if change_pct >= self.price_spike_threshold:
            return MarketAlert(
                alert_type=AlertType.PRICE_SPIKE.value,
                symbol=symbol,
                message=f"{symbol} 价格波动 {change_pct:.2%}",
                severity="high" if change_pct >= 0.1 else "medium",
                timestamp=datetime.now().isoformat(),
                data={
                    "current_price": current_price,
                    "previous_price": previous_price,
                    "change_pct": change_pct
                }
            )

        return None

    def check_volume_spike(
        self,
        symbol: str,
        current_volume: float,
        avg_volume: float
    ) -> Optional[MarketAlert]:
        """
        检查成交量异动

        Args:
            symbol: 股票代码
            current_volume: 当前成交量
            avg_volume: 平均成交量

        Returns:
            MarketAlert: 警报或 None
        """
        if avg_volume == 0:
            return None

        volume_ratio = current_volume / avg_volume

        if volume_ratio >= self.volume_spike_threshold:
            return MarketAlert(
                alert_type=AlertType.VOLUME_SPIKE.value,
                symbol=symbol,
                message=f"{symbol} 成交量放大 {volume_ratio:.1f} 倍",
                severity="medium",
                timestamp=datetime.now().isoformat(),
                data={
                    "current_volume": current_volume,
                    "avg_volume": avg_volume,
                    "volume_ratio": volume_ratio
                }
            )

        return None

    def check_technical_signal(
        self,
        symbol: str,
        signal_type: str,
        strength: float
    ) -> Optional[MarketAlert]:
        """
        检查技术信号

        Args:
            symbol: 股票代码
            signal_type: 信号类型
            strength: 信号强度

        Returns:
            MarketAlert: 警报或 None
        """
        if strength >= 0.7:  # 强信号
            return MarketAlert(
                alert_type=AlertType.TECHNICAL_SIGNAL.value,
                symbol=symbol,
                message=f"{symbol} {signal_type} 信号 (强度: {strength:.2f})",
                severity="high",
                timestamp=datetime.now().isoformat(),
                data={
                    "signal_type": signal_type,
                    "strength": strength
                }
            )

        return None

    def scan_market(self) -> List[MarketAlert]:
        """
        扫描市场

        Returns:
            List[MarketAlert]: 警报列表
        """
        new_alerts = []

        for symbol in self.watchlist:
            try:
                # 获取K线数据
                kline = self.data_loader.load_kline(symbol, "daily")

                if kline.empty:
                    continue

                # 检查价格异动
                current_price = kline.iloc[-1].get("close", 0)
                previous_price = kline.iloc[-2].get("close", 0) if len(kline) >= 2 else current_price

                alert = self.check_price_spike(symbol, current_price, previous_price)
                if alert:
                    new_alerts.append(alert)

                # 检查成交量异动
                current_volume = kline.iloc[-1].get("volume", 0)
                avg_volume = kline["volume"].tail(20).mean() if "volume" in kline.columns else 0

                alert = self.check_volume_spike(symbol, current_volume, avg_volume)
                if alert:
                    new_alerts.append(alert)

            except Exception as e:
                logger.warning(f"监控 {symbol} 失败: {e}")

        # 保存警报
        self.alerts.extend(new_alerts)

        # 触发回调
        for callback in self.alert_callbacks:
            try:
                callback(new_alerts)
            except Exception as e:
                logger.error(f"警报回调失败: {e}")

        logger.info(f"市场扫描完成，发现 {len(new_alerts)} 个警报")
        return new_alerts

    def register_alert_callback(self, callback: Callable):
        """
        注册警报回调

        Args:
            callback: 回调函数
        """
        self.alert_callbacks.append(callback)
        logger.info("警报回调已注册")

    def get_recent_alerts(
        self,
        alert_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        获取最近警报

        Args:
            alert_type: 警报类型
            limit: 数量限制

        Returns:
            List: 警报列表
        """
        alerts = self.alerts

        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]

        return [
            {
                "type": a.alert_type,
                "symbol": a.symbol,
                "message": a.message,
                "severity": a.severity,
                "timestamp": a.timestamp
            }
            for a in alerts[-limit:]
        ]

    def clear_old_alerts(self, hours: int = 24):
        """
        清除旧警报

        Args:
            hours: 保留小时数
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        self.alerts = [
            a for a in self.alerts
            if datetime.fromisoformat(a.timestamp) > cutoff
        ]
        logger.info(f"已清除旧警报，剩余 {len(self.alerts)} 个")


# 单例模式
_monitor: Optional[MarketMonitor] = None


def get_monitor() -> MarketMonitor:
    """获取市场监控器单例"""
    global _monitor
    if _monitor is None:
        _monitor = MarketMonitor()
    return _monitor
