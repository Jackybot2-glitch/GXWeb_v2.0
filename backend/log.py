"""
GX量化 Web 统一平台 v2.0 - 日志配置模块

提供统一的日志配置和初始化
"""

import sys
from pathlib import Path
from loguru import logger
from datetime import datetime


def setup_logging(
    log_dir: Path = Path("logs"),
    log_level: str = "INFO",
    rotation: str = "20 MB",
    retention: str = "7 days",
    format_string: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{message}</cyan>"
    )
):
    """
    配置日志系统

    Args:
        log_dir: 日志文件目录
        log_level: 日志级别（DEBUG/INFO/WARNING/ERROR）
        rotation: 日志文件轮转大小
        retention: 日志保留时间
        format_string: 日志格式
    """
    # 确保日志目录存在
    log_dir.mkdir(parents=True, exist_ok=True)

    # 获取当前日期用于文件名
    today = datetime.now().strftime("%Y-%m-%d")

    # 移除默认的 stderr 输出
    logger.remove()

    # 添加控制台输出
    logger.add(
        sys.stderr,
        level=log_level,
        format=format_string,
        colorize=True
    )

    # 添加文件输出（按日期）
    logger.add(
        log_dir / f"app_{today}.log",
        level=log_level,
        format=format_string,
        rotation=rotation,
        retention=retention,
        encoding="utf-8"
    )

    # 添加错误日志文件（只记录 ERROR 及以上）
    logger.add(
        log_dir / f"error_{today}.log",
        level="ERROR",
        format=format_string,
        rotation=rotation,
        retention=retention,
        encoding="utf-8"
    )

    return logger


# 初始化日志（使用配置中的设置）
from backend.config import config
setup_logging(
    log_dir=Path("logs"),
    log_level=config.LOG_LEVEL
)
