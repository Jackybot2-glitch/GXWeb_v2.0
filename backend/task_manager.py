"""
任务管理器模块 - 管理异步任务的创建、执行和追踪
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any

from backend.log import logger

# 默认任务存储文件
DEFAULT_TASKS_FILE = "data/tasks.json"


class TaskManager:
    """
    任务管理器 - 提供任务的创建、执行、查询和状态管理功能

    Attributes:
        db_path: 任务数据存储文件路径
        tasks: 任务字典
    """

    def __init__(self, db_path: str = DEFAULT_TASKS_FILE):
        """
        初始化任务管理器

        Args:
            db_path: 任务数据存储文件路径
        """
        self.db_path = db_path
        self.tasks: Dict[str, Dict] = self._load_tasks()
        logger.info(f"任务管理器初始化完成，共 {len(self.tasks)} 个任务")

    def _load_tasks(self) -> Dict[str, Dict]:
        """
        从文件加载任务数据

        Returns:
            任务字典
        """
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            logger.warning(f"任务文件格式错误: {self.db_path}")
            return {}

    def _save_tasks(self):
        """保存任务数据到文件"""
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存任务失败: {e}")

    def create_task(
        self,
        name: str,
        func: Optional[Callable] = None,
        **kwargs: Any
    ) -> str:
        """
        创建新任务

        Args:
            name: 任务名称
            func: 可选的任务函数
            **kwargs: 任务参数

        Returns:
            任务ID
        """
        task_id = str(uuid.uuid4())[:8]
        self.tasks[task_id] = {
            "id": task_id,
            "name": name,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error": None,
            "kwargs": kwargs
        }
        self._save_tasks()
        logger.info(f"创建任务: {name} ({task_id})")
        return task_id

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务信息

        Args:
            task_id: 任务ID

        Returns:
            任务信息字典，不存在返回None
        """
        return self.tasks.get(task_id)

    def list_tasks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出任务

        Args:
            status: 可选的状态过滤

        Returns:
            任务列表
        """
        tasks = list(self.tasks.values())
        if status:
            tasks = [t for t in tasks if t["status"] == status]
        return sorted(tasks, key=lambda x: x["created_at"], reverse=True)

    def run_task(self, task_id: str) -> bool:
        """
        执行任务

        Args:
            task_id: 任务ID

        Returns:
            是否执行成功
        """
        task = self.get_task(task_id)
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return False

        if task["status"] not in ["pending", "failed"]:
            logger.warning(f"任务状态不允许执行: {task['status']}")
            return False

        task["status"] = "running"
        task["started_at"] = datetime.now().isoformat()
        self._save_tasks()

        try:
            logger.info(f"开始执行任务: {task['name']}")
            # 这里可以执行实际的任务逻辑
            # 目前仅模拟
            task["status"] = "completed"
            task["completed_at"] = datetime.now().isoformat()
            task["result"] = {"message": "任务执行完成"}
            self._save_tasks()
            logger.info(f"任务完成: {task['name']}")
            return True
        except Exception as e:
            task["status"] = "failed"
            task["error"] = str(e)
            self._save_tasks()
            logger.error(f"任务失败: {task['name']} - {e}")
            return False

    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否取消成功
        """
        task = self.get_task(task_id)
        if not task:
            return False

        if task["status"] not in ["pending", "running"]:
            return False

        task["status"] = "cancelled"
        task["completed_at"] = datetime.now().isoformat()
        self._save_tasks()
        logger.info(f"任务已取消: {task['name']}")
        return True

    def delete_task(self, task_id: str) -> bool:
        """
        删除任务

        Args:
            task_id: 任务ID

        Returns:
            是否删除成功
        """
        if task_id in self.tasks:
            del self.tasks[task_id]
            self._save_tasks()
            logger.info(f"删除任务: {task_id}")
            return True
        return False


# 单例模式
_task_manager: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    """
    获取任务管理器单例

    Returns:
        TaskManager实例
    """
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager
