"""
GX量化 Web 统一平台 v2.0 - 统一数据加载器

提供股票数据、K线、行业数据等的统一访问接口
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from abc import ABC, abstractmethod

import pandas as pd
import numpy as np


class DataLoader:
    """
    统一数据加载器

    支持加载：
    - K线数据（日线、分钟线）
    - 股票基本信息
    - 行业分类数据
    - 财务数据
    """

    def __init__(self, data_root: Optional[str] = None):
        """
        初始化数据加载器

        Args:
            data_root: 数据根目录，默认为配置中的 QUANTDATA_PATH
        """
        from backend.config import config

        self.data_root = Path(data_root or config.QUANTDATA_PATH)
        self._cache: Dict[str, Any] = {}

        # 验证数据目录存在
        if not self.data_root.exists():
            print(f"⚠️  数据目录不存在: {self.data_root}")

    @staticmethod
    def normalize_code(code: str) -> str:
        """
        统一股票代码格式

        支持格式：
        - 600000.SH
        - 000001.SZ
        - SH600000
        - SZ000001

        输出格式：SH600000 或 SZ000001
        """
        if not code:
            return code

        code = code.strip().upper().replace('.', '')

        # 如果已经是标准格式
        if code.startswith(('SH', 'SZ', 'BJ')):
            return code

        # 补全交易所前缀
        if len(code) == 6:
            # 6开头是上海，0/3开头是深圳
            prefix = 'SH' if code.startswith('6') else 'SZ'
            return f"{prefix}{code}"

        return code

    def load_kline(
        self,
        code: str,
        period: str = 'daily',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        加载K线数据

        Args:
            code: 股票代码（支持多种格式）
            period: 周期 ('daily', '1d', '1m', '5m')
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            DataFrame，包含K线数据
        """
        cache_key = f"kline_{code}_{period}_{start_date}_{end_date}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        ncode = self.normalize_code(code)

        # 尝试从QuantData加载
        # 优先检查 stock_daily 目录
        data_path = self.data_root / "stock_daily" / f"{ncode}.csv"
        if not data_path.exists():
            # 备选 daily 目录
            data_path = self.data_root / "daily" / f"{ncode}.csv"

        if data_path.exists():
            # 尝试多种编码
            for enc in ['utf-8', 'gbk', 'gb2312', 'gb18030']:
                try:
                    # 跳过前2行，逗号分隔
                    df = pd.read_csv(
                        data_path,
                        encoding=enc,
                        skiprows=2,
                        header=None,
                        names=['date', 'open', 'high', 'low', 'close', 'volume', 'amount']
                    )
                    if len(df) > 0:
                        break
                except Exception:
                    continue
            else:
                # 如果所有编码都失败，返回空
                return pd.DataFrame()

            # 设置列名
            if len(df.columns) == 8:
                df.columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount', 'adjust']
            elif len(df.columns) == 7:
                df.columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount']
            elif len(df.columns) == 6:
                df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
            else:
                # 使用通用列名
                df.columns = [f'col_{i}' for i in range(len(df.columns))]

            # 清理数据：移除空行和无效数据
            df = df.dropna(subset=['date'])
            df = df[df['date'].astype(str).str.strip() != '']

            # 转换数值列
            numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # 添加 datetime 列
            if 'date' in df.columns:
                df['datetime'] = pd.to_datetime(df['date'], errors='coerce')
                df = df.dropna(subset=['datetime'])
                df = df.sort_values('datetime')
            # 转换日期
            if 'trade_date' in df.columns:
                df['datetime'] = pd.to_datetime(df['trade_date'])
            elif 'date' in df.columns:
                df['datetime'] = pd.to_datetime(df['date'])

            # 筛选日期范围
            if start_date:
                df = df[df['datetime'] >= start_date]
            if end_date:
                df = df[df['datetime'] <= end_date]

            df = df.sort_values('datetime')
            self._cache[cache_key] = df
            return df

        # 如果不存在，返回空DataFrame
        return pd.DataFrame()

    def load_stock_basic(self) -> pd.DataFrame:
        """加载股票基本信息"""
        cache_key = "stock_basic"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # 查找股票基本信息文件
        possible_paths = [
            self.data_root / "stock_basic_info.csv",
            self.data_root / "stock_basic.csv",
        ]

        for path in possible_paths:
            if path.exists():
                # 尝试多种编码
                for enc in ['utf-8', 'gbk', 'gb2312']:
                    try:
                        df = pd.read_csv(path, encoding=enc)
                        self._cache[cache_key] = df
                        return df
                    except Exception:
                        continue

        return pd.DataFrame()

    def get_industry_list(self) -> Dict[str, List[str]]:
        """
        获取行业列表

        Returns:
            Dict[行业名称, [股票代码列表]]
        """
        basic_df = self.load_stock_basic()
        if basic_df.empty:
            return {}

        # 查找行业列
        industry_col = None
        code_col = None

        for col in basic_df.columns:
            col_lower = col.lower()
            if 'industry' in col_lower or '行业' in col:
                industry_col = col
            if col_lower in ['ts_code', 'code', 'symbol', '股票代码']:
                code_col = col

        if not industry_col or not code_col:
            return {}

        result: Dict[str, List[str]] = {}
        for _, row in basic_df.iterrows():
            industry = str(row[industry_col]).strip()
            code = self.normalize_code(str(row[code_col]))
            if industry and code:
                result.setdefault(industry, []).append(code)

        return result

    def get_stocks_by_industry(self, industry: str) -> List[str]:
        """
        获取指定行业的所有股票

        Args:
            industry: 行业名称

        Returns:
            股票代码列表
        """
        industry_list = self.get_industry_list()
        return industry_list.get(industry, [])

    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()


# 单例模式
_loader: Optional[DataLoader] = None


def get_data_loader(data_root: Optional[str] = None) -> DataLoader:
    """获取数据加载器单例"""
    global _loader
    if _loader is None:
        _loader = DataLoader(data_root)
    return _loader
