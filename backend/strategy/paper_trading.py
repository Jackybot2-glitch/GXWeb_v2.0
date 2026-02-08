"""
模拟交易模块

实时模拟交易执行
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

from backend.strategy.risk_control import RiskController, get_risk_controller
from backend.log import logger


@dataclass
class Order:
    """订单"""
    symbol: str
    action: str  # buy/sell
    quantity: int
    price: float
    order_type: str = "limit"  # limit/market
    status: str = "pending"
    created_at: str = ""
    filled_at: Optional[str] = None


@dataclass
class TradeRecord:
    """成交记录"""
    symbol: str
    action: str
    quantity: int
    price: float
    commission: float
    created_at: str


class PaperTrader:
    """
    模拟交易员

    模拟真实交易环境
    """

    def __init__(
        self,
        initial_capital: float = 100000,
        risk_controller: Optional[RiskController] = None
    ):
        """
        初始化模拟交易员

        Args:
            initial_capital: 初始资金
            risk_controller: 风险控制器
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Dict] = {}
        self.orders: List[Order] = []
        self.trades: List[TradeRecord] = []
        self.trade_history: List[Dict] = []

        self.risk_controller = risk_controller or get_risk_controller()

        logger.info(f"模拟交易员初始化，初始资金: {initial_capital}")

    def submit_order(
        self,
        symbol: str,
        action: str,
        quantity: int,
        price: float,
        order_type: str = "limit"
    ) -> Dict[str, Any]:
        """
        提交订单

        Args:
            symbol: 股票代码
            action: 动作 (buy/sell)
            quantity: 数量
            price: 价格
            order_type: 订单类型

        Returns:
            Dict: 订单信息
        """
        # 风险检查
        risk_check = self.risk_controller.check_risk(symbol, action, quantity, price)

        if not risk_check["allowed"]:
            logger.warning(f"订单被拒绝: {risk_check['reason']}")
            return {
                "order_id": "",
                "status": "rejected",
                "reason": risk_check["reason"]
            }

        # 创建订单
        order = Order(
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=price,
            order_type=order_type,
            status="pending",
            created_at=datetime.now().isoformat()
        )

        self.orders.append(order)

        logger.info(f"订单已提交: {order.symbol} {order.action} {order.quantity} @ {order.price}")

        return {
            "order_id": f"order_{len(self.orders)}",
            "status": "pending",
            "order": order.__dict__
        }

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        取消订单

        Args:
            order_id: 订单ID

        Returns:
            Dict: 操作结果
        """
        try:
            idx = int(order_id.split("_")[1]) - 1
            if 0 <= idx < len(self.orders):
                self.orders[idx].status = "cancelled"
                logger.info(f"订单已取消: {order_id}")
                return {"status": "cancelled", "order_id": order_id}
        except:
            pass

        return {"status": "failed", "order_id": order_id}

    def execute_orders(self, current_prices: Dict[str, float]):
        """
        执行订单

        Args:
            current_prices: 当前价格
        """
        for i, order in enumerate(self.orders):
            if order.status != "pending":
                continue

            current_price = current_prices.get(order.symbol, order.price)

            # 检查是否成交
            if order.order_type == "market":
                executed = True
            else:
                # 限价单：买入时需要当前价格 <= 委托价格，卖出时需要当前价格 >= 委托价格
                if order.action == "buy":
                    executed = current_price <= order.price
                else:
                    executed = current_price >= order.price

            if executed:
                self._fill_order(order, current_price)

    def _fill_order(self, order: Order, fill_price: float):
        """
        成交订单

        Args:
            order: 订单
            fill_price: 成交价格
        """
        order.status = "filled"
        order.filled_at = datetime.now().isoformat()

        # 佣金
        commission = fill_price * order.quantity * 0.0003  # 万三佣金

        # 创建成交记录
        trade = TradeRecord(
            symbol=order.symbol,
            action=order.action,
            quantity=order.quantity,
            price=fill_price,
            commission=commission,
            created_at=order.filled_at
        )
        self.trades.append(trade)

        # 更新资金
        cost = fill_price * order.quantity + commission
        if order.action == "buy":
            self.cash -= cost
        else:
            self.cash += cost

        # 更新持仓
        if order.action == "buy":
            if order.symbol not in self.positions:
                self.positions[order.symbol] = {
                    "quantity": 0,
                    "avg_price": 0
                }
            pos = self.positions[order.symbol]
            total_value = pos["quantity"] * pos["avg_price"] + order.quantity * fill_price
            total_qty = pos["quantity"] + order.quantity
            pos["avg_price"] = total_value / total_qty
            pos["quantity"] = total_qty
        else:
            if order.symbol in self.positions:
                self.positions[order.symbol]["quantity"] -= order.quantity
                if self.positions[order.symbol]["quantity"] <= 0:
                    del self.positions[order.symbol]

        # 更新风险控制器
        self.risk_controller.update_position(order.symbol, order.action, order.quantity, fill_price)

        logger.info(f"订单成交: {order.symbol} {order.action} {order.quantity} @ {fill_price}")

    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """
        获取组合价值

        Args:
            current_prices: 当前价格

        Returns:
            float: 组合总价值
        """
        position_value = sum(
            self.positions[symbol]["quantity"] * current_prices.get(symbol, 0)
            for symbol in self.positions
        )
        return self.cash + position_value

    def get_status(self, current_prices: Dict[str, float]) -> Dict[str, Any]:
        """
        获取交易状态

        Args:
            current_prices: 当前价格

        Returns:
            Dict: 状态信息
        """
        portfolio_value = self.get_portfolio_value(current_prices)
        total_return = (portfolio_value - self.initial_capital) / self.initial_capital

        return {
            "cash": self.cash,
            "positions": self.positions,
            "pending_orders": len([o for o in self.orders if o.status == "pending"]),
            "portfolio_value": portfolio_value,
            "total_return": total_return,
            "trade_count": len(self.trades),
            "created_at": datetime.now().isoformat()
        }

    def get_trade_history(self) -> List[Dict]:
        """
        获取交易历史

        Returns:
            List: 交易历史
        """
        return self.trade_history


# 单例模式
_paper_trader: Optional[PaperTrader] = None


def get_paper_trader() -> PaperTrader:
    """获取模拟交易员单例"""
    global _paper_trader
    if _paper_trader is None:
        _paper_trader = PaperTrader()
    return _paper_trader
