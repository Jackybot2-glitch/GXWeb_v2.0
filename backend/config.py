"""
GX量化 Web 统一平台 v2.0 - 统一配置模块

从环境变量和 .env 文件加载配置
"""

import os
from pathlib import Path
from typing import List, Optional
from functools import lru_cache

from dotenv import load_dotenv


# 加载 .env 文件
def load_env_file():
    """加载 .env 文件"""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)


class Config:
    """配置类"""

    def __init__(self):
        load_env_file()

        # ========== API Keys ==========
        self.BIGMODEL_API_KEY: str = os.getenv("BIGMODEL_API_KEY", "")
        self.DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
        self.DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")

        # ========== 服务器配置 ==========
        self.SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))
        self.DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

        # ========== CORS 配置 ==========
        self.CORS_ORIGINS: List[str] = os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:8000"
        ).split(",")

        # ========== 数据库配置 ==========
        self.DATABASE_PATH: Path = Path(os.getenv(
            "DATABASE_PATH",
            "data/gxquant.db"
        ))

        # ========== 数据路径 ==========
        self.QUANTDATA_PATH: Path = Path(os.getenv(
            "QUANTDATA_PATH",
            "/Volumes/高速盘/QuantData"
        ))

        # ========== 日志配置 ==========
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    def validate(self) -> List[str]:
        """
        验证配置是否完整

        Returns:
            缺失的配置项列表
        """
        missing = []

        # 检查必需的 API Keys
        if not self.BIGMODEL_API_KEY:
            missing.append("BIGMODEL_API_KEY (智谱AI)")
        if not self.DASHSCOPE_API_KEY:
            missing.append("DASHSCOPE_API_KEY (阿里云DashScope)")
        if not self.DEEPSEEK_API_KEY:
            missing.append("DEEPSEEK_API_KEY (DeepSeek)")

        return missing

    def is_valid(self) -> bool:
        """检查配置是否有效"""
        return len(self.validate()) == 0


@lru_cache()
def get_config() -> Config:
    """获取配置单例"""
    return Config()


# 便捷访问
config = get_config()
