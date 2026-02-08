"""
预测模型模块

提供各种股票预测模型：
- naive: 简单预测模型（基准）
- moving_average: 移动平均预测模型
- random_forest: 随机森林预测模型（需要 sklearn）
"""

from typing import Dict, Type, Any, List

from backend.models.base import BasePredictionModel, PredictionResult
from backend.models.naive import NaiveLastClose
from backend.models.moving_average import MovingAverage

# 尝试导入随机森林模型
try:
    from backend.models.random_forest import RandomForestModel
    _HAS_RF = True
except Exception:
    RandomForestModel = None
    _HAS_RF = False


class ModelRegistry:
    """
    模型注册表

    管理所有可用的预测模型
    """

    _models: Dict[str, Type[BasePredictionModel]] = {}

    @classmethod
    def register_defaults(cls):
        """
        注册默认模型
        """
        cls._models = {
            'naive': NaiveLastClose,
            'moving_average': MovingAverage,
        }
        if _HAS_RF and RandomForestModel is not None:
            cls._models['random_forest'] = RandomForestModel

    @classmethod
    def list_models(cls) -> List[str]:
        """
        列出所有可用的模型

        Returns:
            List[str]: 模型名称列表
        """
        if not cls._models:
            cls.register_defaults()
        return list(cls._models.keys())

    @classmethod
    def create(cls, name: str, **kwargs) -> BasePredictionModel:
        """
        创建模型实例

        Args:
            name: 模型名称
            **kwargs: 模型参数

        Returns:
            BasePredictionModel: 模型实例

        Raises:
            ValueError: 如果模型不存在
        """
        if not cls._models:
            cls.register_defaults()

        name = (name or 'naive').lower()

        if name not in cls._models:
            available = ', '.join(cls._models.keys())
            raise ValueError(f"未知模型: {name}。可用模型: {available}")

        return cls._models[name](**kwargs)

    @classmethod
    def get_model_info(cls, name: str) -> Dict[str, Any]:
        """
        获取模型信息

        Args:
            name: 模型名称

        Returns:
            Dict: 模型信息
        """
        model = cls.create(name)
        return model.get_model_info()


# 默认注册模型
ModelRegistry.register_defaults()
