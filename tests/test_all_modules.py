"""
GX量化平台单元测试

覆盖所有核心模块
"""

import pytest
import os
import tempfile
from datetime import datetime

# 设置测试环境
os.environ["GX_DATA_PATH"] = "/Volumes/高速盘/QuantData/stock_daily/"


class TestModels:
    """预测模型测试"""

    def test_model_registry(self):
        """测试模型注册器"""
        from backend.models import ModelRegistry

        models = ModelRegistry.list_models()
        assert isinstance(models, list)
        assert "naive" in models
        assert "moving_average" in models
        assert "random_forest" in models

    def test_create_models(self):
        """测试创建模型"""
        from backend.models import ModelRegistry

        naive = ModelRegistry.create("naive")
        assert naive is not None
        assert naive.name == "naive_last_close"

        ma = ModelRegistry.create("moving_average", short_period=5, long_period=20)
        assert ma is not None
        assert ma.short_period == 5


class TestStockSelection:
    """选股模块测试"""

    def test_screening_import(self):
        """测试选股模块导入"""
        from backend.stock_selection import get_screening
        screening = get_screening()
        assert screening is not None

    def test_enhancement_import(self):
        """测试预测增强模块导入"""
        from backend.stock_selection import get_enhancement
        enhancement = get_enhancement()
        assert enhancement is not None

    def test_diagnosis_import(self):
        """测试诊断模块导入"""
        from backend.stock_selection import get_diagnosis
        diagnosis = get_diagnosis()
        assert diagnosis is not None


class TestStrategy:
    """策略模块测试"""

    def test_generator_import(self):
        """测试策略生成器导入"""
        from backend.strategy import get_strategy_generator
        generator = get_strategy_generator()
        assert generator is not None

    def test_backtest_import(self):
        """测试回测引擎导入"""
        from backend.strategy import BacktestEngine
        engine = BacktestEngine()
        assert engine is not None

    def test_optimizer_import(self):
        """测试优化器导入"""
        from backend.strategy import get_optimizer
        optimizer = get_optimizer()
        assert optimizer is not None

    def test_risk_controller_import(self):
        """测试风险控制器导入"""
        from backend.strategy import get_risk_controller
        controller = get_risk_controller()
        assert controller is not None

    def test_paper_trading_import(self):
        """测试模拟交易导入"""
        from backend.strategy import get_paper_trader
        trader = get_paper_trader()
        assert trader is not None


class TestMonitoring:
    """监控模块测试"""

    def test_monitor_import(self):
        """测试市场监控器导入"""
        from backend.monitoring import get_monitor
        monitor = get_monitor()
        assert monitor is not None

    def test_signal_generator_import(self):
        """测试信号生成器导入"""
        from backend.monitoring import get_signal_generator
        generator = get_signal_generator()
        assert generator is not None

    def test_notification_import(self):
        """测试通知管理器导入"""
        from backend.monitoring import get_notification_manager
        manager = get_notification_manager()
        assert manager is not None


class TestTasks:
    """任务模块测试"""

    def test_scheduler_import(self):
        """测试任务调度器导入"""
        from backend.tasks import get_scheduler
        scheduler = get_scheduler()
        assert scheduler is not None


class TestConfig:
    """配置测试"""

    def test_config_import(self):
        """测试配置导入"""
        from backend.config import config
        assert config is not None


class TestDataLoader:
    """数据加载测试"""

    def test_data_loader_import(self):
        """测试数据加载器导入"""
        from backend.data_loader import get_data_loader
        loader = get_data_loader()
        assert loader is not None


class TestAILient:
    """AI客户端测试"""

    def test_ai_import(self):
        """测试AI客户端导入"""
        from backend.ai_client import get_ai_manager
        manager = get_ai_manager()
        assert manager is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
