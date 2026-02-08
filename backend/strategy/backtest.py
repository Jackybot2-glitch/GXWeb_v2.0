"""
回测引擎模块

执行策略回测和绩效评估
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from backend.log import logger


class PositionType(Enum):
    """持仓类型"""
    LONG = "long"
    SHORT = "short"
    CASH = "cash"


@dataclass
class Trade:
    """交易记录"""
    timestamp: str
    action: str  # buy/sell
    price: float
    quantity: int
    commission: float = 0.0


@dataclass
class Position:
    """持仓"""
    symbol: str
    position_type: PositionType
    quantity: int
    entry_price: float
    entry_time: str
    stop_loss: float = 0.0
    take_profit: float = 0.0


class BacktestEngine:
    """
    回测引擎

    执行策略回测
    """

    def __init__(self, initial_capital: float = 100000):
        """
        初始化回测引擎

        Args:
            initial_capital: 初始资金
        """
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions: List[Position] = []
        self.trades: List[Trade] = []
        self.portfolio_value: List[Dict] = []

        logger.info(f"回测引擎初始化完成，初始资金: {initial_capital}")

    def run_backtest(
        self,
        strategy: Dict[str, Any],
        price_data: List[Dict[str, Any]],
        symbol: str = "SH600000"
    ) -> Dict[str, Any]:
        """
        执行回测

        Args:
            strategy: 策略配置
            price_data: 价格数据
            symbol: 股票代码

        Returns:
            Dict: 回测结果
        """
        # 重置状态
        self.capital = self.initial_capital
        self.positions = []
        self.trades = []
        self.portfolio_value = []

        # 执行回测
        for bar in price_data:
            timestamp = bar.get("datetime", bar.get("date", ""))
            price = bar.get("close", bar.get("Close", 0))

            if price <= 0:
                continue

            # 检查是否需要开仓
            if not self.positions:
                if self._should_entry(strategy, bar):
                    self._entry_position(symbol, PositionType.LONG, price, timestamp, strategy)

            # 检查是否需要平仓
            elif self.positions:
                position = self.positions[0]
                if self._should_exit(strategy, bar, position):
                    self._exit_position(position, price, timestamp)

            # 记录组合价值
            position_value = self._calculate_position_value(position, price) if self.positions else 0
            self.portfolio_value.append({
                "timestamp": timestamp,
                "value": self.capital + position_value
            })

        # 计算绩效指标
        metrics = self._calculate_metrics()

        logger.info(f"回测完成，最终价值: {metrics['final_value']:.2f}")
        return {
            "trades": self.trades,
            "portfolio_value": self.portfolio_value,
            "metrics": metrics,
            "created_at": datetime.now().isoformat()
        }

    def _should_entry(self, strategy: Dict, bar: Dict) -> bool:
        """
        判断是否开仓

        Args:
            strategy: 策略
            bar: K线数据

        Returns:
            bool: 是否开仓
        """
        # TODO: 实现更复杂的开仓逻辑
        return True

    def _should_exit(self, strategy: Dict, bar: Dict, position: Position) -> bool:
        """
        判断是否平仓

        Args:
            strategy: 策略
            bar: K线数据
            position: 持仓

        Returns:
            bool: 是否平仓
        """
        # 检查止损止盈
        current_price = bar.get("close", 0)

        # 止损
        if position.stop_loss > 0 and current_price <= position.entry_price * (1 - position.stop_loss):
            return True

        # 止盈
        if position.take_profit > 0 and current_price >= position.entry_price * (1 + position.take_profit):
            return True

        return False

    def _entry_position(
        self,
        symbol: str,
        position_type: PositionType,
        price: float,
        timestamp: str,
        strategy: Dict
    ):
        """
        开仓

        Args:
            symbol: 股票代码
            position_type: 持仓类型
            price: 开仓价格
            timestamp: 时间戳
            strategy: 策略配置
        """
        # 计算开仓数量（使用50%仓位）
        quantity = int(self.capital * 0.5 / price)

        if quantity <= 0:
            return

        # 记录交易
        trade = Trade(
            timestamp=timestamp,
            action="buy",
            price=price,
            quantity=quantity
        )
        self.trades.append(trade)

        # 更新资金
        self.capital -= price * quantity

        # 创建持仓
        position = Position(
            symbol=symbol,
            position_type=position_type,
            quantity=quantity,
            entry_price=price,
            entry_time=timestamp,
            stop_loss=strategy.get("stop_loss", 0.05),
            take_profit=strategy.get("take_profit", 0.10)
        )
        self.positions.append(position)

        logger.info(f"开仓: {symbol} @ {price}, 数量: {quantity}")

    def _exit_position(self, position: Position, price: float, timestamp: str):
        """
        平仓

        Args:
            position: 持仓
            price: 平仓价格
            timestamp: 时间戳
        """
        # 记录交易
        trade = Trade(
            timestamp=timestamp,
            action="sell",
            price=price,
            quantity=position.quantity
        )
        self.trades.append(trade)

        # 更新资金
        self.capital += price * position.quantity

        # 清空持仓
        self.positions = []

        logger.info(f"平仓: {position.symbol} @ {price}")

    def _calculate_position_value(self, position: Position, current_price: float) -> float:
        """
        计算持仓价值

        Args:
            position: 持仓
            current_price: 当前价格

        Returns:
            float: 持仓价值
        """
        return position.quantity * current_price

    def _calculate_metrics(self) -> Dict[str, Any]:
        """
        计算绩效指标

        Returns:
            Dict: 绩效指标
        """
        if not self.portfolio_value:
            return {}

        # 基本指标
        final_value = self.portfolio_value[-1].get("value", self.capital)
        total_return = (final_value - self.initial_capital) / self.initial_capital

        # 交易次数
        total_trades = len(self.trades)
        winning_trades = sum(1 for t in self.trades if t.action == "sell")
        win_rate = winning_trades / total_trades if total_trades > 0 else 0

        # 最大回撤
        max_drawdown = self._calculate_max_drawdown()

        return {
            "initial_capital": self.initial_capital,
            "final_value": final_value,
            "total_return": total_return,
            "total_trades": total_trades,
            "win_rate": win_rate,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": self._calculate_sharpe_ratio()
        }

    def _calculate_max_drawdown(self) -> float:
        """
        计算最大回撤

        Returns:
            float: 最大回撤
        """
        if not self.portfolio_value:
            return 0

        peak = self.portfolio_value[0]["value"]
        max_dd = 0

        for record in self.portfolio_value:
            if record["value"] > peak:
                peak = record["value"]
            dd = (peak - record["value"]) / peak if peak > 0 else 0
            max_dd = max(max_dd, dd)

        return max_dd

    def _calculate_sharpe_ratio(self) -> float:
        """
        计算夏普比率

        Returns:
            float: 夏普比率
        """
        if len(self.portfolio_value) < 2:
            return 0

        returns = []
        for i in range(1, len(self.portfolio_value)):
            prev = self.portfolio_value[i-1]["value"]
            curr = self.portfolio_value[i]["value"]
            if prev > 0:
                returns.append((curr - prev) / prev)

        if not returns:
            return 0

        import numpy as np
        returns = np.array(returns)
        if np.std(returns) == 0:
            return 0

        return np.mean(returns) / np.std(returns) * (252 ** 0.5)  # 年化
