"""
策略模块初始化
"""

from backend.strategy.generator import StrategyGenerator, get_strategy_generator
from backend.strategy.backtest import BacktestEngine
from backend.strategy.optimizer import ParameterOptimizer, get_optimizer
from backend.strategy.risk_control import RiskController, get_risk_controller
from backend.strategy.paper_trading import PaperTrader, get_paper_trader

__all__ = [
    "StrategyGenerator",
    "get_strategy_generator",
    "BacktestEngine",
    "ParameterOptimizer",
    "get_optimizer",
    "RiskController",
    "get_risk_controller",
    "PaperTrader",
    "get_paper_trader"
]
