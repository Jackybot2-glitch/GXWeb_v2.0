"""
股票推荐模块 - M2 初筛

行业分析 + 因子筛选 + 入围判断
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from backend.data_loader import get_data_loader
from backend.log import logger


class StockScreening:
    """
    股票初筛模块

    根据行业和因子条件筛选股票
    """

    def __init__(self):
        """初始化选股模块"""
        self.data_loader = get_data_loader()
        logger.info("股票初筛模块初始化完成")

    def get_industry_stocks(self, industry: str) -> List[str]:
        """
        获取指定行业的所有股票

        Args:
            industry: 行业名称

        Returns:
            List[str]: 股票代码列表
        """
        stocks = self.data_loader.get_stocks_by_industry(industry)
        logger.info(f"行业 {industry} 共有 {len(stocks)} 只股票")
        return stocks

    def screen_by_factors(
        self,
        stocks: List[str],
        factors: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        根据因子条件筛选股票

        Args:
            stocks: 股票代码列表
            factors: 因子条件字典

        Returns:
            List[str]: 符合条件的股票列表
        """
        if not stocks:
            return []

        # 加载所有股票的基本数据
        all_stocks = self.data_loader.get_stock_data()

        if not all_stocks:
            logger.warning("无法获取股票数据")
            return stocks

        # 构建股票代码集合（用于快速查找）
        stock_set = set(stocks)

        # 筛选
        filtered = [
            s for s in all_stocks
            if self._match_factors(s, factors)
            and self._get_stock_code(s) in stock_set
        ]

        logger.info(f"因子筛选: {len(stocks)} -> {len(filtered)} 只股票")
        return [self._get_stock_code(s) for s in filtered]

    def _match_factors(self, stock: Dict, factors: Optional[Dict]) -> bool:
        """
        匹配股票因子条件

        Args:
            stock: 股票数据
            factors: 因子条件

        Returns:
            bool: 是否匹配
        """
        if not factors:
            return True

        # TODO: 实现具体的因子匹配逻辑
        return True

    def _get_stock_code(self, stock: Dict) -> str:
        """
        获取股票代码

        Args:
            stock: 股票数据

        Returns:
            str: 股票代码
        """
        # 查找可能的代码字段
        for key in ['code', 'stock_code', '股票代码', 'ts_code']:
            if key in stock:
                return str(stock[key])
        return ""

    def preliminary_screening(
        self,
        industry: str,
        factors: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行初筛流程

        Args:
            industry: 行业名称
            factors: 因子条件

        Returns:
            Dict: 初筛结果
        """
        start_time = datetime.now()

        # 1. 获取行业股票
        stocks = self.get_industry_stocks(industry)

        if not stocks:
            return {
                "industry": industry,
                "total_count": 0,
                "screened_count": 0,
                "stocks": [],
                "factors": factors,
                "elapsed_ms": (datetime.now() - start_time).total_seconds() * 1000
            }

        # 2. 因子筛选
        screened_stocks = self.screen_by_factors(stocks, factors)

        # 3. 入围判断
        shortlisted = self._determine_shortlist(screened_stocks)

        result = {
            "industry": industry,
            "total_count": len(stocks),
            "screened_count": len(screened_stocks),
            "shortlisted_count": len(shortlisted),
            "stocks": screened_stocks,
            "shortlisted": shortlisted,
            "factors": factors,
            "elapsed_ms": (datetime.now() - start_time).total_seconds() * 1000,
            "created_at": start_time.isoformat()
        }

        logger.info(f"初筛完成: {industry}, {len(stocks)} -> {len(shortlisted)} 只入围")
        return result

    def _determine_shortlist(
        self,
        stocks: List[str]
    ) -> List[str]:
        """
        入围判断

        Args:
            stocks: 筛选后的股票列表

        Returns:
            List[str]: 入围股票列表
        """
        # 默认返回前50只作为入围
        return stocks[:50]


# 单例模式
_screening: Optional[StockScreening] = None


def get_screening() -> StockScreening:
    """获取选股模块单例"""
    global _screening
    if _screening is None:
        _screening = StockScreening()
    return _screening
