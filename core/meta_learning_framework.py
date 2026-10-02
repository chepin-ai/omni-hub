"""
OMNI-HUB v193 — MetaLearningFramework
元学习框架

核心功能：
1. MetaOptimizer          — 元优化器
2. HyperparameterSearch   — 超参数搜索
3. StrategySelector       — 策略选择器
4. TransferLearning       — 迁移学习
5. MetaMemory             — 元记忆
6. MetaLearningFramework  — 统合引擎

映射：
- 元学习 = paramparā（传承）
- 优化 = saṃskāra（完善）
- 迁移 = saṅkramaṇa（转移）
"""

from __future__ import annotations

import hashlib
import json
import time
import math
from collections import deque, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Any


# ═══════════════════════════════════════════════════════════════
# 枚举与常量
# ═══════════════════════════════════════════════════════════════

class MetaStrategy(Enum):
    """元策略"""
    GRID_SEARCH = 0
    RANDOM_SEARCH = 1
    BAYESIAN = 2
    EVOLUTIONARY = 3
    GRADIENT_BASED = 4


class TransferMode(Enum):
    """迁移模式"""
    NONE = 0
    ZERO_SHOT = 1
    FEW_SHOT = 2
    FINE_TUNE = 3
    ADAPTER = 4


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class HyperparameterSpace:
    """超参数空间"""
    name: str
    param_type: str  # float, int, categorical
    low: float = 0.0
    high: float = 1.0
    choices: List[Any] = field(default_factory=list)


@dataclass
class Trial:
    """试验"""
    trial_id: str
    params: Dict[str, Any]
    score: float
    timestamp: float
    strategy: MetaStrategy


@dataclass
class MetaExperience:
    """元经验"""
    exp_id: str
    task: str
    source_params: Dict[str, Any]
    target_params: Dict[str, Any]
    improvement: float
    transfer_mode: TransferMode


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 元优化器
# ═══════════════════════════════════════════════════════════════

class MetaOptimizer:
    """元优化器 — 优化优化过程本身"""

    def __init__(self):
        self.optimization_history: deque = deque(maxlen=500)
        self.best_params: Dict[str, Any] = {}
        self.best_score = float('-inf')

    def suggest(self, space: Dict[str, HyperparameterSpace],
                strategy: MetaStrategy = MetaStrategy.BAYESIAN) -> Dict[str, Any]:
        """建议下一组参数"""
        params = {}
        for name, hp in space.items():
            if hp.param_type == "categorical" and hp.choices:
                params[name] = hp.choices[hash(f"{name}:{time.time()}") % len(hp.choices)]
            elif hp.param_type == "int":
                params[name] = int(hp.low + (hash(f"{name}:{time.time()}") % 1000) / 1000.0 * (hp.high - hp.low))
            else:
                params[name] = hp.low + (hash(f"{name}:{time.time()}") % 1000) / 1000.0 * (hp.high - hp.low)
        return params

    def evaluate(self, params: Dict[str, Any], score: float):
        """评估参数效果"""
        self.optimization_history.append({
            "params": params,
            "score": score,
            "timestamp": time.time()
        })
        if score > self.best_score:
            self.best_score = score
            self.best_params = dict(params)

    def get_report(self) -> Dict:
        return {
            "trials": len(self.optimization_history),
            "best_score": self.best_score,
            "best_params": self.best_params,
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 超参数搜索
# ═══════════════════════════════════════════════════════════════

class HyperparameterSearch:
    """超参数搜索"""

    def __init__(self):
        self.trials: deque = deque(maxlen=300)
        self.search_spaces: Dict[str, Dict[str, HyperparameterSpace]] = {}

    def define_space(self, task: str, space: Dict[str, HyperparameterSpace]):
        self.search_spaces[task] = space

    def search(self, task: str, objective: Callable[[Dict], float],
               n_trials: int = 20, strategy: MetaStrategy = MetaStrategy.RANDOM_SEARCH) -> Trial:
        """搜索最优超参数"""
        space = self.search_spaces.get(task, {})
        best_trial = None
        best_score = float('-inf')

        for i in range(n_trials):
            if strategy == MetaStrategy.GRID_SEARCH:
                params = self._grid_sample(space, i, n_trials)
            elif strategy == MetaStrategy.RANDOM_SEARCH:
                params = self._random_sample(space)
            else:
                params = self._random_sample(space)

            try:
                score = objective(params)
            except Exception:
                score = 0.0

            trial = Trial(
                trial_id=f"{task}_trial_{i}_{int(time.time()*1000)}",
                params=params,
                score=score,
                timestamp=time.time(),
                strategy=strategy
            )
            self.trials.append(trial)

            if score > best_score:
                best_score = score
                best_trial = trial

        return best_trial

    def _random_sample(self, space: Dict[str, HyperparameterSpace]) -> Dict[str, Any]:
        params = {}
        for name, hp in space.items():
            if hp.param_type == "categorical" and hp.choices:
                idx = abs(hash(f"{name}:{time.time()}:{id(hp)}")) % len(hp.choices)
                params[name] = hp.choices[idx]
            elif hp.param_type == "int":
                params[name] = int(hp.low + abs(hash(f"{name}:{time.time()}")) % 1000 / 1000.0 * (hp.high - hp.low))
            else:
                params[name] = hp.low + abs(hash(f"{name}:{time.time()}")) % 1000 / 1000.0 * (hp.high - hp.low)
        return params

    def _grid_sample(self, space: Dict[str, HyperparameterSpace], idx: int, total: int) -> Dict[str, Any]:
        params = {}
        for name, hp in space.items():
            ratio = idx / max(1, total - 1)
            if hp.param_type == "int":
                params[name] = int(hp.low + ratio * (hp.high - hp.low))
            else:
                params[name] = hp.low + ratio * (hp.high - hp.low)
        return params

    def get_report(self) -> Dict:
        if not self.trials:
            return {"trials": 0}
        scores = [t.score for t in self.trials]
        return {
            "trials": len(self.trials),
            "avg_score": sum(scores) / len(scores),
            "best_score": max(scores),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 策略选择器
# ═══════════════════════════════════════════════════════════════

class StrategySelector:
    """策略选择器 — 选择最优元策略"""

    def __init__(self):
        self.strategy_performance: Dict[MetaStrategy, List[float]] = defaultdict(list)
        self.selection_history: deque = deque(maxlen=200)

    def select(self, task_features: Dict[str, float]) -> MetaStrategy:
        """根据任务特征选择策略"""
        # 基于历史性能选择
        best_strategy = MetaStrategy.RANDOM_SEARCH
        best_avg = float('-inf')

        for strategy, scores in self.strategy_performance.items():
            if scores:
                avg = sum(scores) / len(scores)
                if avg > best_avg:
                    best_avg = avg
                    best_strategy = strategy

        self.selection_history.append({
            "task_features": task_features,
            "selected": best_strategy.name,
            "timestamp": time.time()
        })
        return best_strategy

    def report_performance(self, strategy: MetaStrategy, score: float):
        self.strategy_performance[strategy].append(score)
        # 保持最近50个
        if len(self.strategy_performance[strategy]) > 50:
            self.strategy_performance[strategy] = self.strategy_performance[strategy][-50:]

    def get_report(self) -> Dict:
        return {
            "strategies_tested": len(self.strategy_performance),
            "selections": len(self.selection_history),
            "performance": {k.name: sum(v)/max(1,len(v)) for k, v in self.strategy_performance.items()},
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 迁移学习
# ═══════════════════════════════════════════════════════════════

class TransferLearning:
    """迁移学习 — saṅkramaṇa"""

    def __init__(self):
        self.experiences: deque = deque(maxlen=200)
        self.task_embeddings: Dict[str, List[float]] = {}

    def embed_task(self, task: str, features: List[float]):
        self.task_embeddings[task] = features

    def compute_similarity(self, task_a: str, task_b: str) -> float:
        """计算任务相似度（余弦相似度）"""
        a = self.task_embeddings.get(task_a, [])
        b = self.task_embeddings.get(task_b, [])
        if not a or not b or len(a) != len(b):
            return 0.0

        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def transfer(self, source_task: str, target_task: str,
                 source_params: Dict[str, Any], mode: TransferMode = TransferMode.FEW_SHOT) -> Dict[str, Any]:
        """迁移参数"""
        similarity = self.compute_similarity(source_task, target_task)

        if mode == TransferMode.ZERO_SHOT:
            transferred = dict(source_params)
        elif mode == TransferMode.FEW_SHOT:
            transferred = {k: v * (0.5 + 0.5 * similarity) for k, v in source_params.items()}
        elif mode == TransferMode.FINE_TUNE:
            transferred = {k: v + (hash(k) % 100 / 1000.0 - 0.05) for k, v in source_params.items()}
        else:
            transferred = dict(source_params)

        exp = MetaExperience(
            exp_id=f"transfer_{int(time.time()*1000)}",
            task=f"{source_task}->{target_task}",
            source_params=source_params,
            target_params=transferred,
            improvement=similarity,
            transfer_mode=mode
        )
        self.experiences.append(exp)
        return transferred

    def get_report(self) -> Dict:
        return {
            "experiences": len(self.experiences),
            "tasks_embedded": len(self.task_embeddings),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 元记忆
# ═══════════════════════════════════════════════════════════════

class MetaMemory:
    """元记忆 — 跨任务记忆"""

    def __init__(self):
        self.memories: deque = deque(maxlen=500)
        self.task_index: Dict[str, List[Dict]] = defaultdict(list)

    def store(self, task: str, params: Dict[str, Any], score: float,
              context: Dict = None):
        memory = {
            "task": task,
            "params": params,
            "score": score,
            "context": context or {},
            "timestamp": time.time()
        }
        self.memories.append(memory)
        self.task_index[task].append(memory)

    def recall(self, task: str, top_k: int = 3) -> List[Dict]:
        """回忆某任务的最佳记忆"""
        memories = self.task_index.get(task, [])
        sorted_mem = sorted(memories, key=lambda x: x["score"], reverse=True)
        return sorted_mem[:top_k]

    def recall_similar(self, task_features: List[float], top_k: int = 3) -> List[Dict]:
        """回忆相似任务的记忆"""
        # 简化：按分数返回最好的
        all_mem = list(self.memories)
        return sorted(all_mem, key=lambda x: x["score"], reverse=True)[:top_k]

    def get_report(self) -> Dict:
        return {
            "memories": len(self.memories),
            "tasks": len(self.task_index),
        }


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — MetaLearningFramework v193
# ═══════════════════════════════════════════════════════════════

class MetaLearningFramework:
    """
    OMNI-HUB v193 元学习框架

    paramparā · saṃskāra · saṅkramaṇa — 传承、完善、转移
    """

    VERSION = "193.0.0"

    def __init__(self):
        self.optimizer = MetaOptimizer()
        self.search = HyperparameterSearch()
        self.selector = StrategySelector()
        self.transfer = TransferLearning()
        self.memory = MetaMemory()

        self.cycle_count = 0
        self.event_log: deque = deque(maxlen=10000)

    def optimize_module(self, module_name: str, param_space: Dict[str, HyperparameterSpace],
                        evaluator: Callable[[Dict], float]) -> Trial:
        """优化模块参数"""
        # 1. 选择策略
        strategy = self.selector.select({"module": hash(module_name) % 100 / 100.0})

        # 2. 搜索
        self.search.define_space(module_name, param_space)
        best_trial = self.search.search(module_name, evaluator, n_trials=10, strategy=strategy)

        # 3. 存储记忆
        self.memory.store(module_name, best_trial.params, best_trial.score)

        # 4. 报告性能
        self.selector.report_performance(strategy, best_trial.score)

        return best_trial

    def transfer_knowledge(self, source_task: str, target_task: str,
                           source_params: Dict[str, Any]) -> Dict[str, Any]:
        """迁移知识"""
        return self.transfer.transfer(source_task, target_task, source_params)

    def recall_best_practice(self, task: str) -> Optional[Dict]:
        """回忆最佳实践"""
        memories = self.memory.recall(task, top_k=1)
        return memories[0] if memories else None

    def run_cycle(self, module_states: Dict[str, Dict] = None) -> Dict:
        """运行元学习周期"""
        self.cycle_count += 1
        module_states = module_states or {}

        # 为每个模块定义优化空间并搜索
        improvements = {}
        for module, state in list(module_states.items())[:3]:
            space = {
                "learning_rate": HyperparameterSpace("lr", "float", 0.001, 0.1),
                "momentum": HyperparameterSpace("momentum", "float", 0.0, 0.99),
            }

            def evaluator(params):
                health = state.get("health", 0.5)
                return health * (1 - params.get("learning_rate", 0.01))

            best = self.optimize_module(module, space, evaluator)
            improvements[module] = {
                "best_score": best.score,
                "best_params": best.params,
                "strategy": best.strategy.name
            }

        summary = {
            "cycle": self.cycle_count,
            "modules_optimized": len(improvements),
            "improvements": improvements,
        }

        self.event_log.append(summary)
        return summary

    def get_status(self) -> Dict:
        return {
            "version": self.VERSION,
            "cycle_count": self.cycle_count,
            "optimizer": self.optimizer.get_report(),
            "search": self.search.get_report(),
            "selector": self.selector.get_report(),
            "transfer": self.transfer.get_report(),
            "memory": self.memory.get_report(),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_mlf_instance: Optional[MetaLearningFramework] = None


def get_meta_learning_framework() -> MetaLearningFramework:
    global _mlf_instance
    if _mlf_instance is None:
        _mlf_instance = MetaLearningFramework()
    return _mlf_instance


if __name__ == "__main__":
    mlf = MetaLearningFramework()
    print(f"MetaLearningFramework v{mlf.VERSION} initialized")
    print(f"Status: {json.dumps(mlf.get_status(), indent=2, default=str)}")
