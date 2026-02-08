"""
策略生成器模块

AI 驱动的量化策略生成
"""

from typing import Dict, Any, Optional
from datetime import datetime

from backend.ai_client import get_ai_manager
from backend.log import logger


class StrategyGenerator:
    """
    策略生成器

    使用 AI 生成量化交易策略
    """

    def __init__(self):
        """初始化策略生成器"""
        self.ai = get_ai_manager()
        logger.info("策略生成器初始化完成")

    def generate_strategy(
        self,
        strategy_type: str = "trend_following",
        parameters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        生成策略

        Args:
            strategy_type: 策略类型
            parameters: 策略参数

        Returns:
            Dict: 策略配置
        """
        if parameters is None:
            parameters = {}

        prompt = f"""
请生成一个{strategy_type}类型的量化交易策略。

要求：
1. 策略逻辑清晰
2. 参数可配置
3. 包含止损止盈
4. 有明确的开仓平仓条件

当前参数：{parameters}

请用JSON格式回复，包含：
- name: 策略名称
- description: 策略描述
- logic: 策略逻辑
- parameters: 参数定义
- entry_rules: 开仓规则
- exit_rules: 平仓规则
- stop_loss: 止损规则
- take_profit: 止盈规则
"""

        try:
            response = self.ai.chat([
                {"role": "system", "content": "你是一个专业的量化交易策略分析师。"},
                {"role": "user", "content": prompt}
            ])

            # 解析AI回复
            strategy = self._parse_strategy(response)

            return {
                "type": strategy_type,
                "strategy": strategy,
                "created_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"策略生成失败: {e}")
            return {
                "type": strategy_type,
                "error": str(e),
                "created_at": datetime.now().isoformat()
            }

    def _parse_strategy(self, response: str) -> Dict[str, Any]:
        """
        解析AI回复

        Args:
            response: AI回复

        Returns:
            Dict: 策略配置
        """
        # TODO: 实现更复杂的解析逻辑
        return {
            "name": "AI Generated Strategy",
            "description": response[:500],
            "logic": "AI generated strategy logic",
            "parameters": {},
            "entry_rules": [],
            "exit_rules": [],
            "stop_loss": 0.05,
            "take_profit": 0.10
        }

    def optimize_strategy(
        self,
        strategy: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        优化策略

        Args:
            strategy: 策略配置
            market_data: 市场数据

        Returns:
            Dict: 优化后的策略
        """
        prompt = f"""
请优化以下量化策略：

策略：{strategy}
市场数据：{market_data}

请分析策略的优缺点，并给出优化建议。

请用JSON格式回复，包含优化后的策略配置。
"""

        try:
            response = self.ai.chat([
                {"role": "system", "content": "你是一个专业的量化策略优化专家。"},
                {"role": "user", "content": prompt}
            ])

            return {
                "original": strategy,
                "optimized": self._parse_strategy(response),
                "created_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"策略优化失败: {e}")
            return {
                "original": strategy,
                "error": str(e),
                "created_at": datetime.now().isoformat()
            }


# 单例模式
_strategy_generator: Optional[StrategyGenerator] = None


def get_strategy_generator() -> StrategyGenerator:
    """获取策略生成器单例"""
    global _strategy_generator
    if _strategy_generator is None:
        _strategy_generator = StrategyGenerator()
    return _strategy_generator
