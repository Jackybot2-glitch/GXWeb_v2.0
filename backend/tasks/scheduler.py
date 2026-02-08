"""
定时任务模块

管理定时执行的任务
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import schedule
import time
import threading

from backend.log import logger


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ScheduledTask:
    """定时任务"""
    task_id: str
    name: str
    func: Callable
    interval: int  # 秒
    last_run: Optional[str] = None
    status: str = "pending"
    result: Optional[Dict] = None


class TaskScheduler:
    """
    任务调度器

    管理定时执行的任务
    """

    def __init__(self):
        """初始化调度器"""
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self.thread: Optional[threading.Thread] = None

        logger.info("任务调度器初始化完成")

    def add_task(
        self,
        task_id: str,
        name: str,
        func: Callable,
        interval: int = 3600
    ):
        """
        添加任务

        Args:
            task_id: 任务ID
            name: 任务名称
            func: 执行函数
            interval: 执行间隔（秒）
        """
        self.tasks[task_id] = ScheduledTask(
            task_id=task_id,
            name=name,
            func=func,
            interval=interval
        )
        logger.info(f"任务已添加: {name} ({interval}秒)")

    def remove_task(self, task_id: str):
        """
        移除任务

        Args:
            task_id: 任务ID
        """
        if task_id in self.tasks:
            del self.tasks[task_id]
            logger.info(f"任务已移除: {task_id}")

    def run_task(self, task_id: str) -> Dict:
        """
        手动执行任务

        Args:
            task_id: 任务ID

        Returns:
            Dict: 执行结果
        """
        if task_id not in self.tasks:
            return {"error": f"任务不存在: {task_id}"}

        task = self.tasks[task_id]
        task.status = "running"
        task.last_run = datetime.now().isoformat()

        try:
            result = task.func()
            task.result = result
            task.status = "completed"
            logger.info(f"任务执行成功: {task.name}")
            return {"status": "completed", "result": result}

        except Exception as e:
            task.status = "failed"
            task.result = {"error": str(e)}
            logger.error(f"任务执行失败: {task.name} - {e}")
            return {"status": "failed", "error": str(e)}

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            Dict: 任务状态
        """
        if task_id not in self.tasks:
            return None

        task = self.tasks[task_id]
        return {
            "task_id": task.task_id,
            "name": task.name,
            "interval": task.interval,
            "last_run": task.last_run,
            "status": task.status
        }

    def list_tasks(self) -> List[Dict]:
        """
        列出所有任务

        Returns:
            List: 任务列表
        """
        return [
            {
                "task_id": task.task_id,
                "name": task.name,
                "interval": task.interval,
                "last_run": task.last_run,
                "status": task.status
            }
            for task in self.tasks.values()
        ]

    def start(self):
        """启动调度器"""
        self.running = True
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.start()
        logger.info("任务调度器已启动")

    def stop(self):
        """停止调度器"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("任务调度器已停止")

    def _run_loop(self):
        """运行循环"""
        while self.running:
            time.sleep(1)


# 单例模式
_scheduler: Optional[TaskScheduler] = None


def get_scheduler() -> TaskScheduler:
    """获取调度器单例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = TaskScheduler()
    return _scheduler
