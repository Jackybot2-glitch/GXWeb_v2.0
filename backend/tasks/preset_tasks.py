"""
预定义定时任务

提供常用的定时任务函数
"""

from typing import Dict, Any
from datetime import datetime

from backend.log import logger
from backend.monitoring.notification import get_notification_manager


def daily_market_summary() -> Dict[str, Any]:
    """
    每日市场总结

    Returns:
        Dict: 总结结果
    """
    logger.info("执行每日市场总结...")

    return {
        "task": "daily_market_summary",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "summary": "今日市场总结",
        "created_at": datetime.now().isoformat()
    }


def daily_prediction_report() -> Dict[str, Any]:
    """
    每日预测报告

    Returns:
        Dict: 报告结果
    """
    logger.info("生成每日预测报告...")

    return {
        "task": "daily_prediction_report",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "predictions": [],
        "created_at": datetime.now().isoformat()
    }


def weekly_strategy_review() -> Dict[str, Any]:
    """
    每周策略回顾

    Returns:
        Dict: 回顾结果
    """
    logger.info("执行每周策略回顾...")

    return {
        "task": "weekly_strategy_review",
        "week": datetime.now().isocalendar()[1],
        "review": "策略回顾报告",
        "created_at": datetime.now().isoformat()
    }


def market_open_alert() -> Dict[str, Any]:
    """
    开市警报

    Returns:
        Dict: 警报结果
    """
    logger.info("发送开市警报...")

    # 发送通知
    manager = get_notification_manager()
    manager.send(
        notification_type="trading",
        title="📈 市场开市提醒",
        content="A股市场已开市，开始今日交易",
        priority="normal"
    )

    return {
        "task": "market_open_alert",
        "time": datetime.now().isoformat(),
        "sent": True
    }


def market_close_alert() -> Dict[str, Any]:
    """
    收市警报

    Returns:
        Dict: 警报结果
    """
    logger.info("发送收市警报...")

    # 发送通知
    manager = get_notification_manager()
    manager.send(
        notification_type="trading",
        title="📉 市场收市提醒",
        content="A股市场已收市，今日交易结束",
        priority="normal"
    )

    return {
        "task": "market_close_alert",
        "time": datetime.now().isoformat(),
        "sent": True
    }


def setup_daily_tasks(scheduler):
    """
    设置每日任务

    Args:
        scheduler: 任务调度器
    """
    # 每日市场总结 (18:00)
    scheduler.add_task(
        task_id="daily_summary",
        name="每日市场总结",
        func=daily_market_summary,
        interval=86400  # 24小时
    )

    # 每日预测报告 (20:00)
    scheduler.add_task(
        task_id="daily_prediction",
        name="每日预测报告",
        func=daily_prediction_report,
        interval=86400
    )

    # 开市警报 (9:15)
    scheduler.add_task(
        task_id="market_open",
        name="开市警报",
        func=market_open_alert,
        interval=86400
    )

    # 收市警报 (15:00)
    scheduler.add_task(
        task_id="market_close",
        name="收市警报",
        func=market_close_alert,
        interval=86400
    )

    logger.info("每日任务设置完成")


def setup_weekly_tasks(scheduler):
    """
    设置每周任务

    Args:
        scheduler: 任务调度器
    """
    # 每周策略回顾 (周日 20:00)
    scheduler.add_task(
        task_id="weekly_review",
        name="每周策略回顾",
        func=weekly_strategy_review,
        interval=604800  # 7天
    )

    logger.info("每周任务设置完成")
