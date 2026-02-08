"""
股票推荐模块 - M2.1 预测增强

使用预测模型生成选股因子
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from backend.models import ModelRegistry
from backend.data_loader import get_data_loader
from backend.log import logger


class PredictionEnhancement:
    """
    预测增强模块

    利用 Phase 2 的预测模型为选股生成增强因子
    """

    def __init__(self):
        """初始化预测增强模块"""
        self.data_loader = get_data_loader()
        self.models = {}
        logger.info("预测增强模块初始化完成")

    def _get_model(self, model_name: str):
        """获取或创建模型"""
        if model_name not in self.models:
            self.models[model_name] = ModelRegistry.create(model_name)
        return self.models[model_name]

    def generate_prediction_factors(
        self,
        stocks: List[str],
        model: str = "naive",
        period: str = "daily"
    ) -> Dict[str, Dict[str, Any]]:
        """
        生成预测因子

        Args:
            stocks: 股票代码列表
            model: 预测模型
            period: 预测周期

        Returns:
            Dict[股票代码, 预测因子]
        """
        prediction_model = self._get_model(model)
        factors = {}

        for stock in stocks:
            try:
                result = prediction_model.predict(stock, period)

                factors[stock] = {
                    "prediction": result.prediction,
                    "confidence": result.confidence,
                    "model": result.model,
                    "created_at": result.created_at,
                    # 额外因子
                    "trend": self._calculate_trend(result),
                    "volatility": result.metadata.get("volatility", 0) if result.metadata else 0
                }

            except Exception as e:
                logger.warning(f"生成预测因子失败: {stock} - {e}")
                factors[stock] = {
                    "prediction": 0,
                    "confidence": 0,
                    "model": model,
                    "error": str(e)
                }

        logger.info(f"生成 {len(factors)} 只股票的预测因子")
        return factors

    def _calculate_trend(self, result) -> str:
        """
        计算趋势

        Args:
            result: 预测结果

        Returns:
            str: 趋势 (up/down/neutral)
        """
        if not result.metadata:
            return "neutral"

        short_ma = result.metadata.get("short_ma", 0)
        long_ma = result.metadata.get("long_ma", 0)

        if short_ma > long_ma:
            return "up"
        elif short_ma < long_ma:
            return "down"
        else:
            return "neutral"

    def enhance_screening(
        self,
        stocks: List[str],
        model: str = "moving_average",
        period: str = "daily",
        min_confidence: float = 0.5
    ) -> List[str]:
        """
        增强筛选

        使用预测因子增强选股

        Args:
            stocks: 股票代码列表
            model: 预测模型
            period: 预测周期
            min_confidence: 最低置信度

        Returns:
            List[str]: 增强后的股票列表
        """
        # 生成预测因子
        factors = self.generate_prediction_factors(stocks, model, period)

        # 根据预测因子筛选
        enhanced = [
            stock for stock, data in factors.items()
            if data.get("confidence", 0) >= min_confidence
            and data.get("trend") == "up"
        ]

        logger.info(f"增强筛选: {len(stocks)} -> {len(enhanced)} 只股票")
        return enhanced

    def get_prediction_report(
        self,
        stocks: List[str],
        model: str = "naive",
        period: str = "daily"
    ) -> Dict[str, Any]:
        """
        获取预测报告

        Args:
            stocks: 股票代码列表
            model: 预测模型
            period: 预测周期

        Returns:
            Dict: 预测报告
        """
        factors = self.generate_prediction_factors(stocks, model, period)

        # 统计
        total = len(factors)
        up_count = sum(1 for f in factors.values() if f.get("trend") == "up")
        down_count = sum(1 for f in factors.values() if f.get("trend") == "down")
        avg_confidence = sum(f.get("confidence", 0) for f in factors.values()) / total if total > 0 else 0

        return {
            "total_stocks": total,
            "up_count": up_count,
            "down_count": down_count,
            "neutral_count": total - up_count - down_count,
            "avg_confidence": avg_confidence,
            "factors": factors,
            "model": model,
            "period": period,
            "created_at": datetime.now().isoformat()
        }


# 单例模式
_enhancement: Optional[PredictionEnhancement] = None


def get_enhancement() -> PredictionEnhancement:
    """获取预测增强模块单例"""
    global _enhancement
    if _enhancement is None:
        _enhancement = PredictionEnhancement()
    return _enhancement
