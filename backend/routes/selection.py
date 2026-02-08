"""
股票推荐路由模块

提供选股相关的 API 接口
"""

from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from backend.stock_selection.m2_screening import get_screening
from backend.stock_selection.m2_1_prediction import get_enhancement
from backend.stock_selection.m3_diagnosis import get_diagnosis
from backend.log import logger


# FastAPI 应用
app = FastAPI(
    title="GX量化股票推荐服务",
    description="提供股票推荐和智能诊断功能的 API 服务",
    version="1.0.0"
)


# ========== Pydantic Models ==========

class ScreeningRequest(BaseModel):
    """选股请求"""
    industry: str
    factors: Optional[dict] = None


class ScreeningResponse(BaseModel):
    """选股响应"""
    success: bool
    industry: str
    total_count: int
    screened_count: int
    shortlisted_count: int
    stocks: List[str]
    shortlisted: List[str]
    elapsed_ms: float


class DiagnosisRequest(BaseModel):
    """诊断请求"""
    stock_code: str
    aspects: Optional[List[str]] = None


class DiagnosisResponse(BaseModel):
    """诊断响应"""
    success: bool
    code: str
    overall_score: float
    diagnosis: dict
    created_at: str


class EnhancementResponse(BaseModel):
    """预测增强响应"""
    success: bool
    total_stocks: int
    up_count: int
    down_count: int
    avg_confidence: float
    enhanced_count: int
    enhanced_stocks: List[str]


# ========== API Endpoints ==========

@app.get("/", summary="根路径")
async def root():
    """服务根路径"""
    return {
        "service": "GX量化股票推荐服务",
        "version": "1.0.0",
        "status": "running"
    }


@app.post("/selection/tasks", response_model=ScreeningResponse, summary="创建选股任务")
async def create_screening_task(request: ScreeningRequest):
    """
    创建选股任务

    - **industry**: 行业名称
    - **factors**: 筛选因子条件
    """
    try:
        logger.info(f"收到选股请求: {request.industry}")

        screening = get_screening()
        result = screening.preliminary_screening(
            industry=request.industry,
            factors=request.factors
        )

        return ScreeningResponse(
            success=True,
            industry=result["industry"],
            total_count=result["total_count"],
            screened_count=result["screened_count"],
            shortlisted_count=result["shortlisted_count"],
            stocks=result["stocks"],
            shortlisted=result["shortlisted"],
            elapsed_ms=result["elapsed_ms"]
        )

    except Exception as e:
        logger.error(f"选股任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/selection/industries", summary="获取行业列表")
async def list_industries():
    """
    获取所有可用行业列表
    """
    try:
        from backend.data_loader import get_data_loader
        loader = get_data_loader()
        industries = loader.get_industry_list()

        return {
            "industries": list(industries.keys()),
            "count": len(industries)
        }

    except Exception as e:
        logger.error(f"获取行业列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/selection/enhance", response_model=EnhancementResponse, summary="预测增强筛选")
async def enhance_screening(
    stocks: List[str],
    model: str = Query("moving_average", description="预测模型"),
    min_confidence: float = Query(0.5, ge=0, le=1)
):
    """
    使用预测因子增强筛选

    - **stocks**: 股票代码列表
    - **model**: 预测模型
    - **min_confidence**: 最低置信度
    """
    try:
        enhancement = get_enhancement()

        # 生成预测报告
        report = enhancement.get_prediction_report(stocks, model)

        # 增强筛选
        enhanced = enhancement.enhance_screening(
            stocks=stocks,
            model=model,
            min_confidence=min_confidence
        )

        return EnhancementResponse(
            success=True,
            total_stocks=report["total_stocks"],
            up_count=report["up_count"],
            down_count=report["down_count"],
            avg_confidence=report["avg_confidence"],
            enhanced_count=len(enhanced),
            enhanced_stocks=enhanced
        )

    except Exception as e:
        logger.error(f"预测增强失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/diagnosis", response_model=DiagnosisResponse, summary="AI股票诊断")
async def diagnose_stock(request: DiagnosisRequest):
    """
    AI 诊断单只股票

    - **stock_code**: 股票代码
    - **aspects**: 诊断方面
    """
    try:
        diagnosis = get_diagnosis()
        result = diagnosis.diagnose_stock(
            stock_code=request.stock_code,
            aspects=request.aspects
        )

        return DiagnosisResponse(
            success=True,
            code=result["code"],
            overall_score=result["overall_score"],
            diagnosis=result["diagnosis"],
            created_at=result["created_at"]
        )

    except Exception as e:
        logger.error(f"股票诊断失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/diagnosis/batch", summary="批量股票诊断")
async def batch_diagnosis(
    stocks: List[str],
    aspects: Optional[List[str]] = None
):
    """
    批量 AI 诊断多只股票

    - **stocks**: 股票代码列表
    - **aspects**: 诊断方面
    """
    try:
        diagnosis = get_diagnosis()
        results = diagnosis.batch_diagnosis(stocks, aspects)

        # 统计
        total = len(results)
        with_score = [r for r in results if "overall_score" in r]
        avg_score = sum(r.get("overall_score", 0) for r in with_score) / len(with_score) if with_score else 0

        return {
            "success": True,
            "total": total,
            "completed": len(with_score),
            "avg_score": avg_score,
            "results": results
        }

    except Exception as e:
        logger.error(f"批量诊断失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 启动服务 ==========

if __name__ == "__main__":
    import uvicorn

    logger.info("启动股票推荐服务...")
    uvicorn.run(app, host="0.0.0.0", port=8002)
