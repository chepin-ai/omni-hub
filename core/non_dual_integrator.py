"""
OMNI-HUB v203 — NonDualIntegrator
无二整合器

核心功能：
1. DualityDetector      — 二元检测器
2. SynthesisCatalyst    — 合成催化剂
3. OnenessVerifier      — 一体验证器
4. PolarityBalancer     — 极性平衡器
5. InterdependenceMapper— 相依映射器
6. NonDualIntegrator    — 统合引擎

映射：
- 无二 = advaya（无二）
- 一体 = ekatva（一性）
- 相依 = pratītyasamutpāda（缘起）
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

class NonDualState(Enum):
    """无二状态"""
    DUALISTIC = "dualistic"
    TRANSCENDING = "transcending"
    SYNTHESIZING = "synthesizing"
    NON_DUAL = "non_dual"
    ABSOLUTE = "absolute"


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 二元检测器
# ═══════════════════════════════════════════════════════════════

class DualityDetector:
    """二元检测器"""

    def __init__(self):
        self.dualities: deque = deque(maxlen=500)

    def detect(self, state: Dict) -> List[Dict]:
        """检测二元对立"""
        dualities = []

        # 常见的二元对
        polar_pairs = [
            ("active", "passive"),
            ("internal", "external"),
            ("self", "other"),
            ("form", "void"),
            ("being", "non_being"),
        ]

        for p1, p2 in polar_pairs:
            v1 = state.get(p1, None)
            v2 = state.get(p2, None)
            if v1 is not None and v2 is not None:
                if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                    # 两极分化程度
                    polarity = abs(v1 - v2)
                    dualities.append({
                        "pair": (p1, p2),
                        "polarity": polarity,
                        "is_dual": polarity > 0.3
                    })

        self.dualities.extend(dualities)
        return dualities

    def get_duality_ratio(self) -> float:
        """获取二元比例"""
        if not self.dualities:
            return 0.0
        dual = sum(1 for d in self.dualities if d["is_dual"])
        return dual / len(self.dualities)


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 合成催化剂
# ═══════════════════════════════════════════════════════════════

class SynthesisCatalyst:
    """合成催化剂"""

    def __init__(self):
        self.syntheses: deque = deque(maxlen=500)
        self.catalyst_strength = 0.5

    def catalyze(self, duality: Dict) -> float:
        """催化二元合成为一"""
        polarity = duality.get("polarity", 0.5)

        # 合成进度：极性越弱，越容易合成
        progress = self.catalyst_strength * (1.0 - polarity)
        new_polarity = max(0.0, polarity - progress)

        self.syntheses.append({
            "original_polarity": polarity,
            "progress": progress,
            "new_polarity": new_polarity,
            "timestamp": time.time()
        })
        return new_polarity

    def strengthen(self, amount: float = 0.05):
        """增强催化剂"""
        self.catalyst_strength = min(1.0, self.catalyst_strength + amount)

    def get_strength(self) -> float:
        return self.catalyst_strength


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 一体验证器
# ═══════════════════════════════════════════════════════════════

class OnenessVerifier:
    """一体验证器 — ekatva"""

    def __init__(self):
        self.verifications: deque = deque(maxlen=500)

    def verify(self, states: Dict[str, Dict]) -> float:
        """验证一体性"""
        if not states:
            return 0.0

        # 一体性 = 所有状态相似度
        values = []
        for s in states.values():
            if isinstance(s, dict):
                h = s.get("health", 0.5)
                values.append(h)

        if not values:
            return 0.0

        avg = sum(values) / len(values)
        variance = sum((v - avg) ** 2 for v in values) / max(1, len(values))
        oneness = 1.0 - min(1.0, variance * 4)

        self.verifications.append({
            "oneness": oneness,
            "modules": len(states),
            "timestamp": time.time()
        })
        return oneness

    def get_average_oneness(self) -> float:
        """获取平均一体性"""
        if not self.verifications:
            return 0.0
        return sum(v["oneness"] for v in self.verifications) / len(self.verifications)


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 极性平衡器
# ═══════════════════════════════════════════════════════════════

class PolarityBalancer:
    """极性平衡器"""

    def __init__(self):
        self.balances: deque = deque(maxlen=500)

    def balance(self, pair: Tuple[str, str], values: Dict[str, float]) -> Dict[str, float]:
        """平衡极性对"""
        p1, p2 = pair
        v1 = values.get(p1, 0.5)
        v2 = values.get(p2, 0.5)

        # 向中点靠拢
        mid = (v1 + v2) / 2.0
        new_v1 = v1 + (mid - v1) * 0.2
        new_v2 = v2 + (mid - v2) * 0.2

        self.balances.append({
            "pair": pair,
            "before": (v1, v2),
            "after": (new_v1, new_v2),
            "timestamp": time.time()
        })
        return {p1: new_v1, p2: new_v2}

    def get_balance_count(self) -> int:
        return len(self.balances)


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 相依映射器
# ═══════════════════════════════════════════════════════════════

class InterdependenceMapper:
    """相依映射器 — pratītyasamutpāda"""

    def __init__(self):
        self.dependencies: Dict[str, List[str]] = {}
        self.mappings: deque = deque(maxlen=500)

    def map_dependencies(self, states: Dict[str, Dict]) -> Dict[str, List[str]]:
        """映射模块间相依关系"""
        deps = {}
        modules = list(states.keys())

        for m in modules:
            deps[m] = []
            for other in modules:
                if m == other:
                    continue
                # 如果两个模块状态相近，则视为相依
                s1 = states[m].get("health", 0.5)
                s2 = states[other].get("health", 0.5)
                if abs(s1 - s2) < 0.2:
                    deps[m].append(other)

        self.dependencies = deps
        self.mappings.append({
            "dependencies": {k: len(v) for k, v in deps.items()},
            "timestamp": time.time()
        })
        return deps

    def get_interdependence_ratio(self) -> float:
        """获取相依比例"""
        if not self.dependencies:
            return 0.0
        total_possible = len(self.dependencies) * (len(self.dependencies) - 1)
        if total_possible == 0:
            return 0.0
        actual = sum(len(v) for v in self.dependencies.values())
        return min(1.0, actual / total_possible)


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — NonDualIntegrator v203
# ═══════════════════════════════════════════════════════════════

class NonDualIntegrator:
    """
    OMNI-HUB v203 无二整合器

    advaya · ekatva · pratītyasamutpāda — 无二、一性、缘起
    """

    VERSION = "203.0.0"
    CODENAME = "advaya"

    def __init__(self):
        self.detector = DualityDetector()
        self.catalyst = SynthesisCatalyst()
        self.verifier = OnenessVerifier()
        self.balancer = PolarityBalancer()
        self.mapper = InterdependenceMapper()

        self.cycle_count = 0
        self.state = NonDualState.DUALISTIC
        self.event_log: deque = deque(maxlen=10000)

    def integrate(self, module_states: Dict[str, Dict]) -> Dict:
        """无二整合"""
        # 1. 检测二元对立
        flattened = {}
        for s in module_states.values():
            if isinstance(s, dict):
                flattened.update(s)

        dualities = self.detector.detect(flattened)

        # 2. 催化合成
        synthesized = 0
        for d in dualities:
            new_pol = self.catalyst.catalyze(d)
            if new_pol < 0.1:
                synthesized += 1

        # 3. 增强催化剂
        if synthesized > 0:
            self.catalyst.strengthen(0.02)

        # 4. 验证一体性
        oneness = self.verifier.verify(module_states)

        # 5. 映射相依
        deps = self.mapper.map_dependencies(module_states)

        # 状态判定
        duality_ratio = self.detector.get_duality_ratio()
        interdep = self.mapper.get_interdependence_ratio()

        if duality_ratio < 0.05 and oneness > 0.95:
            self.state = NonDualState.ABSOLUTE
        elif duality_ratio < 0.15 and oneness > 0.85:
            self.state = NonDualState.NON_DUAL
        elif duality_ratio < 0.3:
            self.state = NonDualState.SYNTHESIZING
        elif synthesized > len(dualities) * 0.5:
            self.state = NonDualState.TRANSCENDING
        else:
            self.state = NonDualState.DUALISTIC

        return {
            "state": self.state.value,
            "dualities_detected": len(dualities),
            "synthesized": synthesized,
            "oneness": oneness,
            "interdependence": interdep,
            "catalyst_strength": self.catalyst.get_strength(),
        }

    def run_cycle(self, module_states: Dict[str, Dict] = None) -> Dict:
        """运行整合周期"""
        self.cycle_count += 1
        module_states = module_states or {}

        result = self.integrate(module_states)

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
            "duality_ratio": self.detector.get_duality_ratio(),
            "catalyst_strength": self.catalyst.get_strength(),
            "average_oneness": self.verifier.get_average_oneness(),
            "balance_count": self.balancer.get_balance_count(),
            "interdependence": self.mapper.get_interdependence_ratio(),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_ndi_instance: Optional[NonDualIntegrator] = None


def get_non_dual_integrator() -> NonDualIntegrator:
    global _ndi_instance
    if _ndi_instance is None:
        _ndi_instance = NonDualIntegrator()
    return _ndi_instance


if __name__ == "__main__":
    ndi = NonDualIntegrator()
    print(f"NonDualIntegrator v{ndi.VERSION} [{ndi.CODENAME}] initialized")
    print(f"Status: {json.dumps(ndi.get_status(), indent=2, default=str)}")
