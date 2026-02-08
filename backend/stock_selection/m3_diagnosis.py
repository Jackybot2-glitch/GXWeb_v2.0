"""
股票推荐模块 - M3 AI 诊断

使用 AI 模型进行股票智能诊断
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from backend.ai_client import get_ai_manager
from backend.data_loader import get_data_loader
from backend.log import logger


class StockDiagnosis:
    """
    AI 股票诊断模块

    使用 AI 模型进行多维度股票诊断
    """

    def __init__(self):
        """初始化诊断模块"""
        self.ai = get_ai_manager()
        self.data_loader = get_data_loader()
        logger.info("AI股票诊断模块初始化完成")

    def diagnose_stock(
        self,
        stock_code: str,
        aspects: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        诊断单只股票

        Args:
            stock_code: 股票代码
            aspects: 诊断方面 (基本面、技术面、资金面、消息面)

        Returns:
            Dict: 诊断结果
        """
        if aspects is None:
            aspects = ["基本面", "技术面", "资金面", "消息面"]

        # 1. 收集股票数据
        stock_data = self._collect_stock_data(stock_code)

        # 2. AI 分析
        diagnosis = {}
        for aspect in aspects:
            diagnosis[aspect] = self._analyze_aspect(stock_code, stock_data, aspect)

        # 3. 综合评分
        overall_score = self._calculate_overall_score(diagnosis)

        result = {
            "code": stock_code,
            "diagnosis": diagnosis,
            "overall_score": overall_score,
            "created_at": datetime.now().isoformat()
        }

        logger.info(f"股票诊断完成: {stock_code}, 评分: {overall_score:.1f}")
        return result

    def _collect_stock_data(self, stock_code: str) -> Dict[str, Any]:
        """
        收集股票相关数据

        Args:
            stock_code: 股票代码

        Returns:
            Dict: 股票数据
        """
        data = {
            "basic": None,
            "kline": None,
            "industry": None
        }

        # 基本信息
        try:
            basic = self.data_loader.get_stock_data(code=stock_code)
            if basic:
                data["basic"] = basic[0] if isinstance(basic, list) and len(basic) > 0 else basic
        except Exception as e:
            logger.warning(f"获取基本信息失败: {stock_code} - {e}")

        # K线数据
        try:
            kline = self.data_loader.load_kline(stock_code, "daily")
            if not kline.empty:
                data["kline"] = kline.tail(30).to_dict(orient="records")
        except Exception as e:
            logger.warning(f"获取K线数据失败: {stock_code} - {e}")

        # 行业信息
        try:
            industries = self.data_loader.get_industry_list()
            for industry, stocks in industries.items():
                normalized_stocks = [self.data_loader.normalize_code(s) for s in stocks]
                if self.data_loader.normalize_code(stock_code) in normalized_stocks:
                    data["industry"] = industry
                    break
        except Exception as e:
            logger.warning(f"获取行业信息失败: {stock_code} - {e}")

        return data

    def _analyze_aspect(
        self,
        stock_code: str,
        stock_data: Dict,
        aspect: str
    ) -> Dict[str, Any]:
        """
        分析单个方面

        Args:
            stock_code: 股票代码
            stock_data: 股票数据
            aspect: 分析方面

        Returns:
            Dict: 分析结果
        """
        prompt = f"""
请分析股票 {stock_code} 的 {aspect}。

数据:
{stock_data}

请给出：
1. 当前状况简述 (1-2句话)
2. 评分 (0-100)
3. 关键指标
4. 风险提示

请用JSON格式回复。
"""

        try:
            response = self.ai.chat([
                {"role": "system", "content": "你是一个专业的股票分析师。"},
                {"role": "user", "content": prompt}
            ])

            # 解析AI回复
            return self._parse_ai_response(response)

        except Exception as e:
            logger.error(f"AI分析失败: {aspect} - {e}")
            return {
                "aspect": aspect,
                "score": 50,
                "summary": f"AI分析失败: {str(e)}",
                "details": {}
            }

    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """
        解析AI回复

        Args:
            response: AI回复文本

        Returns:
            Dict: 结构化结果
        """
        # TODO: 实现更复杂的解析逻辑
        return {
            "aspect": "",
            "score": 50,
            "summary": response[:200],
            "details": {}
        }

    def _calculate_overall_score(self, diagnosis: Dict[str, Dict]) -> float:
        """
        计算综合评分

        Args:
            diagnosis: 各方面诊断结果

        Returns:
            float: 综合评分 (0-100)
        """
        if not diagnosis:
            return 50.0

        scores = [
            d.get("score", 50)
            for d in diagnosis.values()
            if isinstance(d, dict) and "score" in d
        ]

        if not scores:
            return 50.0

        return sum(scores) / len(scores)

    def batch_diagnosis(
        self,
        stocks: List[str],
        aspects: Optional[List[str]] = None,
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """
        批量诊断

        Args:
            stocks: 股票代码列表
            aspects: 诊断方面
            max_concurrent: 最大并发数

        Returns:
            List[Dict]: 诊断结果列表
        """
        results = []
        for stock in stocks:
            try:
                result = self.diagnose_stock(stock, aspects)
                results.append(result)
            except Exception as e:
                logger.error(f"批量诊断失败: {stock} - {e}")
                results.append({
                    "code": stock,
                    "error": str(e),
                    "created_at": datetime.now().isoformat()
                })

        logger.info(f"批量诊断完成: {len(results)} 只股票")
        return results


# 单例模式
_diagnosis: Optional[StockDiagnosis] = None


def get_diagnosis() -> StockDiagnosis:
    """获取股票诊断模块单例"""
    global _diagnosis
    if _diagnosis is None:
        _diagnosis = StockDiagnosis()
    return _diagnosis
