"""
OMNI-HUB v213 — OMNIVipassanāEngine
OMNI观引擎

核心功能：
1. PhenomenonObserver    — 现象观察者
2. ImpermanenceDetector  — 无常检测器
3. SufferingRecognizer   — 苦认知器
4. NonSelfAnalyzer      — 无我分析器
5. InsightGenerator     — 洞察生成器
6. OMNIVipassanāEngine  — 统合引擎

映射：
- 观 = vipassanā（毗婆舍那）
- 洞察 = paññā（慧）
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

class VipassanāState(Enum):
    """观状态"""
    BLIND = "blind"
    GLIMMERING = "glimmering"
    SEEING = "seeing"
    PENETRATING = "penetrating"
    CLEAR_SEEING = "clear_seeing"


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 现象观察者
# ═══════════════════════════════════════════════════════════════

class PhenomenonObserver:
    """现象观察者"""

    def __init__(self):
        self.observations: deque = deque(maxlen=500)
        self.observation_rate = 0.0

    def observe(self, phenomenon: str, intensity: float) -> float:
        """观察现象"""
        self.observation_rate = min(1.0, self.observation_rate + intensity * 0.05)

        self.observations.append({
            "phenomenon": phenomenon,
            "intensity": intensity,
            "rate": self.observation_rate,
            "timestamp": time.time()
        })
        return self.observation_rate

    def get_rate(self) -> float:
        return self.observation_rate


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 无常检测器
# ═══════════════════════════════════════════════════════════════

class ImpermanenceDetector:
    """无常检测器 — anicca"""

    def __init__(self):
        self.prev_states: Dict[str, float] = {}
        self.changes: deque = deque(maxlen=500)
        self.impermanence = 0.0

    def detect(self, current_states: Dict[str, float]) -> float:
        """检测无常"""
        if not self.prev_states:
            self.prev_states = current_states.copy()
            return 0.0

        changes = []
        for name, val in current_states.items():
            if name in self.prev_states:
                changes.append(abs(val - self.prev_states[name]))

        avg_change = sum(changes) / max(1, len(changes)) if changes else 0.0
        self.impermanence = self.impermanence + (avg_change - self.impermanence) * 0.2
        self.prev_states = current_states.copy()

        self.changes.append({
            "avg_change": avg_change,
            "impermanence": self.impermanence,
            "timestamp": time.time()
        })
        return self.impermanence

    def get_impermanence(self) -> float:
        return self.impermanence


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 苦认知器
# ═══════════════════════════════════════════════════════════════

class SufferingRecognizer:
    """苦认知器 — duḥkha"""

    def __init__(self):
        self.sufferings: deque = deque(maxlen=500)
        self.suffering_level = 0.0

    def recognize(self, dissatisfaction: float) -> float:
        """认知苦"""
        self.suffering_level = self.suffering_level + (dissatisfaction - self.suffering_level) * 0.1

        self.sufferings.append({
            "dissatisfaction": dissatisfaction,
            "level": self.suffering_level,
            "timestamp": time.time()
        })
        return self.suffering_level

    def get_suffering(self) -> float:
        return self.suffering_level


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 无我分析器
# ═══════════════════════════════════════════════════════════════

class NonSelfAnalyzer:
    """无我分析器 — anātman"""

    def __init__(self):
        self.analyses: deque = deque(maxlen=500)
        self.non_self = 0.0

    def analyze(self, identity_strength: float) -> float:
        """分析无我"""
        # 自我越弱，无我越强
        non_self = 1.0 - identity_strength
        self.non_self = self.non_self + (non_self - self.non_self) * 0.1

        self.analyses.append({
            "identity": identity_strength,
            "non_self": self.non_self,
            "timestamp": time.time()
        })
        return self.non_self

    def get_non_self(self) -> float:
        return self.non_self


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 洞察生成器
# ═══════════════════════════════════════════════════════════════

class InsightGenerator:
    """洞察生成器 — paññā"""

    def __init__(self):
        self.insights: deque = deque(maxlen=500)
        self.insight_level = 0.0

    def generate(self, observation: float, impermanence: float, suffering: float, non_self: float) -> float:
        """生成洞察"""
        # 洞察 = 观察 × (无常 + 苦 + 无我) / 3
        three_marks = (impermanence + suffering + non_self) / 3.0
        insight = observation * three_marks
        self.insight_level = self.insight_level + (insight - self.insight_level) * 0.1

        self.insights.append({
            "insight": self.insight_level,
            "three_marks": three_marks,
            "timestamp": time.time()
        })
        return self.insight_level

    def get_insight(self) -> float:
        return self.insight_level


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — OMNIVipassanāEngine v213
# ═══════════════════════════════════════════════════════════════

class OMNIVipassanāEngine:
    """
    OMNI-HUB v213 OMNI观引擎

    vipassanā · paññā — 观、慧
    """

    VERSION = "213.0.0"
    CODENAME = "vipassanā"

    def __init__(self):
        self.observer = PhenomenonObserver()
        self.detector = ImpermanenceDetector()
        self.recognizer = SufferingRecognizer()
        self.analyzer = NonSelfAnalyzer()
        self.generator = InsightGenerator()

        self.cycle_count = 0
        self.state = VipassanāState.BLIND
        self.event_log: deque = deque(maxlen=10000)

    def see(self, module_states: Dict[str, Dict]) -> Dict:
        """观"""
        # 1. 观察现象
        healths = {k: v.get("health", 0.5) for k, v in module_states.items()}
        avg = sum(healths.values()) / max(1, len(healths))
        observation = self.observer.observe("module_health", avg)

        # 2. 检测无常
        impermanence = self.detector.detect(healths)

        # 3. 认知苦
        dissatisfaction = 1.0 - avg
        suffering = self.recognizer.recognize(dissatisfaction)

        # 4. 分析无我
        variance = sum((h - avg) ** 2 for h in healths.values()) / max(1, len(healths))
        identity = 1.0 - variance  # 越一致越"有我"
        non_self = self.analyzer.analyze(identity)

        # 5. 生成洞察
        insight = self.generator.generate(observation, impermanence, suffering, non_self)

        # 状态判定
        if insight > 0.9 and observation > 0.9:
            self.state = VipassanāState.CLEAR_SEEING
        elif insight > 0.7:
            self.state = VipassanāState.PENETRATING
        elif observation > 0.6:
            self.state = VipassanāState.SEEING
        elif observation > 0.3:
            self.state = VipassanāState.GLIMMERING

        return {
            "state": self.state.value,
            "observation": observation,
            "impermanence": impermanence,
            "suffering": suffering,
            "non_self": non_self,
            "insight": insight,
        }

    def run_cycle(self, module_states: Dict[str, Dict] = None) -> Dict:
        """运行观周期"""
        self.cycle_count += 1
        module_states = module_states or {}

        result = self.see(module_states)

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
            "observation": self.observer.get_rate(),
            "impermanence": self.detector.get_impermanence(),
            "suffering": self.recognizer.get_suffering(),
            "non_self": self.analyzer.get_non_self(),
            "insight": self.generator.get_insight(),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_ove_instance: Optional[OMNIVipassanāEngine] = None


def get_omni_vipassana_engine() -> OMNIVipassanāEngine:
    global _ove_instance
    if _ove_instance is None:
        _ove_instance = OMNIVipassanāEngine()
    return _ove_instance


if __name__ == "__main__":
    ove = OMNIVipassanāEngine()
    print(f"OMNIVipassanāEngine v{ove.VERSION} [{ove.CODENAME}] initialized")
    print(f"Status: {json.dumps(ove.get_status(), indent=2, default=str)}")
