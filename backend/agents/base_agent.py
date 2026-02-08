"""
AI智能体基类模块

提供统一的智能体接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

from backend.ai_client import get_ai_manager
from backend.log import logger


class BaseAgent(ABC):
    """
    AI智能体基类

    所有智能体的父类
    """

    def __init__(self, name: str, description: str):
        """
        初始化智能体

        Args:
            name: 智能体名称
            description: 智能体描述
        """
        self.name = name
        self.description = description
        self.ai = get_ai_manager()
        logger.info(f"智能体初始化: {name}")

    @abstractmethod
    def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析输入数据

        Args:
            input_data: 输入数据

        Returns:
            Dict: 分析结果
        """
        pass

    def _call_ai(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        调用AI

        Args:
            prompt: 用户提示
            system_prompt: 系统提示

        Returns:
            str: AI响应
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.ai.chat(messages)
            return response
        except Exception as e:
            logger.error(f"AI调用失败: {self.name} - {e}")
            raise

    def get_info(self) -> Dict[str, Any]:
        """
        获取智能体信息

        Returns:
            Dict: 智能体信息
        """
        return {
            "name": self.name,
            "description": self.description,
            "type": self.__class__.__name__
        }
