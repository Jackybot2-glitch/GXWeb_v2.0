"""
GX量化 Web 统一平台 v2.0 - AI 客户端

统一管理 GLM-4.5、DashScope、DeepSeek 三个AI服务
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.config import config
from backend.log import logger


class BaseAIClient(ABC):
    """AI客户端基类"""

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """发送对话请求"""
        pass

    @abstractmethod
    def chat_stream(self, messages: List[Dict[str, str]], **kwargs):
        """流式对话请求"""
        pass


class GLMClient(BaseAIClient):
    """智谱AI GLM-4.5 客户端"""

    BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.BIGMODEL_API_KEY
        self.model = "glm-4.5"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> str:
        """发送对话请求"""
        url = f"{self.BASE_URL}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"]

    def chat_stream(self, messages: List[Dict[str, str]], **kwargs):
        """流式对话请求"""
        # TODO: 实现流式输出
        raise NotImplementedError("流式输出待实现")


class DashScopeClient(BaseAIClient):
    """阿里云 DashScope (Qwen) 客户端"""

    BASE_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.DASHSCOPE_API_KEY
        self.model = "qwen-plus"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> str:
        """发送对话请求"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "input": {
                "messages": messages
            },
            "parameters": {
                "temperature": temperature,
                "max_tokens": max_tokens
            }
        }

        response = requests.post(
            self.BASE_URL,
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()

        result = response.json()
        return result["output"]["text"]

    def chat_stream(self, messages: List[Dict[str, str]], **kwargs):
        """流式对话请求"""
        # TODO: 实现流式输出
        raise NotImplementedError("流式输出待实现")


class DeepSeekClient(BaseAIClient):
    """DeepSeek 客户端"""

    BASE_URL = "https://api.deepseek.com/chat/completions"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.DEEPSEEK_API_KEY
        self.model = "deepseek-chat"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> str:
        """发送对话请求"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        response = requests.post(self.BASE_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"]

    def chat_stream(self, messages: List[Dict[str, str]], **kwargs):
        """流式对话请求"""
        # TODO: 实现流式输出
        raise NotImplementedError("流式输出待实现")


class AIClientManager:
    """
    AI客户端管理器

    提供统一的AI调用接口，支持切换不同服务
    """

    def __init__(self):
        self.clients: Dict[str, BaseAIClient] = {
            "glm": GLMClient(),
            "dashscope": DashScopeClient(),
            "deepseek": DeepSeekClient(),
        }
        self.default_client = "glm"  # 默认使用GLM

    def set_default(self, provider: str):
        """设置默认AI服务"""
        if provider in self.clients:
            self.default_client = provider
            logger.info(f"默认AI服务已切换为: {provider}")

    def chat(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        发送对话请求

        Args:
            messages: 消息列表
            provider: AI服务提供商 ('glm'/'dashscope'/'deepseek')
            **kwargs: 其他参数

        Returns:
            AI生成的文本
        """
        provider = provider or self.default_client
        client = self.clients.get(provider)

        if not client:
            raise ValueError(f"未知的AI服务提供商: {provider}")

        logger.debug(f"调用AI服务: {provider}")
        return client.chat(messages, **kwargs)

    def chat_with_all(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, str]:
        """
        同时调用所有AI服务，返回结果对比

        Returns:
            Dict[provider, response]
        """
        results = {}
        for name, client in self.clients.items():
            try:
                results[name] = client.chat(messages, **kwargs)
            except Exception as e:
                logger.error(f"{name} 调用失败: {e}")
                results[name] = f"Error: {str(e)}"
        return results


# 单例
_ai_manager: Optional[AIClientManager] = None


def get_ai_manager() -> AIClientManager:
    """获取AI客户端管理器单例"""
    global _ai_manager
    if _ai_manager is None:
        _ai_manager = AIClientManager()
    return _ai_manager


# 便捷函数
ai = get_ai_manager()
