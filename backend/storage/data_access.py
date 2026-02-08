"""
统一数据访问接口模块

封装底层数据访问逻辑，提供统一的数据访问接口
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from backend.data_loader import get_data_loader, DataLoader
from backend.log import logger


class DataAccess:
    """
    统一数据访问类

    提供股票、K线、行业、财务等数据的统一访问接口

    Attributes:
        loader: 数据加载器实例
    """

    def __init__(self, data_loader: Optional[DataLoader] = None):
        """
        初始化数据访问接口

        Args:
            data_loader: 可选的数据加载器实例
        """
        self.loader = data_loader or get_data_loader()
        logger.info("数据访问接口初始化完成")

    def get_stock_data(
        self,
        code: Optional[str] = None,
        fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        获取股票基本信息

        Args:
            code: 股票代码，不传则返回全部
            fields: 返回字段列表，None则返回全部

        Returns:
            股票信息列表
        """
        try:
            df = self.loader.load_stock_basic()
            if df.empty:
                logger.warning("股票基本信息为空")
                return []

            # 筛选特定股票
            if code:
                code = self.loader.normalize_code(code)
                df = df[df.apply(
                    lambda row: code in str(row.values),
                    axis=1
                )]

            # 筛选特定字段
            if fields:
                df = df[[f for f in fields if f in df.columns]]

            # 转换为字典列表
            return df.to_dict(orient='records')

        except Exception as e:
            logger.error(f"获取股票数据失败: {e}")
            return []

    def get_kline_data(
        self,
        code: str,
        period: str = 'daily',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取K线数据

        Args:
            code: 股票代码
            period: 周期 ('daily', '1d', '1m', '5m')
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            K线数据字典
        """
        try:
            df = self.loader.load_kline(
                code=code,
                period=period,
                start_date=start_date,
                end_date=end_date
            )

            if df.empty:
                logger.warning(f"K线数据为空: {code}")
                return {"columns": [], "data": []}

            # 返回标准格式
            return {
                "columns": df.columns.tolist(),
                "data": df.to_dict(orient='records'),
                "count": len(df),
                "code": self.loader.normalize_code(code),
                "period": period
            }

        except Exception as e:
            logger.error(f"获取K线数据失败: {code} - {e}")
            return {"columns": [], "data": [], "error": str(e)}

    def get_industry_data(self, industry: Optional[str] = None) -> Dict[str, List[str]]:
        """
        获取行业分类数据

        Args:
            industry: 行业名称，None则返回全部

        Returns:
            行业股票字典
        """
        try:
            industry_list = self.loader.get_industry_list()

            if not industry_list:
                logger.warning("行业数据为空")
                return {}

            # 筛选特定行业
            if industry:
                if industry in industry_list:
                    return {industry: industry_list[industry]}
                else:
                    logger.warning(f"行业不存在: {industry}")
                    return {}

            return industry_list

        except Exception as e:
            logger.error(f"获取行业数据失败: {e}")
            return {}

    def get_stocks_by_industry(self, industry: str) -> List[str]:
        """
        获取指定行业的所有股票

        Args:
            industry: 行业名称

        Returns:
            股票代码列表
        """
        try:
            stocks = self.loader.get_stocks_by_industry(industry)
            if not stocks:
                logger.warning(f"行业无股票数据: {industry}")
            return stocks

        except Exception as e:
            logger.error(f"获取行业股票失败: {industry} - {e}")
            return []

    def search_stocks(
        self,
        code: Optional[str] = None,
        name: Optional[str] = None,
        industry: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        多条件搜索股票

        Args:
            code: 股票代码
            name: 股票名称（模糊匹配）
            industry: 所属行业

        Returns:
            符合条件的股票列表
        """
        try:
            stocks = self.get_stock_data()

            # 按代码筛选
            if code:
                code = self.loader.normalize_code(code)
                stocks = [
                    s for s in stocks
                    if code in str(s).upper()
                ]

            # 按名称筛选
            if name:
                name = name.upper()
                stocks = [
                    s for s in stocks
                    if name in str(s).upper()
                ]

            # 按行业筛选
            if industry:
                industry_stocks = self.get_stocks_by_industry(industry)
                stocks = [
                    s for s in stocks
                    if self.loader.normalize_code(str(s.get('code', ''))) in industry_stocks
                ]

            return stocks

        except Exception as e:
            logger.error(f"搜索股票失败: {e}")
            return []


# 单例模式
_data_access: Optional[DataAccess] = None


def get_data_access() -> DataAccess:
    """
    获取数据访问接口单例

    Returns:
        DataAccess实例
    """
    global _data_access
    if _data_access is None:
        _data_access = DataAccess()
    return _data_access
