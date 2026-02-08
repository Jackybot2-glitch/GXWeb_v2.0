"""
预测模块测试用例
"""

import pytest
import os
import tempfile
from datetime import datetime

from backend.models import ModelRegistry, PredictionResult
from backend.prediction.storage import PredictionStorage


class TestPredictionModels:
    """预测模型测试类"""

    def test_list_models(self):
        """测试列出可用模型"""
        models = ModelRegistry.list_models()
        assert isinstance(models, list)
        assert "naive" in models
        assert "moving_average" in models
        assert "random_forest" in models

    def test_create_naive_model(self):
        """测试创建简单预测模型"""
        model = ModelRegistry.create("naive")
        assert model is not None
        assert model.name == "naive_last_close"

    def test_create_ma_model(self):
        """测试创建移动平均模型"""
        model = ModelRegistry.create("moving_average", short_period=5, long_period=20)
        assert model is not None
        assert model.short_period == 5
        assert model.long_period == 20

    def test_create_unknown_model(self):
        """测试创建未知模型"""
        with pytest.raises(ValueError):
            ModelRegistry.create("unknown_model")

    def test_naive_prediction(self):
        """测试简单预测模型"""
        model = ModelRegistry.create("naive")
        result = model.predict("SH600000", "daily")

        assert result is not None
        assert result.code == "SH600000"
        assert result.model == "naive_last_close"
        assert isinstance(result.prediction, float)
        assert result.period == "daily"

    def test_ma_prediction(self):
        """测试移动平均预测模型"""
        model = ModelRegistry.create("moving_average", short_period=5, long_period=20)
        result = model.predict("SH600000", "daily")

        assert result is not None
        assert result.code == "SH600000"
        assert result.model == "moving_average"
        assert isinstance(result.prediction, float)

    def test_prediction_result_dataclass(self):
        """测试预测结果数据类"""
        result = PredictionResult(
            code="SH600000",
            prediction=10.5,
            confidence=0.75,
            period="daily",
            created_at=datetime.now().isoformat(),
            model="test",
            metadata={"test": "data"}
        )

        assert result.code == "SH600000"
        assert result.prediction == 10.5
        assert result.confidence == 0.75
        assert result.metadata["test"] == "data"

    def test_get_model_info(self):
        """测试获取模型信息"""
        info = ModelRegistry.get_model_info("naive")
        assert info is not None
        assert "name" in info
        assert "type" in info


class TestPredictionStorage:
    """预测存储测试类"""

    @pytest.fixture
    def temp_storage(self):
        """创建临时存储目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = PredictionStorage(storage_dir=tmpdir)
            yield storage

    def test_save_and_get_result(self, temp_storage):
        """测试保存和获取预测结果"""
        # 创建预测结果
        result = PredictionResult(
            code="SH600000",
            prediction=10.5,
            confidence=0.75,
            period="daily",
            created_at=datetime.now().isoformat(),
            model="naive",
            metadata={"test": "value"}
        )

        # 保存结果
        task_id = temp_storage.save_result("SH600000", "naive", result)
        assert task_id is not None
        assert "SH600000_naive_" in task_id

        # 获取结果
        saved_result = temp_storage.get_result(task_id)
        assert saved_result is not None
        assert saved_result["code"] == "SH600000"
        assert saved_result["prediction"] == 10.5

    def test_get_latest_result(self, temp_storage):
        """测试获取最新预测结果"""
        # 创建并保存多个预测结果
        for i in range(3):
            result = PredictionResult(
                code="SH600000",
                prediction=10.0 + i,
                confidence=0.5,
                period="daily",
                created_at=datetime.now().isoformat(),
                model="naive",
                metadata={}
            )
            temp_storage.save_result("SH600000", "naive", result)

        # 获取最新结果
        latest = temp_storage.get_latest_result("SH600000")
        assert latest is not None
        assert latest["prediction"] == 12.0

    def test_list_predictions(self, temp_storage):
        """测试列出预测结果"""
        # 保存预测结果
        for code in ["SH600000", "SH600001"]:
            for i in range(2):
                result = PredictionResult(
                    code=code,
                    prediction=10.0,
                    confidence=0.5,
                    period="daily",
                    created_at=datetime.now().isoformat(),
                    model="naive",
                    metadata={}
                )
                temp_storage.save_result(code, "naive", result)

        # 列出所有预测
        all_preds = temp_storage.list_predictions(limit=10)
        assert len(all_preds) >= 2

        # 按股票筛选
        sh600000_preds = temp_storage.list_predictions(code="SH600000", limit=10)
        assert len(sh600000_preds) >= 2

    def test_get_statistics(self, temp_storage):
        """测试获取统计信息"""
        # 保存一些预测结果
        for code in ["SH600000", "SH600001"]:
            result = PredictionResult(
                code=code,
                prediction=10.0,
                confidence=0.5,
                period="daily",
                created_at=datetime.now().isoformat(),
                model="naive",
                metadata={}
            )
            temp_storage.save_result(code, "naive", result)

        stats = temp_storage.get_statistics()
        assert stats is not None
        assert "total_predictions" in stats
        assert "unique_stocks" in stats

    def test_get_nonexistent_result(self, temp_storage):
        """测试获取不存在的预测结果"""
        result = temp_storage.get_result("nonexistent_task_id")
        assert result is None


class TestDataLoader:
    """数据加载器测试类"""

    def test_load_kline_data(self):
        """测试加载K线数据"""
        from backend.data_loader import get_data_loader

        loader = get_data_loader()
        kline = loader.load_kline("SH600000", "daily")

        # 浦发银行应该有数据
        assert kline is not None
        assert len(kline) > 0
        assert "close" in kline.columns or "close" in [c.lower() for c in kline.columns]

    def test_load_stock_basic(self):
        """测试加载股票基本信息"""
        from backend.data_loader import get_data_loader

        loader = get_data_loader()
        basic = loader.load_stock_basic()

        assert basic is not None
        assert len(basic) > 0

    def test_get_industry_list(self):
        """测试获取行业列表"""
        from backend.data_loader import get_data_loader

        loader = get_data_loader()
        industries = loader.get_industry_list()

        assert industries is not None
        assert len(industries) > 0
