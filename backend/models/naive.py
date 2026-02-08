"""
简单预测模型 - 使用最后一天收盘价作为预测值
"""

from datetime import datetime
from typing import Dict, Any

from backend.models.base import BasePredictionModel, PredictionResult
from backend.data_loader import get_data_loader


class NaiveLastClose(BasePredictionModel):
    """
    简单预测模型

    使用最后一天的收盘价作为下一天的预测值。
    这是最简单的预测方法，作为基准模型。
    """

    def __init__(self):
        """初始化简单预测模型"""
        super().__init__(name="naive_last_close")
        self.data_loader = None

    def predict(
        self,
        code: str,
        period: str = 'daily',
        **kwargs
    ) -> PredictionResult:
        """
        预测下一天的收盘价

        Args:
            code: 股票代码
            period: 预测周期 ('daily', '1d', '1m', '5m')
            **kwargs: 其他参数

        Returns:
            PredictionResult: 预测结果
        """
        # 验证输入
        if not self.validate_input(code, period):
            return PredictionResult(
                code=code,
                prediction=0.0,
                confidence=0.0,
                period=period,
                created_at=datetime.now().isoformat(),
                model=self.name,
                metadata={"error": "Invalid input parameters"}
            )

        # 初始化数据加载器
        if self.data_loader is None:
            self.data_loader = get_data_loader()

        try:
            # 获取 K 线数据
            kline_data = self.data_loader.load_kline(
                code=code,
                period=period
            )

            if kline_data.empty:
                return PredictionResult(
                    code=code,
                    prediction=0.0,
                    confidence=0.0,
                    period=period,
                    created_at=datetime.now().isoformat(),
                    model=self.name,
                    metadata={"error": "No data available"}
                )

            # 获取最后一天的收盘价
            close_col = None
            for col in ['close', '收盘价', 'Close']:
                if col in kline_data.columns:
                    close_col = col
                    break

            if close_col is None:
                return PredictionResult(
                    code=code,
                    prediction=0.0,
                    confidence=0.0,
                    period=period,
                    created_at=datetime.now().isoformat(),
                    model=self.name,
                    metadata={"error": "No close price column found"}
                )

            # 最后一天的收盘价作为预测值
            last_close = kline_data[close_col].iloc[-1]
            data_count = len(kline_data)

            return PredictionResult(
                code=code,
                prediction=float(last_close),
                confidence=0.5,  # 简单模型置信度较低
                period=period,
                created_at=datetime.now().isoformat(),
                model=self.name,
                metadata={
                    "data_count": data_count,
                    "last_date": str(kline_data['datetime'].iloc[-1]) if 'datetime' in kline_data.columns else None
                }
            )

        except Exception as e:
            return PredictionResult(
                code=code,
                prediction=0.0,
                confidence=0.0,
                period=period,
                created_at=datetime.now().isoformat(),
                model=self.name,
                metadata={"error": str(e)}
            )

    def train(self, **kwargs) -> bool:
        """
        简单模型不需要训练

        Args:
            **kwargs: 忽略

        Returns:
            bool: 始终返回 True
        """
        return True
