"""
预测结果存储模块

存储和管理预测结果
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from backend.log import logger
from backend.models import PredictionResult


class PredictionStorage:
    """
    预测结果存储类

    管理预测结果的持久化和查询
    """

    def __init__(self, storage_dir: str = "data/predictions"):
        """
        初始化预测存储

        Args:
            storage_dir: 存储目录
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # 索引文件
        self.index_file = self.storage_dir / "index.json"
        self._ensure_index()

        logger.info(f"预测存储初始化完成: {self.storage_dir}")

    def _ensure_index(self):
        """确保索引文件存在"""
        if not self.index_file.exists():
            self._save_index({})

    def _load_index(self) -> Dict:
        """加载索引"""
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"加载索引失败: {e}")
            return {}

    def _save_index(self, index: Dict):
        """保存索引"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存索引失败: {e}")

    def save_result(
        self,
        code: str,
        model: str,
        result: PredictionResult
    ) -> str:
        """
        保存预测结果

        Args:
            code: 股票代码
            model: 模型名称
            result: 预测结果

        Returns:
            str: 预测任务ID
        """
        # 生成任务ID
        task_id = f"{code}_{model}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 保存结果文件
        result_file = self.storage_dir / f"{task_id}.json"

        try:
            # 转换为字典
            result_dict = {
                "task_id": task_id,
                "code": result.code,
                "model": result.model,
                "prediction": result.prediction,
                "confidence": result.confidence,
                "period": result.period,
                "created_at": result.created_at,
                "metadata": result.metadata or {}
            }

            # 保存文件
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, ensure_ascii=False, indent=2)

            # 更新索引
            index = self._load_index()
            if code not in index:
                index[code] = []
            index[code].append({
                "task_id": task_id,
                "model": model,
                "created_at": result.created_at,
                "prediction": result.prediction
            })
            self._save_index(index)

            logger.info(f"预测结果已保存: {task_id}")
            return task_id

        except Exception as e:
            logger.error(f"保存预测结果失败: {e}")
            raise

    def get_result(self, task_id: str) -> Optional[Dict]:
        """
        获取预测结果

        Args:
            task_id: 任务ID

        Returns:
            Dict: 预测结果，不存在返回None
        """
        result_file = self.storage_dir / f"{task_id}.json"

        if not result_file.exists():
            logger.warning(f"预测结果文件不存在: {task_id}")
            return None

        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"读取预测结果失败: {task_id} - {e}")
            return None

    def get_latest_result(self, code: str, model: Optional[str] = None) -> Optional[Dict]:
        """
        获取最新的预测结果

        Args:
            code: 股票代码
            model: 可选的模型名称

        Returns:
            Dict: 最新的预测结果
        """
        index = self._load_index()

        if code not in index:
            return None

        predictions = index[code]

        if model:
            predictions = [p for p in predictions if p.get("model") == model]

        if not predictions:
            return None

        # 返回最新的
        latest = sorted(predictions, key=lambda x: x.get("created_at", ""), reverse=True)[0]
        return self.get_result(latest["task_id"])

    def list_predictions(
        self,
        code: Optional[str] = None,
        model: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        列出预测结果

        Args:
            code: 可选的股票代码过滤
            model: 可选的模型名称过滤
            limit: 返回数量限制

        Returns:
            List[Dict]: 预测结果列表
        """
        index = self._load_index()
        results = []

        for stock_code, predictions in index.items():
            if code and stock_code != code:
                continue

            for pred in predictions:
                if model and pred.get("model") != model:
                    continue
                results.append({
                    "code": stock_code,
                    "task_id": pred["task_id"],
                    "model": pred["model"],
                    "created_at": pred["created_at"],
                    "prediction": pred["prediction"]
                })

        # 按时间倒序
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return results[:limit]

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取预测统计信息

        Returns:
            Dict: 统计信息
        """
        index = self._load_index()

        total_predictions = sum(len(preds) for preds in index.values())
        unique_stocks = len(index)
        models_used = set()

        for preds in index.values():
            for pred in preds:
                models_used.add(pred.get("model", "unknown"))

        return {
            "total_predictions": total_predictions,
            "unique_stocks": unique_stocks,
            "models_available": list(models_used),
            "timestamp": datetime.now().isoformat()
        }


# 单例模式
_prediction_storage: Optional[PredictionStorage] = None


def get_prediction_storage() -> PredictionStorage:
    """获取预测存储单例"""
    global _prediction_storage
    if _prediction_storage is None:
        _prediction_storage = PredictionStorage()
    return _prediction_storage
