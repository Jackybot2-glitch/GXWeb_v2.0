"""
定时任务模块初始化
"""

from backend.tasks.scheduler import TaskScheduler, get_scheduler
from backend.tasks.preset_tasks import (
    daily_market_summary,
    daily_prediction_report,
    weekly_strategy_review,
    market_open_alert,
    market_close_alert,
    setup_daily_tasks,
    setup_weekly_tasks
)

__all__ = [
    "TaskScheduler",
    "get_scheduler",
    "daily_market_summary",
    "daily_prediction_report",
    "weekly_strategy_review",
    "market_open_alert",
    "market_close_alert",
    "setup_daily_tasks",
    "setup_weekly_tasks"
]
