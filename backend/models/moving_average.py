"""
移动平均预测模型
"""

from datetime import datetime
from typing import Dict, Any

from backend.models.base import BasePredictionModel, PredictionResult
from backend.data_loader import get_data_loader


class MovingAverage(BasePredictionModel):
    """
    移动平均预测模型

    使用移动平均线的斜率预测未来价格趋势。
    """

    def __init__(self, short_period: int = 5, long_period: int = 20):
        """
        初始化移动平均预测模型

        Args:
            short_period: 短期均线周期（默认5天）
            long_period: 长期均线周期（默认20天）
        """
        super().__init__(name="moving_average")
        self.short_period = short_period
        self.long_period = long_period
        self.data_loader = None

    def predict(
        self,
        code: str,
        period: str = 'daily',
        **kwargs
    ) -> PredictionResult:
        """
        基于移动平均预测价格趋势

        Args:
            code: 股票代码
            period: 预测周期 ('daily', '1d', '1m', '5m')
            short_period: 短期均线周期（可选）
            long_period: 长期均线周期（可选）
            **kwargs: 其他参数

        Returns:
            PredictionResult: 预测结果
        """
        # 获取参数
        short_period = kwargs.get('short_period', self.short_period)
        long_period = kwargs.get('long_period', self.long_period)

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
            # 获取 K 线数据（需要足够的历史数据）
            lookback = max(short_period, long_period) + 10
            kline_data = self.data_loader.load_kline(
                code=code,
                period=period,
                end_date=datetime.now().strftime('%Y-%m-%d')
            )

            if kline_data.empty or len(kline_data) < lookback:
                return PredictionResult(
                    code=code,
                    prediction=0.0,
                    confidence=0.0,
                    period=period,
                    created_at=datetime.now().isoformat(),
                    model=self.name,
                    metadata={"error": "Insufficient data for moving average"}
                )

            # 获取收盘价
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

            close_prices = kline_data[close_col].values

            # 计算移动平均
            import numpy as np
            short_ma = np.mean(close_prices[-short_period:])
            long_ma = np.mean(close_prices[-long_period:])

            # 计算斜率（基于最近几天的趋势）
            recent_prices = close_prices[-10:] if len(close_prices) >= 10 else close_prices
            if len(recent_prices) >= 2:
                slope = (recent_prices[-1] - recent_prices[0]) / len(recent_prices)
            else:
                slope = 0

            # 预测值 = 最后收盘价 + 趋势斜率
            last_close = close_prices[-1]
            prediction = last_close + slope

            # 计算置信度（基于均线金叉/死叉状态）
            if short_ma > long_ma:
                confidence = 0.65  # 金叉，趋势向上
            elif short_ma < long_ma:
                confidence = 0.60  # 死叉，趋势向下
            else:
                confidence = 0.50  # 持平

            return PredictionResult(
                code=code,
                prediction=float(prediction),
                confidence=confidence,
                period=period,
                created_at=datetime.now().isoformat(),
                model=self.name,
                metadata={
                    "short_ma": float(short_ma),
                    "long_ma": float(long_ma),
                    "slope": float(slope),
                    "data_count": len(kline_data)
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
        移动平均模型不需要训练

        Args:
            **kwargs: 忽略

        Returns:
            bool: 始终返回 True
        """
        return True
