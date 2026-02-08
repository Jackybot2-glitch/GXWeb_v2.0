"""
GX量化 Web 统一平台

主应用入口
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.log import logger
from backend.config import config


# 创建 FastAPI 应用
app = FastAPI(
    title="GX量化 Web 统一平台",
    description="集成了股票预测、推荐、策略管理和监控的统一平台",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== 根路径 ==========

@app.get("/")
async def root():
    """服务根路径"""
    return {
        "service": "GX量化 Web 统一平台 v2.0",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


# ========== 路由导入 ==========

# 预测路由
from backend.routes.prediction import app as prediction_app
app.include_router(prediction_app, prefix="/api/v1/prediction", tags=["预测"])

# 选股路由
from backend.routes.selection import app as selection_app
app.include_router(selection_app, prefix="/api/v1/selection", tags=["选股"])

# 行业路由
from backend.routes.industry import app as industry_app
app.include_router(industry_app, prefix="/api/v1/industry", tags=["行业"])

# 策略路由
from backend.routes.strategy import app as strategy_app
app.include_router(strategy_app, prefix="/api/v1/strategy", tags=["策略"])

# 监控路由
from backend.routes.monitoring import app as monitoring_app
app.include_router(monitoring_app, prefix="/api/v1/monitoring", tags=["监控"])


# ========== 启动入口 ==========

if __name__ == "__main__":
    port = config.get("server.port", 8000)
    host = config.get("server.host", "0.0.0.0")

    logger.info(f"GX量化 Web 统一平台启动中...")
    logger.info(f"服务地址: http://{host}:{port}")
    logger.info(f"API文档: http://{host}:{port}/docs")

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
