"""
通知模块

发送各类通知（邮件/飞书/短信）
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

from backend.log import logger


class NotificationType(Enum):
    """通知类型"""
    SIGNAL = "signal"
    ALERT = "alert"
    TRADING = "trading"
    SYSTEM = "system"
    REPORT = "report"


class NotificationPriority(Enum):
    """通知优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Notification:
    """通知"""
    notification_type: str
    title: str
    content: str
    priority: str = "normal"
    data: Optional[Dict] = None
    created_at: str = ""


class NotificationChannel(ABC):
    """通知通道基类"""

    @abstractmethod
    def send(self, notification: Notification) -> bool:
        """发送通知"""
        pass


class FeishuChannel(NotificationChannel):
    """飞书通知通道"""

    def __init__(self, target_user: str = ""):
        """
        初始化飞书通道

        Args:
            target_user: 目标用户ID
        """
        self.target_user = target_user
        logger.info("飞书通知通道初始化完成")

    def send(self, notification: Notification) -> bool:
        """
        发送飞书通知

        Args:
            notification: 通知

        Returns:
            bool: 是否成功
        """
        try:
            # 使用 OpenClaw 的 message 工具发送
            from tools import message

            message(
                action="send",
                channel="feishu",
                target=self.target_user,
                message=f"**{notification.title}**\n\n{notification.content}"
            )

            logger.info(f"飞书通知已发送: {notification.title}")
            return True

        except Exception as e:
            logger.error(f"飞书通知发送失败: {e}")
            return False


class ConsoleChannel(NotificationChannel):
    """控制台通知通道"""

    def send(self, notification: Notification) -> bool:
        """
        发送控制台通知

        Args:
            notification: 通知

        Returns:
            bool: 是否成功
        """
        print(f"[{notification.priority.upper()}] {notification.title}")
        print(notification.content)
        return True


class NotificationManager:
    """
    通知管理器

    统一管理各类通知
    """

    def __init__(self):
        """初始化通知管理器"""
        self.channels: List[NotificationChannel] = []
        self.notification_history: List[Notification] = []

        # 添加默认通道
        self.channels.append(ConsoleChannel())

        logger.info("通知管理器初始化完成")

    def add_channel(self, channel: NotificationChannel):
        """
        添加通知通道

        Args:
            channel: 通知通道
        """
        self.channels.append(channel)
        logger.info(f"通知通道已添加: {channel.__class__.__name__}")

    def send(
        self,
        notification_type: str,
        title: str,
        content: str,
        priority: str = "normal",
        data: Optional[Dict] = None
    ) -> bool:
        """
        发送通知

        Args:
            notification_type: 通知类型
            title: 标题
            content: 内容
            priority: 优先级
            data: 数据

        Returns:
            bool: 是否成功
        """
        notification = Notification(
            notification_type=notification_type,
            title=title,
            content=content,
            priority=priority,
            data=data,
            created_at=datetime.now().isoformat()
        )

        # 保存历史
        self.notification_history.append(notification)

        # 发送所有通道
        success = True
        for channel in self.channels:
            if not channel.send(notification):
                success = False

        logger.info(f"通知已发送: {title}")
        return success

    def send_trading_signal(
        self,
        symbol: str,
        signal_type: str,
        confidence: float,
        message: str,
        price_target: Optional[float] = None
    ):
        """
        发送交易信号通知

        Args:
            symbol: 股票代码
            signal_type: 信号类型
            confidence: 置信度
            message: 消息
            price_target: 目标价
        """
        priority = "high" if confidence > 0.8 else "normal"

        self.send(
            notification_type=NotificationType.SIGNAL.value,
            title=f"交易信号: {symbol} {signal_type.upper()}",
            content=f"{message}\n\n置信度: {confidence:.0%}" +
                    (f"\n目标价: {price_target}" if price_target else ""),
            priority=priority,
            data={
                "symbol": symbol,
                "signal_type": signal_type,
                "confidence": confidence,
                "price_target": price_target
            }
        )

    def send_alert(
        self,
        alert_type: str,
        symbol: str,
        message: str,
        severity: str = "medium"
    ):
        """
        发送警报通知

        Args:
            alert_type: 警报类型
            symbol: 股票代码
            message: 消息
            severity: 严重程度
        """
        priority_map = {
            "low": "normal",
            "medium": "normal",
            "high": "high",
            "critical": "urgent"
        }

        self.send(
            notification_type=NotificationType.ALERT.value,
            title=f"警报: {symbol} - {alert_type}",
            content=message,
            priority=priority_map.get(severity, "normal"),
            data={
                "alert_type": alert_type,
                "symbol": symbol,
                "severity": severity
            }
        )

    def get_history(
        self,
        notification_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        获取通知历史

        Args:
            notification_type: 通知类型
            limit: 数量限制

        Returns:
            List: 通知历史
        """
        history = self.notification_history

        if notification_type:
            history = [n for n in history if n.notification_type == notification_type]

        return [
            {
                "type": n.notification_type,
                "title": n.title,
                "content": n.content[:200],
                "priority": n.priority,
                "created_at": n.created_at
            }
            for n in history[-limit:]
        ]


# 单例模式
_notification_manager: Optional[NotificationManager] = None


def get_notification_manager() -> NotificationManager:
    """获取通知管理器单例"""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager
