"""
股票预测服务模块

提供股票价格预测 API 接口
"""

from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from backend.models import ModelRegistry, PredictionResult
from backend.data_loader import get_data_loader
from backend.prediction.storage import get_prediction_storage
from backend.log import logger


# FastAPI 应用
app = FastAPI(
    title="GX量化股票预测服务",
    description="提供股票价格预测功能的 API 服务",
    version="1.0.0"
)


# ========== Pydantic Models ==========

class PredictionRequest(BaseModel):
    """预测请求模型"""
    code: str
    model: str = "naive"
    period: str = "daily"
    parameters: Optional[dict] = None


class PredictionResponse(BaseModel):
    """预测响应模型"""
    success: bool
    code: str
    model: str
    prediction: float
    confidence: float
    period: str
    created_at: str
    metadata: Optional[dict] = None
    error: Optional[str] = None


class ModelInfo(BaseModel):
    """模型信息"""
    name: str
    type: str


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    models_available: List[str]
    timestamp: str


# ========== API Endpoints ==========

@app.get("/", summary="根路径")
async def root():
    """服务根路径"""
    return {
        "service": "GX量化股票预测服务",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health", response_model=HealthResponse, summary="健康检查")
async def health_check():
    """
    健康检查接口

    返回服务状态和可用模型列表
    """
    try:
        models = ModelRegistry.list_models()
        return HealthResponse(
            status="healthy",
            models_available=models,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return HealthResponse(
            status="unhealthy",
            models_available=[],
            timestamp=datetime.now().isoformat()
        )


@app.get("/models", response_model=List[ModelInfo], summary="列出可用模型")
async def list_models():
    """
    列出所有可用的预测模型
    """
    try:
        models = ModelRegistry.list_models()
        return [
            ModelInfo(name=name, type=ModelRegistry.create(name).__class__.__name__)
            for name in models
        ]
    except Exception as e:
        logger.error(f"获取模型列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models/{model_name}/info", summary="获取模型信息")
async def get_model_info(model_name: str):
    """
    获取指定模型的详细信息
    """
    try:
        info = ModelRegistry.get_model_info(model_name)
        return info
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取模型信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/run", response_model=PredictionResponse, summary="执行预测")
async def run_prediction(request: PredictionRequest):
    """
    执行股票价格预测

    - **code**: 股票代码 (如 SH600000)
    - **model**: 预测模型 (naive/moving_average/random_forest)
    - **period**: 数据周期 (daily/1d/1m/5m)
    - **parameters**: 模型特定参数
    """
    try:
        logger.info(f"收到预测请求: {request.code}, 模型: {request.model}")

        # 创建模型
        model = ModelRegistry.create(request.model)

        # 执行预测
        result = model.predict(
            code=request.code,
            period=request.period,
            **(request.parameters or {})
        )

        if result is None:
            raise HTTPException(status_code=500, detail="预测失败")

        # 保存预测结果
        try:
            storage = get_prediction_storage()
            task_id = storage.save_result(request.code, request.model, result)
            result.metadata = result.metadata or {}
            result.metadata["task_id"] = task_id
        except Exception as storage_error:
            logger.warning(f"保存预测结果失败: {storage_error}")
            # 继续返回结果，不因存储失败而中断

        return PredictionResponse(
            success=result.metadata.get("error") is None if result.metadata else True,
            code=result.code,
            model=result.model,
            prediction=result.prediction,
            confidence=result.confidence,
            period=result.period,
            created_at=result.created_at,
            metadata=result.metadata,
            error=result.metadata.get("error") if result.metadata else None
        )

    except ValueError as e:
        logger.error(f"模型不存在: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"预测失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predict/{code}", response_model=PredictionResponse, summary="快速预测")
async def quick_predict(
    code: str,
    model: str = Query("naive", description="预测模型"),
    period: str = Query("daily", description="数据周期")
):
    """
    快速预测接口（GET 方法）

    - **code**: 股票代码
    - **model**: 预测模型
    - **period**: 数据周期
    """
    try:
        prediction_model = ModelRegistry.create(model)
        result = prediction_model.predict(code=code, period=period)

        return PredictionResponse(
            success=result.metadata.get("error") is None if result.metadata else True,
            code=result.code,
            model=result.model,
            prediction=result.prediction,
            confidence=result.confidence,
            period=result.period,
            created_at=result.created_at,
            metadata=result.metadata,
            error=result.metadata.get("error") if result.metadata else None
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"预测失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predict/{code}/result/{task_id}", response_model=PredictionResponse, summary="获取预测结果")
async def get_prediction_result(task_id: str):
    """
    获取预测结果

    根据任务ID获取之前保存的预测结果
    """
    try:
        storage = get_prediction_storage()
        result = storage.get_result(task_id)

        if result is None:
            raise HTTPException(status_code=404, detail=f"预测结果不存在: {task_id}")

        return PredictionResponse(
            success=True,
            code=result.get("code", ""),
            model=result.get("model", ""),
            prediction=result.get("prediction", 0.0),
            confidence=result.get("confidence", 0.0),
            period=result.get("period", ""),
            created_at=result.get("created_at", ""),
            metadata=result.get("metadata", {}),
            error=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取预测结果失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predict/results", response_model=List[PredictionResponse], summary="列出预测结果")
async def list_predictions(
    code: Optional[str] = None,
    model: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100)
):
    """
    列出预测结果

    可按股票代码和模型名称过滤
    """
    try:
        storage = get_prediction_storage()
        results = storage.list_predictions(code=code, model=model, limit=limit)

        return [
            PredictionResponse(
                success=True,
                code=r["code"],
                model=r["model"],
                prediction=r["prediction"],
                confidence=0.0,
                period="",
                created_at=r["created_at"],
                metadata={"task_id": r["task_id"]},
                error=None
            )
            for r in results
        ]

    except Exception as e:
        logger.error(f"列出预测结果失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predict/statistics", summary="获取预测统计")
async def get_statistics():
    """
    获取预测统计信息
    """
    try:
        storage = get_prediction_storage()
        return storage.get_statistics()

    except Exception as e:
        logger.error(f"获取统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predict/{code}/status", summary="预测状态")
async def get_prediction_status(code: str):
    """
    获取预测服务状态

    返回指定股票的预测相关状态信息
    """
    try:
        # 检查模型可用性
        models = ModelRegistry.list_models()

        # 检查数据可用性
        from backend.data_loader import get_data_loader
        loader = get_data_loader()
        kline = loader.load_kline(code, 'daily')

        return {
            "code": code,
            "data_available": len(kline) > 0,
            "data_count": len(kline),
            "models_available": models,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"获取预测状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 启动服务 ==========

if __name__ == "__main__":
    import uvicorn

    logger.info("启动股票预测服务...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
