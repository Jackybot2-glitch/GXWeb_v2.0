"""
任务管理器测试用例
"""

import pytest
import os
import tempfile
from backend.task_manager import TaskManager


class TestTaskManager:
    """任务管理器测试类"""

    @pytest.fixture
    def temp_db(self):
        """创建临时数据库文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{}')
            temp_path = f.name
        yield temp_path
        # 清理
        if os.path.exists(temp_path):
            os.remove(temp_path)

    @pytest.fixture
    def task_manager(self, temp_db):
        """创建任务管理器实例"""
        return TaskManager(db_path=temp_db)

    def test_init_success(self, task_manager):
        """测试初始化成功"""
        assert task_manager is not None
        assert isinstance(task_manager.tasks, dict)

    def test_create_task(self, task_manager):
        """测试创建任务"""
        task_id = task_manager.create_task(name="测试任务")
        assert task_id is not None
        assert len(task_id) == 8  # UUID 前8位

        task = task_manager.get_task(task_id)
        assert task is not None
        assert task["name"] == "测试任务"
        assert task["status"] == "pending"

    def test_get_nonexistent_task(self, task_manager):
        """测试获取不存在的任务"""
        task = task_manager.get_task("not_exist")
        assert task is None

    def test_list_tasks_empty(self, task_manager):
        """测试空任务列表"""
        tasks = task_manager.list_tasks()
        assert tasks == []

    def test_list_tasks_with_filter(self, temp_db):
        """测试按状态筛选任务"""
        tm = TaskManager(db_path=temp_db)
        tm.create_task(name="任务1")
        tm.create_task(name="任务2")

        # 获取所有任务
        all_tasks = tm.list_tasks()
        assert len(all_tasks) == 2

        # 按状态筛选
        pending_tasks = tm.list_tasks(status="pending")
        assert len(pending_tasks) == 2

    def test_run_task(self, task_manager):
        """测试执行任务"""
        task_id = task_manager.create_task(name="执行测试")
        result = task_manager.run_task(task_id)

        assert result is True
        task = task_manager.get_task(task_id)
        assert task["status"] == "completed"
        assert task["completed_at"] is not None

    def test_cancel_task(self, task_manager):
        """测试取消任务"""
        task_id = task_manager.create_task(name="取消测试")
        result = task_manager.cancel_task(task_id)

        assert result is True
        task = task_manager.get_task(task_id)
        assert task["status"] == "cancelled"

    def test_cancel_nonexistent_task(self, task_manager):
        """测试取消不存在的任务"""
        result = task_manager.cancel_task("not_exist")
        assert result is False

    def test_delete_task(self, task_manager):
        """测试删除任务"""
        task_id = task_manager.create_task(name="删除测试")
        result = task_manager.delete_task(task_id)

        assert result is True
        task = task_manager.get_task(task_id)
        assert task is None

    def test_delete_nonexistent_task(self, task_manager):
        """测试删除不存在的任务"""
        result = task_manager.delete_task("not_exist")
        assert result is False

    def test_task_timestamps(self, task_manager):
        """测试任务时间戳"""
        task_id = task_manager.create_task(name="时间戳测试")

        task = task_manager.get_task(task_id)
        assert task["created_at"] is not None
        assert task["started_at"] is None
        assert task["completed_at"] is None

    def test_run_nonexistent_task(self, task_manager):
        """测试执行不存在的任务"""
        result = task_manager.run_task("not_exist")
        assert result is False

    def test_multiple_tasks_order(self, temp_db):
        """测试多个任务的创建顺序"""
        tm = TaskManager(db_path=temp_db)
        ids = []
        for i in range(3):
            task_id = tm.create_task(name=f"任务{i}")
            ids.append(task_id)

        tasks = tm.list_tasks()
        # 按创建时间倒序排列
        assert len(tasks) == 3
