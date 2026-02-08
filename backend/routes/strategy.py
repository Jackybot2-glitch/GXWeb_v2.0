"""
策略管理路由模块

提供策略生成和回测接口
"""

from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from backend.strategy.generator import get_strategy_generator
from backend.strategy.backtest import BacktestEngine
from backend.data_loader import get_data_loader
from backend.log import logger


# FastAPI 应用
app = FastAPI(
    title="GX量化策略管理服务",
    description="提供策略生成、回测和绩效评估的 API 服务",
    version="1.0.0"
)


# ========== Pydantic Models ==========

class StrategyRequest(BaseModel):
    """策略生成请求"""
    strategy_type: str = "trend_following"
    parameters: Optional[dict] = None


class StrategyResponse(BaseModel):
    """策略生成响应"""
    success: bool
    type: str
    strategy: dict
    created_at: str


class BacktestRequest(BaseModel):
    """回测请求"""
    strategy: dict
    symbol: str = "SH600000"
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class BacktestMetrics(BaseModel):
    """回测绩效指标"""
    initial_capital: float
    final_value: float
    total_return: float
    total_trades: int
    win_rate: float
    max_drawdown: float
    sharpe_ratio: float


class BacktestResponse(BaseModel):
    """回测响应"""
    success: bool
    symbol: str
    trades_count: int
    final_value: float
    metrics: BacktestMetrics
    created_at: str


# ========== API Endpoints ==========

@app.get("/", summary="根路径")
async def root():
    """服务根路径"""
    return {
        "service": "GX量化策略管理服务",
        "version": "1.0.0",
        "status": "running"
    }


@app.post("/strategy/create", response_model=StrategyResponse, summary="创建策略")
async def create_strategy(request: StrategyRequest):
    """
    使用 AI 创建量化策略

    - **strategy_type**: 策略类型 (趋势跟踪/均值回归/突破交易等)
    - **parameters**: 策略参数
    """
    try:
        generator = get_strategy_generator()
        result = generator.generate_strategy(
            strategy_type=request.strategy_type,
            parameters=request.parameters
        )

        return StrategyResponse(
            success="error" not in result,
            type=result["type"],
            strategy=result.get("strategy", {}),
            created_at=result["created_at"]
        )

    except Exception as e:
        logger.error(f"策略创建失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/strategy/optimize", summary="优化策略")
async def optimize_strategy(
    strategy: dict,
    symbol: str = Query("SH600000", description="股票代码")
):
    """
    优化现有策略

    - **strategy**: 策略配置
    - **symbol**: 股票代码（用于获取市场数据）
    """
    try:
        generator = get_strategy_generator()

        # 获取市场数据
        loader = get_data_loader()
        price_data = loader.load_kline(symbol, "daily")

        if price_data.empty:
            raise HTTPException(status_code=400, detail="无法获取市场数据")

        market_data = price_data.tail(100).to_dict(orient="records")

        result = generator.optimize_strategy(strategy, {"price_data": market_data})

        return {
            "success": "error" not in result,
            "original": result.get("original"),
            "optimized": result.get("optimized"),
            "created_at": result["created_at"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"策略优化失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/strategy/backtest", response_model=BacktestResponse, summary="执行回测")
async def run_backtest(request: BacktestRequest):
    """
    执行策略回测

    - **strategy**: 策略配置
    - **symbol**: 股票代码
    - **start_date**: 开始日期
    - **end_date**: 结束日期
    """
    try:
        # 获取市场数据
        loader = get_data_loader()
        price_data = loader.load_kline(
            request.symbol,
            "daily",
            start_date=request.start_date,
            end_date=request.end_date
        )

        if price_data.empty:
            raise HTTPException(status_code=400, detail="无法获取市场数据")

        # 执行回测
        engine = BacktestEngine(initial_capital=100000)
        result = engine.run_backtest(
            strategy=request.strategy,
            price_data=price_data.to_dict(orient="records"),
            symbol=request.symbol
        )

        metrics = result["metrics"]

        return BacktestResponse(
            success=True,
            symbol=request.symbol,
            trades_count=len(result["trades"]),
            final_value=metrics["final_value"],
            metrics=BacktestMetrics(
                initial_capital=metrics["initial_capital"],
                final_value=metrics["final_value"],
                total_return=metrics["total_return"],
                total_trades=metrics["total_trades"],
                win_rate=metrics["win_rate"],
                max_drawdown=metrics["max_drawdown"],
                sharpe_ratio=metrics["sharpe_ratio"]
            ),
            created_at=result["created_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"回测失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/strategy/result/{task_id}", summary="获取回测结果")
async def get_backtest_result(task_id: str):
    """
    获取历史回测结果

    预留接口
    """
    # TODO: 实现历史回测结果查询
    raise HTTPException(status_code=501, detail="历史回测结果功能待实现")


# ========== 启动服务 ==========

if __name__ == "__main__":
    import uvicorn

    logger.info("启动策略管理服务...")
    uvicorn.run(app, host="0.0.0.0", port=8004)
