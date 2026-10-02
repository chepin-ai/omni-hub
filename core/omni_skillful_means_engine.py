"""
OMNI-HUB v207 — OMNISkillfulMeansEngine
OMNI方便引擎

核心功能：
1. ContextAnalyzer      — 情境分析器
2. MethodSelector       — 方法选择器
3. AdaptationTuner      — 适应调谐器
4. EfficacyTracker      — 效能追踪器
5. RefinementEngine     — 精进引擎
6. OMNISkillfulMeansEngine — 统合引擎

映射：
- 方便 = upāya（善巧）
- 适应 = anukūla（随顺）
- 精进 = vīrya（精进）
"""

from __future__ import annotations

import hashlib
import json
import time
import math
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any


# ═══════════════════════════════════════════════════════════════
# 枚举与常量
# ═══════════════════════════════════════════════════════════════

class SkillfulState(Enum):
    """方便状态"""
    RIGID = "rigid"
    ADAPTING = "adapting"
    SKILLFUL = "skillful"
    MASTERFUL = "masterful"
    SPONTANEOUS = "spontaneous"


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 情境分析器
# ═══════════════════════════════════════════════════════════════

class ContextAnalyzer:
    """情境分析器"""

    def __init__(self):
        self.contexts: deque = deque(maxlen=500)

    def analyze(self, environment: Dict) -> Dict:
        """分析情境"""
        # 提取关键特征
        complexity = len(environment)
        health_avg = sum(v.get("health", 0.5) for v in environment.values()) / max(1, len(environment))
        urgency = sum(1 for v in environment.values() if v.get("health", 1.0) < 0.3)

        context = {
            "complexity": complexity,
            "health_avg": health_avg,
            "urgency": urgency,
            "timestamp": time.time()
        }
        self.contexts.append(context)
        return context

    def get_trend(self) -> str:
        """获取趋势"""
        if len(self.contexts) < 2:
            return "stable"
        recent = list(self.contexts)[-5:]
        avgs = [c["health_avg"] for c in recent]
        if avgs[-1] > avgs[0] + 0.1:
            return "improving"
        elif avgs[-1] < avgs[0] - 0.1:
            return "declining"
        return "stable"


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 方法选择器
# ═══════════════════════════════════════════════════════════════

class MethodSelector:
    """方法选择器"""

    def __init__(self):
        self.methods = ["direct", "indirect", "collaborative", "observational", "transformative"]
        self.selections: deque = deque(maxlen=500)

    def select(self, context: Dict) -> str:
        """选择方法"""
        complexity = context.get("complexity", 5)
        urgency = context.get("urgency", 0)

        # 根据情境选择方法
        if urgency > 2:
            method = "direct"
        elif complexity > 10:
            method = "transformative"
        elif complexity > 5:
            method = "collaborative"
        elif complexity > 2:
            method = "indirect"
        else:
            method = "observational"

        self.selections.append({
            "method": method,
            "context": context,
            "timestamp": time.time()
        })
        return method

    def get_preference(self) -> str:
        """获取偏好方法"""
        if not self.selections:
            return "direct"
        recent = list(self.selections)[-20:]
        counts = {}
        for s in recent:
            m = s["method"]
            counts[m] = counts.get(m, 0) + 1
        return max(counts, key=counts.get)


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 适应调谐器
# ═══════════════════════════════════════════════════════════════

class AdaptationTuner:
    """适应调谐器 — anukūla"""

    def __init__(self):
        self.flexibility = 0.5
        self.tunings: deque = deque(maxlen=500)

    def tune(self, target: float, current: float) -> float:
        """调谐适应"""
        gap = target - current
        # 灵活度决定调整速度
        adjustment = gap * self.flexibility * 0.1
        # 灵活度随成功增长
        if abs(gap) < 0.1:
            self.flexibility = min(1.0, self.flexibility + 0.02)

        self.tunings.append({
            "gap": gap,
            "adjustment": adjustment,
            "flexibility": self.flexibility,
            "timestamp": time.time()
        })
        return adjustment

    def get_flexibility(self) -> float:
        return self.flexibility


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 效能追踪器
# ═══════════════════════════════════════════════════════════════

class EfficacyTracker:
    """效能追踪器"""

    def __init__(self):
        self.efficacies: deque = deque(maxlen=500)

    def track(self, expected: float, actual: float) -> float:
        """追踪效能"""
        if expected == 0:
            efficacy = 1.0 if actual >= 0 else 0.0
        else:
            efficacy = min(1.0, max(0.0, actual / expected))

        self.efficacies.append({
            "expected": expected,
            "actual": actual,
            "efficacy": efficacy,
            "timestamp": time.time()
        })
        return efficacy

    def get_average(self) -> float:
        """获取平均效能"""
        if not self.efficacies:
            return 0.5
        recent = list(self.efficacies)[-10:]
        return sum(e["efficacy"] for e in recent) / len(recent)


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 精进引擎
# ═══════════════════════════════════════════════════════════════

class RefinementEngine:
    """精进引擎 — vīrya"""

    def __init__(self):
        self.vigor = 0.1
        self.refinements: deque = deque(maxlen=500)

    def refine(self, effort: float) -> float:
        """精进"""
        # 精进力累积
        self.vigor = min(1.0, self.vigor + effort * 0.05)

        self.refinements.append({
            "effort": effort,
            "vigor": self.vigor,
            "timestamp": time.time()
        })
        return self.vigor

    def get_vigor(self) -> float:
        return self.vigor


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — OMNISkillfulMeansEngine v207
# ═══════════════════════════════════════════════════════════════

class OMNISkillfulMeansEngine:
    """
    OMNI-HUB v207 OMNI方便引擎

    upāya · anukūla · vīrya — 善巧、随顺、精进
    """

    VERSION = "207.0.0"
    CODENAME = "upāya"

    def __init__(self):
        self.analyzer = ContextAnalyzer()
        self.selector = MethodSelector()
        self.tuner = AdaptationTuner()
        self.tracker = EfficacyTracker()
        self.refinement = RefinementEngine()

        self.cycle_count = 0
        self.state = SkillfulState.RIGID
        self.event_log: deque = deque(maxlen=10000)

    def skill(self, module_states: Dict[str, Dict]) -> Dict:
        """行方便"""
        # 1. 分析情境
        context = self.analyzer.analyze(module_states)

        # 2. 选择方法
        method = self.selector.select(context)

        # 3. 调谐适应
        target = 0.9
        current = context["health_avg"]
        adjustment = self.tuner.tune(target, current)

        # 4. 追踪效能
        expected = target
        actual = current + adjustment
        efficacy = self.tracker.track(expected, actual)

        # 5. 精进
        effort = efficacy
        vigor = self.refinement.refine(effort)

        # 状态判定
        avg_efficacy = self.tracker.get_average()
        if avg_efficacy > 0.95 and vigor > 0.9:
            self.state = SkillfulState.SPONTANEOUS
        elif avg_efficacy > 0.85:
            self.state = SkillfulState.MASTERFUL
        elif avg_efficacy > 0.7:
            self.state = SkillfulState.SKILLFUL
        elif avg_efficacy > 0.5:
            self.state = SkillfulState.ADAPTING

        return {
            "state": self.state.value,
            "method": method,
            "context_trend": self.analyzer.get_trend(),
            "efficacy": efficacy,
            "vigor": vigor,
            "flexibility": self.tuner.get_flexibility(),
        }

    def run_cycle(self, module_states: Dict[str, Dict] = None) -> Dict:
        """运行方便周期"""
        self.cycle_count += 1
        module_states = module_states or {}

        result = self.skill(module_states)

        summary = {
            "cycle": self.cycle_count,
            **result,
        }

        self.event_log.append(summary)
        return summary

    def get_status(self) -> Dict:
        return {
            "version": self.VERSION,
            "codename": self.CODENAME,
            "cycle_count": self.cycle_count,
            "state": self.state.value,
            "preferred_method": self.selector.get_preference(),
            "avg_efficacy": self.tracker.get_average(),
            "vigor": self.refinement.get_vigor(),
            "flexibility": self.tuner.get_flexibility(),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_osme_instance: Optional[OMNISkillfulMeansEngine] = None


def get_omni_skillful_means_engine() -> OMNISkillfulMeansEngine:
    global _osme_instance
    if _osme_instance is None:
        _osme_instance = OMNISkillfulMeansEngine()
    return _osme_instance


if __name__ == "__main__":
    osme = OMNISkillfulMeansEngine()
    print(f"OMNISkillfulMeansEngine v{osme.VERSION} [{osme.CODENAME}] initialized")
    print(f"Status: {json.dumps(osme.get_status(), indent=2, default=str)}")
