"""
参数优化模块

网格搜索和参数调优
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from itertools import product

from backend.strategy.backtest import BacktestEngine
from backend.log import logger


class ParameterOptimizer:
    """
    参数优化器

    使用网格搜索优化策略参数
    """

    def __init__(self):
        """初始化优化器"""
        logger.info("参数优化器初始化完成")

    def grid_search(
        self,
        strategy: Dict[str, Any],
        price_data: List[Dict[str, Any]],
        param_grid: Dict[str, List],
        symbol: str = "SH600000"
    ) -> Dict[str, Any]:
        """
        网格搜索

        Args:
            strategy: 策略基础配置
            price_data: 价格数据
            param_grid: 参数网格
            symbol: 股票代码

        Returns:
            Dict: 优化结果
        """
        # 生成参数组合
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        combinations = list(product(*param_values))

        logger.info(f"开始网格搜索，共 {len(combinations)} 种参数组合")

        results = []

        for i, combo in enumerate(combinations):
            # 构建参数
            params = dict(zip(param_names, combo))
            test_strategy = {**strategy, **params}

            # 执行回测
            engine = BacktestEngine()
            result = engine.run_backtest(
                strategy=test_strategy,
                price_data=price_data,
                symbol=symbol
            )

            # 记录结果
            results.append({
                "params": params,
                "metrics": result["metrics"],
                "trades_count": len(result["trades"])
            })

            logger.info(f"组合 {i+1}/{len(combinations)}: {params} -> 收益率: {result['metrics']['total_return']:.2%}")

        # 找出最优参数
        best = self._find_best(results)

        return {
            "total_combinations": len(combinations),
            "results": results,
            "best": best,
            "created_at": datetime.now().isoformat()
        }

    def _find_best(self, results: List[Dict]) -> Dict:
        """
        找出最优参数

        Args:
            results: 所有结果

        Returns:
            Dict: 最优结果
        """
        if not results:
            return {}

        # 按夏普比率排序
        sorted_results = sorted(
            results,
            key=lambda x: x["metrics"].get("sharpe_ratio", 0),
            reverse=True
        )

        return sorted_results[0]

    def walk_forward_optimization(
        self,
        strategy: Dict[str, Any],
        price_data: List[Dict[str, Any]],
        param_grid: Dict[str, List],
        train_size: int = 252,
        test_size: int = 21,
        symbol: str = "SH600000"
    ) -> Dict[str, Any]:
        """
        Walk-Forward 优化

        Args:
            strategy: 策略基础配置
            price_data: 价格数据
            param_grid: 参数网格
            train_size: 训练集大小
            test_size: 测试集大小
            symbol: 股票代码

        Returns:
            Dict: 优化结果
        """
        results = []
        best_params_list = []

        for i in range(0, len(price_data) - train_size - test_size, test_size):
            train_data = price_data[i:i + train_size]
            test_data = price_data[i + train_size:i + train_size + test_size]

            # 训练集优化
            train_result = self.grid_search(strategy, train_data, param_grid, symbol)
            best_params = train_result["best"]["params"]
            best_params_list.append(best_params)

            # 测试集验证
            test_strategy = {**strategy, **best_params}
            engine = BacktestEngine()
            test_result = engine.run_backtest(
                strategy=test_strategy,
                price_data=test_data,
                symbol=symbol
            )

            results.append({
                "period_start": i,
                "period_end": i + train_size + test_size,
                "best_params": best_params,
                "test_metrics": test_result["metrics"]
            })

            logger.info(f"Walk-Forward {len(results)}: {best_params} -> 测试收益率: {test_result['metrics']['total_return']:.2%}")

        return {
            "results": results,
            "best_params_list": best_params_list,
            "created_at": datetime.now().isoformat()
        }


# 单例模式
_optimizer: Optional[ParameterOptimizer] = None


def get_optimizer() -> ParameterOptimizer:
    """获取优化器单例"""
    global _optimizer
    if _optimizer is None:
        _optimizer = ParameterOptimizer()
    return _optimizer
