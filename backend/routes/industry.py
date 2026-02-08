"""
行业分析路由模块

提供行业分析和选股推荐接口
"""

from typing import Optional, List, Dict
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from backend.data_loader import get_data_loader
from backend.stock_selection import get_screening, get_enhancement
from backend.log import logger


# FastAPI 应用
app = FastAPI(
    title="GX量化行业分析服务",
    description="提供行业分析和选股推荐功能的 API 服务",
    version="1.0.0"
)


# ========== Pydantic Models ==========

class IndustryAnalysis(BaseModel):
    """行业分析结果"""
    industry: str
    stock_count: int
    avg_prediction: float
    up_ratio: float
    top_stocks: List[Dict]
    created_at: str


class PreviewRecommend(BaseModel):
    """预览推荐结果"""
    industry: str
    total_stocks: int
    recommended_count: int
    recommended_stocks: List[str]
    average_confidence: float
    created_at: str


class AnalyzeSelected(BaseModel):
    """分析选定股票结果"""
    industry: str
    analyzed_count: int
    results: List[Dict]
    created_at: str


# ========== API Endpoints ==========

@app.get("/", summary="根路径")
async def root():
    """服务根路径"""
    return {
        "service": "GX量化行业分析服务",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/industry/list", summary="获取行业列表")
async def list_industries():
    """
    获取所有可用行业列表
    """
    try:
        loader = get_data_loader()
        industries = loader.get_industry_list()

        # 统计每个行业的股票数量
        result = [
            {
                "name": name,
                "stock_count": len(stocks)
            }
            for name, stocks in industries.items()
        ]

        return {
            "industries": result,
            "total_count": len(result)
        }

    except Exception as e:
        logger.error(f"获取行业列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/industry/{industry}/stocks", summary="获取行业股票")
async def get_industry_stocks(industry: str):
    """
    获取指定行业的所有股票
    """
    try:
        screening = get_screening()
        stocks = screening.get_industry_stocks(industry)

        return {
            "industry": industry,
            "stocks": stocks,
            "count": len(stocks)
        }

    except Exception as e:
        logger.error(f"获取行业股票失败: {industry} - {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/industry/{industry}/analysis", response_model=IndustryAnalysis, summary="分析行业")
async def analyze_industry(
    industry: str,
    model: str = Query("moving_average", description="预测模型")
):
    """
    分析指定行业

    - 获取行业所有股票
    - 生成预测因子
    - 计算统计数据
    """
    try:
        screening = get_screening()
        enhancement = get_enhancement()

        # 1. 获取行业股票
        stocks = screening.get_industry_stocks(industry)
        if not stocks:
            return IndustryAnalysis(
                industry=industry,
                stock_count=0,
                avg_prediction=0,
                up_ratio=0,
                top_stocks=[],
                created_at=datetime.now().isoformat()
            )

        # 2. 生成预测报告
        report = enhancement.get_prediction_report(stocks, model)

        # 3. 找出上涨的股票
        up_stocks = [
            {"code": stock, **report["factors"][stock]}
            for stock in stocks
            if report["factors"].get(stock, {}).get("trend") == "up"
        ]

        # 4. 按置信度排序
        up_stocks.sort(key=lambda x: x.get("confidence", 0), reverse=True)

        return IndustryAnalysis(
            industry=industry,
            stock_count=len(stocks),
            avg_prediction=report["avg_confidence"],
            up_ratio=report["up_count"] / max(report["total_stocks"], 1),
            top_stocks=up_stocks[:10],  # 前10只
            created_at=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"行业分析失败: {industry} - {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/industry/preview-recommend", response_model=PreviewRecommend, summary="预览推荐")
async def preview_recommend(industry: str):
    """
    预览行业推荐

    快速获取行业推荐结果预览
    """
    try:
        screening = get_screening()
        enhancement = get_enhancement()

        # 1. 初筛
        result = screening.preliminary_screening(industry)

        # 2. 增强筛选
        enhanced = enhancement.enhance_screening(
            stocks=result["shortlisted"],
            min_confidence=0.5
        )

        # 3. 计算平均置信度
        if enhanced:
            report = enhancement.get_prediction_report(enhanced)
            avg_conf = report["avg_confidence"]
        else:
            avg_conf = 0

        return PreviewRecommend(
            industry=industry,
            total_stocks=result["total_count"],
            recommended_count=len(enhanced),
            recommended_stocks=enhanced[:20],
            average_confidence=avg_conf,
            created_at=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"预览推荐失败: {industry} - {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/industry/analyze-selected", response_model=AnalyzeSelected, summary="分析选定股票")
async def analyze_selected(industry: str, stocks: List[str]):
    """
    分析选定股票池

    对选定的股票列表进行深入分析
    """
    try:
        screening = get_screening()
        enhancement = get_enhancement()

        # 1. 验证行业
        industry_stocks = set(screening.get_industry_stocks(industry))
        valid_stocks = [s for s in stocks if s in industry_stocks]

        # 2. 生成预测因子
        factors = enhancement.generate_prediction_factors(valid_stocks)

        # 3. 构建分析结果
        results = []
        for stock in valid_stocks:
            factor = factors.get(stock, {})
            results.append({
                "code": stock,
                "prediction": factor.get("prediction", 0),
                "confidence": factor.get("confidence", 0),
                "trend": factor.get("trend", "neutral"),
                "shortlisted": stock in screening._determine_shortlist(valid_stocks)
            })

        # 按置信度排序
        results.sort(key=lambda x: x.get("confidence", 0), reverse=True)

        return AnalyzeSelected(
            industry=industry,
            analyzed_count=len(valid_stocks),
            results=results,
            created_at=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"分析选定股票失败: {industry} - {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 启动服务 ==========

if __name__ == "__main__":
    import uvicorn

    logger.info("启动行业分析服务...")
    uvicorn.run(app, host="0.0.0.0", port=8003)
