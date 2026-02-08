"""
随机森林预测模型
"""

from datetime import datetime
from typing import Dict, Any, Optional
import numpy as np

from backend.models.base import BasePredictionModel, PredictionResult
from backend.data_loader import get_data_loader


class RandomForestModel(BasePredictionModel):
    """
    随机森林预测模型

    使用机器学习算法预测股票价格趋势。
    基于历史数据的特征工程进行预测。
    """

    def __init__(self, n_estimators: int = 100, lookback: int = 30):
        """
        初始化随机森林预测模型

        Args:
            n_estimators: 决策树数量（默认100）
            lookback: 回看天数（默认30天）
        """
        super().__init__(name="random_forest")
        self.n_estimators = n_estimators
        self.lookback = lookback
        self.model = None
        self.is_trained = False
        self.data_loader = None

        # 尝试导入 sklearn
        try:
            from sklearn.ensemble import RandomForestRegressor
            self._has_sklearn = True
        except ImportError:
            self._has_sklearn = False

    def _prepare_features(self, kline_data) -> Optional[np.ndarray]:
        """
        准备特征数据

        Args:
            kline_data: K线数据 DataFrame

        Returns:
            np.ndarray: 特征数组
        """
        if kline_data.empty or len(kline_data) < self.lookback + 5:
            return None

        # 获取需要的列
        close_col = None
        high_col = None
        low_col = None
        vol_col = None

        for col in kline_data.columns:
            col_lower = col.lower()
            if close_col is None and col_lower in ['close', '收盘价']:
                close_col = col
            elif high_col is None and col_lower in ['high', '最高价']:
                high_col = col
            elif low_col is None and col_lower in ['low', '最低价']:
                low_col = col
            elif vol_col is None and col_lower in ['volume', 'vol', '成交量']:
                vol_col = col

        if close_col is None:
            return None

        close = kline_data[close_col].values
        high = kline_data[high_col].values if high_col else close
        low = kline_data[low_col].values if low_col else close
        vol = kline_data[vol_col].values if vol_col else np.ones(len(close))

        # 准备特征
        features = []
        for i in range(self.lookback, len(close)):
            # 技术指标特征
            feat = [
                close[i] - close[i-1],  # 日收益率
                close[i] - close[i-self.lookback],  # 长期收益率
                (high[i] - low[i]) / close[i],  # 波动率
                vol[i] / np.mean(vol[i-self.lookback:i]) if np.mean(vol[i-self.lookback:i]) > 0 else 0,  # 成交量比率
                np.std(close[i-self.lookback:i]) if np.std(close[i-self.lookback:i]) > 0 else 0,  # 价格波动
            ]
            features.append(feat)

        return np.array(features)

    def _prepare_target(self, kline_data) -> Optional[np.ndarray]:
        """
        准备目标变量（下一天收益率）

        Args:
            kline_data: K线数据 DataFrame

        Returns:
            np.ndarray: 目标数组
        """
        if kline_data.empty or len(kline_data) < self.lookback + 5:
            return None

        close_col = None
        for col in kline_data.columns:
            if col.lower() in ['close', '收盘价']:
                close_col = col
                break

        if close_col is None:
            return None

        close = kline_data[close_col].values
        target = []

        for i in range(self.lookback, len(close) - 1):
            # 下一天收益率
            ret = (close[i+1] - close[i]) / close[i] if close[i] != 0 else 0
            target.append(ret)

        return np.array(target)

    def predict(
        self,
        code: str,
        period: str = 'daily',
        **kwargs
    ) -> PredictionResult:
        """
        预测下一天的价格趋势

        Args:
            code: 股票代码
            period: 预测周期 ('daily', '1d', '1m', '5m')
            **kwargs: 其他参数

        Returns:
            PredictionResult: 预测结果
        """
        # 检查 sklearn 是否可用
        if not self._has_sklearn:
            return PredictionResult(
                code=code,
                prediction=0.0,
                confidence=0.0,
                period=period,
                created_at=datetime.now().isoformat(),
                model=self.name,
                metadata={"error": "sklearn not installed"}
            )

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
                period=period,
                end_date=datetime.now().strftime('%Y-%m-%d')
            )

            if kline_data.empty or len(kline_data) < self.lookback + 5:
                return PredictionResult(
                    code=code,
                    prediction=0.0,
                    confidence=0.0,
                    period=period,
                    created_at=datetime.now().isoformat(),
                    model=self.name,
                    metadata={"error": "Insufficient data for prediction"}
                )

            # 获取特征和目标
            X = self._prepare_features(kline_data)
            y = self._prepare_target(kline_data)

            if X is None or y is None or len(X) == 0:
                return PredictionResult(
                    code=code,
                    prediction=0.0,
                    confidence=0.0,
                    period=period,
                    created_at=datetime.now().isoformat(),
                    model=self.name,
                    metadata={"error": "Failed to prepare features"}
                )

            # 获取最后一个特征向量（用于预测）
            last_features = X[-1].reshape(1, -1)

            # 如果模型未训练，先训练
            if not self.is_trained:
                self.train(X=X, y=y)

            if self.model is None:
                return PredictionResult(
                    code=code,
                    prediction=0.0,
                    confidence=0.0,
                    period=period,
                    created_at=datetime.now().isoformat(),
                    model=self.name,
                    metadata={"error": "Model training failed"}
                )

            # 预测
            prediction = self.model.predict(last_features)[0]

            # 获取最后收盘价
            close_col = None
            for col in kline_data.columns:
                if col.lower() in ['close', '收盘价']:
                    close_col = col
                    break

            last_close = kline_data[close_col].iloc[-1] if close_col else 0

            # 预测价格 = 最后收盘价 + 预测收益率 * 收盘价
            predicted_price = last_close * (1 + prediction)

            # 计算置信度（基于模型评分）
            try:
                score = self.model.score(X[:-1], y[:-1]) if self.is_trained else 0.5
                confidence = min(0.85, max(0.5, score))  # 限制在 0.5-0.85 之间
            except Exception:
                confidence = 0.5

            return PredictionResult(
                code=code,
                prediction=float(predicted_price),
                confidence=confidence,
                period=period,
                created_at=datetime.now().isoformat(),
                model=self.name,
                metadata={
                    "predicted_return": float(prediction),
                    "model_score": float(confidence),
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

    def train(self, X: Optional[np.ndarray] = None, y: Optional[np.ndarray] = None, **kwargs) -> bool:
        """
        训练随机森林模型

        Args:
            X: 特征数据（可选，如果未提供则使用缓存数据）
            y: 目标数据（可选）
            **kwargs: 其他参数

        Returns:
            bool: 是否训练成功
        """
        if not self._has_sklearn:
            return False

        try:
            from sklearn.ensemble import RandomForestRegressor

            if X is not None and y is not None and len(X) > 10:
                self.model = RandomForestRegressor(
                    n_estimators=self.n_estimators,
                    random_state=42,
                    n_jobs=-1
                )
                self.model.fit(X, y)
                self.is_trained = True
                return True
            else:
                return False

        except Exception as e:
            self.is_trained = False
            return False
