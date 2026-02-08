"""
预测模型基类模块
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PredictionResult:
    """
    预测结果数据类

    Attributes:
        code: 股票代码
        prediction: 预测值
        confidence: 置信度 (0-1)
        period: 预测周期
        created_at: 预测时间
        model: 模型名称
        metadata: 额外信息
    """
    code: str
    prediction: float
    confidence: float
    period: str
    created_at: str
    model: str
    metadata: Optional[Dict[str, Any]] = None


class BasePredictionModel(ABC):
    """
    预测模型基类

    所有预测模型必须继承此类并实现 predict 方法
    """

    def __init__(self, name: str = "base"):
        """
        初始化预测模型

        Args:
            name: 模型名称
        """
        self.name = name

    @abstractmethod
    def predict(
        self,
        code: str,
        period: str = 'daily',
        **kwargs
    ) -> PredictionResult:
        """
        执行预测

        Args:
            code: 股票代码
            period: 预测周期 ('daily', '1d', '1m', '5m')
            **kwargs: 其他参数

        Returns:
            PredictionResult: 预测结果
        """
        pass

    @abstractmethod
    def train(self, **kwargs) -> bool:
        """
        训练模型（如果需要）

        Args:
            **kwargs: 训练参数

        Returns:
            bool: 是否训练成功
        """
        pass

    def validate_input(self, code: str, period: str) -> bool:
        """
        验证输入参数

        Args:
            code: 股票代码
            period: 预测周期

        Returns:
            bool: 参数是否有效
        """
        if not code:
            return False
        if period not in ['daily', '1d', '1m', '5m']:
            return False
        return True

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            Dict: 模型信息字典
        """
        return {
            "name": self.name,
            "type": self.__class__.__name__
        }
