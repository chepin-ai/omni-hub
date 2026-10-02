"""
OMNI-HUB v188 — AdaptiveLearningEngine
自适应学习引擎

核心功能：
1. DefenseStrategyPool      — 防御策略池
2. PatternLearner           — 模式学习器
3. AnomalyDetector          — 异常检测器
4. AutoTuner                — 自动调优器
5. FeedbackLoop             — 反馈回路
6. AdaptiveLearningEngine   — 统合引擎

映射：
- 学习 = śikṣā（学）
- 适应 = yogyatā（适应性）
- 模式 = saṃskāra（行蕴/习气）
"""

from __future__ import annotations

import hashlib
import json
import time
import math
from collections import deque, Counter
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Callable


# ═══════════════════════════════════════════════════════════════
# 枚举与常量
# ═══════════════════════════════════════════════════════════════

class StrategyType(Enum):
    """策略类型"""
    FILTER = 0          # 过滤
    ISOLATE = 1         # 隔离
    REDUNDANCY = 2      # 冗余
    DELAY = 3           # 延迟
    ENCRYPT = 4         # 加密
    QUARANTINE = 5      # 检疫


class PatternClass(Enum):
    """模式类别"""
    NORMAL = 0
    ANOMALY = 1
    ATTACK = 2
    DRIFT = 3
    EMERGENCE = 4


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class DefenseStrategy:
    """防御策略"""
    strategy_id: str
    name: str
    strategy_type: StrategyType
    target_attack: str
    effectiveness: float
    cost: float
    usage_count: int = 0
    success_count: int = 0
    created_at: float = field(default_factory=time.time)


@dataclass
class LearnedPattern:
    """学习到的模式"""
    pattern_id: str
    features: Tuple[Any, ...]
    pattern_class: PatternClass
    confidence: float
    frequency: int = 1
    last_seen: float = field(default_factory=time.time)


@dataclass
class AnomalyRecord:
    """异常记录"""
    anomaly_id: str
    module_id: str
    feature_vector: List[float]
    anomaly_score: float
    timestamp: float
    confirmed: bool = False


@dataclass
class TuningAction:
    """调优动作"""
    action_id: str
    parameter: str
    old_value: float
    new_value: float
    expected_improvement: float
    timestamp: float


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 防御策略池
# ═══════════════════════════════════════════════════════════════

class DefenseStrategyPool:
    """防御策略池 — 存储和管理防御策略"""

    DEFAULT_STRATEGIES = [
        ("strat_filter", "Filter Suspicious", StrategyType.FILTER, "HALLUCINATION", 0.7, 0.3),
        ("strat_isolate", "Isolate Node", StrategyType.ISOLATE, "BYZANTINE", 0.8, 0.6),
        ("strat_redundant", "Triple Redundancy", StrategyType.REDUNDANCY, "DECAY", 0.6, 0.5),
        ("strat_delay", "Delay Execution", StrategyType.DELAY, "CONTRADICTION", 0.5, 0.2),
        ("strat_encrypt", "Encrypt Channel", StrategyType.ENCRYPT, "SYBIL", 0.75, 0.4),
        ("strat_quarantine", "Quarantine Module", StrategyType.QUARANTINE, "ECLIPSE", 0.85, 0.7),
    ]

    def __init__(self):
        self.strategies: Dict[str, DefenseStrategy] = {}
        self._init_defaults()

    def _init_defaults(self):
        for sid, name, stype, target, eff, cost in self.DEFAULT_STRATEGIES:
            self.strategies[sid] = DefenseStrategy(
                strategy_id=sid, name=name, strategy_type=stype,
                target_attack=target, effectiveness=eff, cost=cost
            )

    def add(self, strategy: DefenseStrategy):
        self.strategies[strategy.strategy_id] = strategy

    def select_for_attack(self, attack_type: str) -> Optional[DefenseStrategy]:
        """为特定攻击选择最佳策略"""
        candidates = [s for s in self.strategies.values()
                      if s.target_attack == attack_type or s.target_attack == "ANY"]
        if not candidates:
            return None
        # 按效果/成本比排序
        candidates.sort(key=lambda s: (s.effectiveness * s.success_count / max(1, s.usage_count)) / max(0.01, s.cost),
                       reverse=True)
        return candidates[0]

    def report_outcome(self, strategy_id: str, success: bool):
        if strategy_id in self.strategies:
            self.strategies[strategy_id].usage_count += 1
            if success:
                self.strategies[strategy_id].success_count += 1
            # 更新效果
            s = self.strategies[strategy_id]
            s.effectiveness = s.success_count / max(1, s.usage_count)

    def evolve(self, attack_history: List[Dict]) -> List[DefenseStrategy]:
        """基于攻击历史进化策略"""
        new_strategies = []
        attack_counts = Counter(a.get("attack_type", "UNKNOWN") for a in attack_history)
        for attack_type, count in attack_counts.most_common(3):
            existing = [s for s in self.strategies.values() if s.target_attack == attack_type]
            if not existing or max(s.effectiveness for s in existing) < 0.8:
                # 创建新策略变体
                sid = f"strat_evolved_{attack_type.lower()}_{int(time.time()*1000)}"
                new_s = DefenseStrategy(
                    strategy_id=sid,
                    name=f"Evolved {attack_type} Defense",
                    strategy_type=random.choice(list(StrategyType)),
                    target_attack=attack_type,
                    effectiveness=0.6,
                    cost=0.4,
                )
                self.strategies[sid] = new_s
                new_strategies.append(new_s)
        return new_strategies

    def get_report(self) -> Dict:
        if not self.strategies:
            return {"strategies": 0}
        return {
            "strategies": len(self.strategies),
            "avg_effectiveness": sum(s.effectiveness for s in self.strategies.values()) / len(self.strategies),
            "best_strategy": max(self.strategies.items(), key=lambda x: x[1].effectiveness)[0],
        }


import random  # for evolve method


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 模式学习器
# ═══════════════════════════════════════════════════════════════

class PatternLearner:
    """模式学习器 — śikṣā"""

    def __init__(self, similarity_threshold: float = 0.9):
        self.patterns: Dict[str, LearnedPattern] = {}
        self.similarity_threshold = similarity_threshold
        self.pattern_counter = 0

    def _vectorize(self, data: Dict) -> Tuple[Any, ...]:
        """将数据向量化"""
        keys = sorted(data.keys())
        return tuple((k, round(data[k], 3) if isinstance(data[k], float) else data[k]) for k in keys if not isinstance(data[k], (dict, list)))

    def _similarity(self, f1: Tuple, f2: Tuple) -> float:
        """计算特征相似度"""
        if len(f1) != len(f2):
            return 0.0
        matches = sum(1 for a, b in zip(f1, f2) if a == b)
        return matches / max(1, len(f1))

    def learn(self, data: Dict, pattern_class: PatternClass = PatternClass.NORMAL) -> LearnedPattern:
        """学习新模式"""
        features = self._vectorize(data)

        # 查找相似模式
        for p in self.patterns.values():
            if self._similarity(p.features, features) >= self.similarity_threshold:
                p.frequency += 1
                p.last_seen = time.time()
                # 贝叶斯更新置信度
                p.confidence = (p.confidence * p.frequency + (1.0 if pattern_class == p.pattern_class else 0.0)) / (p.frequency + 1)
                return p

        # 创建新模式
        self.pattern_counter += 1
        pid = f"pattern_{self.pattern_counter}_{int(time.time()*1000)}"
        pattern = LearnedPattern(
            pattern_id=pid,
            features=features,
            pattern_class=pattern_class,
            confidence=0.5,
            frequency=1,
        )
        self.patterns[pid] = pattern
        return pattern

    def classify(self, data: Dict) -> Tuple[PatternClass, float]:
        """分类数据"""
        features = self._vectorize(data)
        best_match = None
        best_sim = 0.0

        for p in self.patterns.values():
            sim = self._similarity(p.features, features)
            if sim > best_sim:
                best_sim = sim
                best_match = p

        if best_match and best_sim >= self.similarity_threshold:
            return best_match.pattern_class, best_match.confidence * best_sim
        return PatternClass.ANOMALY, 0.3

    def get_report(self) -> Dict:
        class_counts = {}
        for p in self.patterns.values():
            class_counts[p.pattern_class.name] = class_counts.get(p.pattern_class.name, 0) + 1
        return {
            "patterns": len(self.patterns),
            "class_distribution": class_counts,
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 异常检测器
# ═══════════════════════════════════════════════════════════════

class AnomalyDetector:
    """异常检测器"""

    def __init__(self, z_threshold: float = 2.5):
        self.z_threshold = z_threshold
        self.baseline: Dict[str, deque] = {}  # metric -> history
        self.anomalies: deque = deque(maxlen=500)
        self.baseline_window = 50

    def update_baseline(self, module_id: str, metrics: Dict[str, float]):
        """更新基线"""
        for metric, value in metrics.items():
            key = f"{module_id}:{metric}"
            if key not in self.baseline:
                self.baseline[key] = deque(maxlen=self.baseline_window)
            self.baseline[key].append(value)

    def detect(self, module_id: str, metrics: Dict[str, float]) -> List[AnomalyRecord]:
        """检测异常"""
        detected = []
        for metric, value in metrics.items():
            key = f"{module_id}:{metric}"
            history = self.baseline.get(key)
            if not history or len(history) < 5:
                continue

            mean = sum(history) / len(history)
            variance = sum((x - mean) ** 2 for x in history) / len(history)
            std = math.sqrt(variance) if variance > 0 else 0.001

            z_score = abs(value - mean) / std
            if z_score > self.z_threshold:
                anomaly = AnomalyRecord(
                    anomaly_id=f"anom_{key}_{int(time.time()*1000)}",
                    module_id=module_id,
                    feature_vector=[value, mean, std],
                    anomaly_score=min(1.0, z_score / 5.0),
                    timestamp=time.time(),
                )
                self.anomalies.append(anomaly)
                detected.append(anomaly)

        return detected

    def confirm(self, anomaly_id: str):
        for a in self.anomalies:
            if a.anomaly_id == anomaly_id:
                a.confirmed = True
                return True
        return False

    def get_report(self) -> Dict:
        confirmed = sum(1 for a in self.anomalies if a.confirmed)
        return {
            "total_anomalies": len(self.anomalies),
            "confirmed": confirmed,
            "false_positives": len(self.anomalies) - confirmed,
            "metrics_tracked": len(self.baseline),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 自动调优器
# ═══════════════════════════════════════════════════════════════

class AutoTuner:
    """自动调优器"""

    def __init__(self, learning_rate: float = 0.1):
        self.learning_rate = learning_rate
        self.parameters: Dict[str, float] = {}
        self.history: deque = deque(maxlen=200)
        self.tuning_log: deque = deque(maxlen=500)

    def register(self, param_name: str, initial_value: float, min_val: float = 0.0, max_val: float = 1.0):
        self.parameters[param_name] = {
            "value": initial_value,
            "min": min_val,
            "max": max_val,
            "gradient": 0.0,
        }

    def feedback(self, param_name: str, performance_delta: float):
        """接收性能反馈"""
        if param_name not in self.parameters:
            return
        # 简单梯度下降
        self.parameters[param_name]["gradient"] = performance_delta
        self.history.append({
            "param": param_name,
            "performance_delta": performance_delta,
            "time": time.time(),
        })

    def tune(self) -> List[TuningAction]:
        """执行调优"""
        actions = []
        for name, config in self.parameters.items():
            grad = config["gradient"]
            if abs(grad) < 0.01:
                continue

            old_val = config["value"]
            new_val = old_val + self.learning_rate * grad
            new_val = max(config["min"], min(config["max"], new_val))

            if abs(new_val - old_val) > 0.001:
                action = TuningAction(
                    action_id=f"tune_{name}_{int(time.time()*1000)}",
                    parameter=name,
                    old_value=old_val,
                    new_value=new_val,
                    expected_improvement=grad,
                    timestamp=time.time()
                )
                config["value"] = new_val
                config["gradient"] = 0.0
                self.tuning_log.append(action)
                actions.append(action)

        return actions

    def get_report(self) -> Dict:
        return {
            "parameters": len(self.parameters),
            "tuning_actions": len(self.tuning_log),
            "recent_actions": len([a for a in self.tuning_log if a.timestamp > time.time() - 3600]),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 反馈回路
# ═══════════════════════════════════════════════════════════════

class FeedbackLoop:
    """反馈回路 — 连接攻击→防御→学习的循环"""

    def __init__(self):
        self.cycles: deque = deque(maxlen=500)
        self.effectiveness_history: deque = deque(maxlen=1000)

    def record_cycle(self, attack_type: str, strategy_id: str, detected: bool,
                    contained: bool, impact: float):
        """记录一个完整的攻防周期"""
        self.cycles.append({
            "attack_type": attack_type,
            "strategy_id": strategy_id,
            "detected": detected,
            "contained": contained,
            "impact": impact,
            "time": time.time(),
        })

        # 计算该周期的有效性
        effectiveness = (float(detected) * 0.4 + float(contained) * 0.4 + (1.0 - impact) * 0.2)
        self.effectiveness_history.append(effectiveness)

    def get_trend(self) -> Tuple[float, str]:
        """获取有效性趋势"""
        if len(self.effectiveness_history) < 5:
            return 0.5, "INSUFFICIENT_DATA"

        recent = list(self.effectiveness_history)[-10:]
        older = list(self.effectiveness_history)[-20:-10] if len(self.effectiveness_history) >= 20 else recent[:5]

        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)

        diff = recent_avg - older_avg
        if diff > 0.1:
            return recent_avg, "IMPROVING"
        elif diff < -0.1:
            return recent_avg, "DEGRADING"
        else:
            return recent_avg, "STABLE"

    def get_report(self) -> Dict:
        trend, label = self.get_trend()
        return {
            "cycles": len(self.cycles),
            "avg_effectiveness": trend,
            "trend": label,
        }


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — AdaptiveLearningEngine v188
# ═══════════════════════════════════════════════════════════════

class AdaptiveLearningEngine:
    """
    OMNI-HUB v188 自适应学习引擎

    śikṣā · yogyatā — 学与适应
    """

    VERSION = "188.0.0"

    def __init__(self):
        self.strategy_pool = DefenseStrategyPool()
        self.pattern_learner = PatternLearner()
        self.anomaly_detector = AnomalyDetector()
        self.auto_tuner = AutoTuner()
        self.feedback_loop = FeedbackLoop()

        self.cycle_count = 0
        self.event_log: deque = deque(maxlen=10000)

    def process_attack_result(self, attack_result: Dict):
        """处理攻击结果并学习"""
        attack_type = attack_result.get("attack_type", "UNKNOWN")
        strategy_id = attack_result.get("strategy_used", "")
        detected = attack_result.get("detected", False)
        contained = attack_result.get("contained", False)
        impact = attack_result.get("impact_score", 0.5)

        # 1. 更新策略效果
        if strategy_id:
            self.strategy_pool.report_outcome(strategy_id, detected and contained)

        # 2. 记录反馈
        self.feedback_loop.record_cycle(attack_type, strategy_id, detected, contained, impact)

        # 3. 学习模式
        pattern_class = PatternClass.ATTACK if impact > 0.3 else PatternClass.NORMAL
        self.pattern_learner.learn(attack_result, pattern_class)

    def process_system_state(self, module_id: str, metrics: Dict[str, float]):
        """处理系统状态"""
        # 更新基线
        self.anomaly_detector.update_baseline(module_id, metrics)
        # 检测异常
        anomalies = self.anomaly_detector.detect(module_id, metrics)
        # 学习正常模式
        if not anomalies:
            self.pattern_learner.learn(metrics, PatternClass.NORMAL)
        else:
            for a in anomalies:
                self.pattern_learner.learn({"anomaly_score": a.anomaly_score, "module": module_id}, PatternClass.ANOMALY)
        return anomalies

    def auto_tune(self) -> List[TuningAction]:
        """执行自动调优"""
        trend, label = self.feedback_loop.get_trend()
        if label == "IMPROVING":
            self.auto_tuner.feedback("defense_aggressiveness", 0.05)
        elif label == "DEGRADING":
            self.auto_tuner.feedback("defense_aggressiveness", -0.1)
            self.auto_tuner.feedback("sensitivity", 0.1)
        return self.auto_tuner.tune()

    def select_defense(self, attack_type: str) -> Optional[DefenseStrategy]:
        """选择防御策略"""
        return self.strategy_pool.select_for_attack(attack_type)

    def run_cycle(self, attack_results: List[Dict] = None,
                 system_states: Dict[str, Dict] = None) -> Dict:
        """运行完整学习周期"""
        self.cycle_count += 1
        attack_results = attack_results or []
        system_states = system_states or {}

        # 1. 处理攻击结果
        for ar in attack_results:
            self.process_attack_result(ar)

        # 2. 处理系统状态
        total_anomalies = 0
        for module_id, metrics in system_states.items():
            anomalies = self.process_system_state(module_id, metrics)
            total_anomalies += len(anomalies)

        # 3. 自动调优
        tuning_actions = self.auto_tune()

        # 4. 进化策略
        new_strategies = self.strategy_pool.evolve(attack_results)

        # 5. 趋势
        trend, label = self.feedback_loop.get_trend()

        result = {
            "cycle": self.cycle_count,
            "attacks_processed": len(attack_results),
            "anomalies_detected": total_anomalies,
            "tuning_actions": len(tuning_actions),
            "new_strategies": len(new_strategies),
            "effectiveness_trend": trend,
            "trend_label": label,
            "patterns_learned": len(self.pattern_learner.patterns),
        }

        self.event_log.append(result)
        return result

    def get_status(self) -> Dict:
        return {
            "version": self.VERSION,
            "cycle_count": self.cycle_count,
            "strategy_pool": self.strategy_pool.get_report(),
            "pattern_learner": self.pattern_learner.get_report(),
            "anomaly_detector": self.anomaly_detector.get_report(),
            "auto_tuner": self.auto_tuner.get_report(),
            "feedback_loop": self.feedback_loop.get_report(),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_ale_instance: Optional[AdaptiveLearningEngine] = None


def get_adaptive_learning_engine() -> AdaptiveLearningEngine:
    global _ale_instance
    if _ale_instance is None:
        _ale_instance = AdaptiveLearningEngine()
    return _ale_instance


if __name__ == "__main__":
    ale = AdaptiveLearningEngine()
    print(f"AdaptiveLearningEngine v{ale.VERSION} initialized")
    print(f"Status: {json.dumps(ale.get_status(), indent=2, default=str)}")
