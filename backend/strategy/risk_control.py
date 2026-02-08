"""
风险控制模块

实时风险监控和资金管理
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from backend.log import logger


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskMetrics:
    """风险指标"""
    current_drawdown: float
    current_exposure: float
    daily_pnl: float
    total_exposure: float
    risk_level: str


class RiskController:
    """
    风险控制器

    实时监控和控制系统风险
    """

    def __init__(
        self,
        max_position_pct: float = 0.25,
        max_daily_loss_pct: float = 0.05,
        max_total_loss_pct: float = 0.20,
        max_drawdown_pct: float = 0.15
    ):
        """
        初始化风险控制器

        Args:
            max_position_pct: 单个最大持仓比例
            max_daily_loss_pct: 单日最大亏损比例
            max_total_loss_pct: 累计最大亏损比例
            max_drawdown_pct: 最大回撤限制
        """
        self.max_position_pct = max_position_pct
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_total_loss_pct = max_total_loss_pct
        self.max_drawdown_pct = max_drawdown_pct

        self.initial_capital = 100000
        self.current_capital = 100000
        self.daily_pnl = 0
        self.positions: Dict[str, Dict] = {}

        logger.info("风险控制器初始化完成")

    def calculate_position_size(
        self,
        symbol: str,
        price: float,
        risk_per_trade: float = 0.02
    ) -> Dict[str, Any]:
        """
        计算仓位大小

        Args:
            symbol: 股票代码
            price: 当前价格
            risk_per_tride: 每笔风险比例

        Returns:
            Dict: 仓位信息
        """
        # 可用资金
        available = self._get_available_capital()

        # 风险金额
        risk_amount = self.current_capital * risk_per_trade

        # 假设止损为 5%
        stop_loss_pct = 0.05
        risk_per_share = price * stop_loss_pct

        # 仓位数量
        if risk_per_share > 0:
            quantity = int(risk_amount / risk_per_share)
        else:
            quantity = int(available / price)

        # 限制最大仓位
        max_quantity = int(self.current_capital * self.max_position_pct / price)
        quantity = min(quantity, max_quantity)

        # 资金限制
        max_by_capital = int(available / price)
        quantity = min(quantity, max_by_capital)

        if quantity <= 0:
            return {
                "symbol": symbol,
                "quantity": 0,
                "reason": "资金不足"
            }

        return {
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "estimated_value": quantity * price,
            "risk_amount": quantity * price * stop_loss_pct,
            "risk_pct": (quantity * price) / self.current_capital
        }

    def check_risk(
        self,
        symbol: str,
        action: str,
        quantity: int,
        price: float
    ) -> Dict[str, Any]:
        """
        检查交易风险

        Args:
            symbol: 股票代码
            action: 动作 (buy/sell)
            quantity: 数量
            price: 价格

        Returns:
            Dict: 风险检查结果
        """
        # 检查日亏损
        if self.daily_pnl < -self.current_capital * self.max_daily_loss_pct:
            return {
                "allowed": False,
                "reason": "已达到日亏损限制",
                "risk_level": RiskLevel.CRITICAL
            }

        # 检查总亏损
        total_loss = (self.initial_capital - self.current_capital) / self.initial_capital
        if total_loss >= self.max_total_loss_pct:
            return {
                "allowed": False,
                "reason": "已达到总亏损限制",
                "risk_level": RiskLevel.CRITICAL
            }

        # 检查持仓集中度
        position_value = self._get_position_value(symbol)
        total_exposure = self._get_total_exposure()

        new_exposure = total_exposure + (quantity * price if action == "buy" else 0)
        new_exposure_pct = new_exposure / self.current_capital

        if new_exposure_pct > self.max_position_pct:
            return {
                "allowed": False,
                "reason": f"持仓超过 {self.max_position_pct:.0%} 限制",
                "risk_level": RiskLevel.HIGH
            }

        # 检查单个持仓
        if position_value + (quantity * price if action == "buy" else 0) > self.current_capital * self.max_position_pct:
            return {
                "allowed": False,
                "reason": f"单只股票持仓超过 {self.max_position_pct:.0%} 限制",
                "risk_level": RiskLevel.MEDIUM
            }

        return {
            "allowed": True,
            "risk_level": RiskLevel.LOW
        }

    def update_position(
        self,
        symbol: str,
        action: str,
        quantity: int,
        price: float
    ):
        """
        更新持仓

        Args:
            symbol: 股票代码
            action: 动作
            quantity: 数量
            price: 价格
        """
        if symbol not in self.positions:
            self.positions[symbol] = {
                "quantity": 0,
                "avg_price": 0
            }

        position = self.positions[symbol]

        if action == "buy":
            # 更新平均成本
            total_value = position["quantity"] * position["avg_price"] + quantity * price
            total_quantity = position["quantity"] + quantity
            position["avg_price"] = total_value / total_quantity if total_quantity > 0 else 0
            position["quantity"] = total_quantity

        elif action == "sell":
            position["quantity"] -= quantity
            if position["quantity"] <= 0:
                del self.positions[symbol]

    def get_risk_report(self) -> Dict[str, Any]:
        """
        获取风险报告

        Returns:
            Dict: 风险报告
        """
        total_exposure = self._get_total_exposure()
        current_drawdown = self._calculate_drawdown()

        # 评估风险等级
        if current_drawdown >= self.max_drawdown_pct:
            risk_level = RiskLevel.CRITICAL
        elif current_drawdown >= self.max_drawdown_pct * 0.7:
            risk_level = RiskLevel.HIGH
        elif total_exposure / self.current_capital >= self.max_position_pct * 0.8:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        return {
            "initial_capital": self.initial_capital,
            "current_capital": self.current_capital,
            "total_exposure": total_exposure,
            "exposure_pct": total_exposure / self.current_capital if self.current_capital > 0 else 0,
            "current_drawdown": current_drawdown,
            "daily_pnl": self.daily_pnl,
            "daily_pnl_pct": self.daily_pnl / self.initial_capital,
            "positions_count": len(self.positions),
            "risk_level": risk_level.value,
            "created_at": datetime.now().isoformat()
        }

    def _get_available_capital(self) -> float:
        """获取可用资金"""
        total_exposure = self._get_total_exposure()
        return max(0, self.current_capital - total_exposure)

    def _get_position_value(self, symbol: str) -> float:
        """获取持仓市值"""
        if symbol not in self.positions:
            return 0
        # TODO: 需要实时价格
        return self.positions[symbol]["quantity"] * self.current_capital

    def _get_total_exposure(self) -> float:
        """获取总敞口"""
        return sum(
            self.positions[s]["quantity"] * self.current_capital
            for s in self.positions
        )

    def _calculate_drawdown(self) -> float:
        """计算当前回撤"""
        if self.initial_capital == 0:
            return 0
        peak = self.initial_capital
        current = self.current_capital
        return max(0, (peak - current) / peak)


# 单例模式
_risk_controller: Optional[RiskController] = None


def get_risk_controller() -> RiskController:
    """获取风险控制器单例"""
    global _risk_controller
    if _risk_controller is None:
        _risk_controller = RiskController()
    return _risk_controller
