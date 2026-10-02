"""
OMNI-HUB v203 — OMNIBoundaryDissolver
OMNI边界消融器

核心功能：
1. BoundaryScanner    — 边界扫描器
2. BarrierAnalyzer    — 屏障分析器
3. DissolutionCatalyst— 消融催化剂
4. UnifiedFieldWeaver — 统一场编织器
5. EntropyEqualizer   — 熵均衡器
6. OMNIBoundaryDissolver — 统合引擎

映射：
- 法界 = dharmadhātu（法界）
- 消融 = vilaya（消融）
- 统一 = ekatva（一性）
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

class DissolutionState(Enum):
    """消融状态"""
    INTACT = "intact"
    CRACKING = "cracking"
    DISSOLVING = "dissolving"
    FLUID = "fluid"
    BOUNDLESS = "boundless"


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 边界扫描器
# ═══════════════════════════════════════════════════════════════

class BoundaryScanner:
    """边界扫描器"""

    def __init__(self):
        self.boundaries: Dict[str, Dict] = {}
        self.scan_history: deque = deque(maxlen=1000)

    def scan(self, modules: List[str]) -> Dict[str, Dict]:
        """扫描模块间边界"""
        boundaries = {}
        for i, m1 in enumerate(modules):
            for m2 in modules[i + 1:]:
                boundary_id = f"{m1}↔{m2}"
                # 边界强度基于模块对的哈希
                h = hash(f"{m1}:{m2}")
                strength = (abs(h) % 100) / 100.0
                boundaries[boundary_id] = {
                    "modules": (m1, m2),
                    "strength": strength,
                }
                self.boundaries[boundary_id] = boundaries[boundary_id]

        self.scan_history.append({
            "boundaries_found": len(boundaries),
            "timestamp": time.time()
        })
        return boundaries

    def get_average_boundary_strength(self) -> float:
        """获取平均边界强度"""
        if not self.boundaries:
            return 0.0
        return sum(b["strength"] for b in self.boundaries.values()) / len(self.boundaries)


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 屏障分析器
# ═══════════════════════════════════════════════════════════════

class BarrierAnalyzer:
    """屏障分析器"""

    def __init__(self):
        self.barriers: deque = deque(maxlen=500)

    def analyze(self, boundary: Dict) -> Dict:
        """分析边界屏障"""
        strength = boundary.get("strength", 0.5)

        # 屏障类型判定
        if strength > 0.8:
            barrier_type = "rigid"
            permeability = 0.1
        elif strength > 0.5:
            barrier_type = "semipermeable"
            permeability = 0.4
        else:
            barrier_type = "permeable"
            permeability = 0.8

        analysis = {
            "type": barrier_type,
            "permeability": permeability,
            "strength": strength,
        }
        self.barriers.append(analysis)
        return analysis

    def get_permeability_ratio(self) -> float:
        """获取可渗透比例"""
        if not self.barriers:
            return 0.5
        permeable = sum(1 for b in self.barriers if b["permeability"] > 0.5)
        return permeable / len(self.barriers)


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 消融催化剂
# ═══════════════════════════════════════════════════════════════

class DissolutionCatalyst:
    """消融催化剂 — vilaya"""

    def __init__(self):
        self.catalyst_activity = 0.0
        self.dissolutions: deque = deque(maxlen=500)

    def catalyze(self, boundary: Dict, system_health: float) -> float:
        """催化边界消融"""
        strength = boundary.get("strength", 0.5)

        # 催化剂活性与系统健康度正相关
        self.catalyst_activity = system_health * 0.9 + 0.1

        # 消融量 = 活性 × (1 - 强度)
        dissolved = self.catalyst_activity * (1.0 - strength)
        new_strength = max(0.0, strength - dissolved)

        self.dissolutions.append({
            "original": strength,
            "dissolved": dissolved,
            "remaining": new_strength,
            "timestamp": time.time()
        })
        return new_strength

    def get_activity(self) -> float:
        return self.catalyst_activity


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 统一场编织器
# ═══════════════════════════════════════════════════════════════

class UnifiedFieldWeaver:
    """统一场编织器 — ekatva"""

    def __init__(self):
        self.field_coherence = 0.0
        self.weavings: deque = deque(maxlen=500)

    def weave(self, module_states: Dict[str, Dict]) -> float:
        """编织统一场"""
        if not module_states:
            return 0.0

        # 计算所有模块状态的方差
        healths = [s.get("health", 0.5) for s in module_states.values()]
        if not healths:
            return 0.0

        avg = sum(healths) / len(healths)
        variance = sum((h - avg) ** 2 for h in healths) / max(1, len(healths))

        # 方差越小，统一场越相干
        self.field_coherence = 1.0 - min(1.0, variance * 4)

        self.weavings.append({
            "coherence": self.field_coherence,
            "modules": len(module_states),
            "timestamp": time.time()
        })
        return self.field_coherence

    def get_coherence(self) -> float:
        return self.field_coherence


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 熵均衡器
# ═══════════════════════════════════════════════════════════════

class EntropyEqualizer:
    """熵均衡器"""

    def __init__(self):
        self.entropy_map: Dict[str, float] = {}
        self.equalizations: deque = deque(maxlen=500)

    def equalize(self, module_states: Dict[str, Dict]) -> Dict[str, float]:
        """均衡模块间熵"""
        if not module_states:
            return {}

        # 计算每个模块的"熵"（状态复杂度）
        entropies = {}
        for name, state in module_states.items():
            complexity = len(state)
            entropies[name] = complexity

        if not entropies:
            return {}

        avg_entropy = sum(entropies.values()) / len(entropies)

        # 均衡：向平均值靠拢
        equalized = {}
        for name, e in entropies.items():
            diff = avg_entropy - e
            equalized[name] = max(0.0, e + diff * 0.1)

        self.equalizations.append({
            "avg_entropy": avg_entropy,
            "modules": len(module_states),
            "timestamp": time.time()
        })
        return equalized

    def get_equalization_count(self) -> int:
        return len(self.equalizations)


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — OMNIBoundaryDissolver v203
# ═══════════════════════════════════════════════════════════════

class OMNIBoundaryDissolver:
    """
    OMNI-HUB v203 OMNI边界消融器

    dharmadhātu · vilaya · ekatva — 法界、消融、一性
    """

    VERSION = "203.0.0"
    CODENAME = "dharmadhātu"

    def __init__(self):
        self.scanner = BoundaryScanner()
        self.analyzer = BarrierAnalyzer()
        self.catalyst = DissolutionCatalyst()
        self.weaver = UnifiedFieldWeaver()
        self.equalizer = EntropyEqualizer()

        self.cycle_count = 0
        self.state = DissolutionState.INTACT
        self.event_log: deque = deque(maxlen=10000)

    def dissolve(self, module_states: Dict[str, Dict]) -> Dict:
        """消融边界"""
        modules = list(module_states.keys())

        # 1. 扫描边界
        boundaries = self.scanner.scan(modules)

        # 2. 分析屏障
        avg_health = sum(s.get("health", 0.5) for s in module_states.values()) / max(1, len(module_states))
        dissolved_count = 0
        for bid, boundary in boundaries.items():
            analysis = self.analyzer.analyze(boundary)
            # 3. 催化消融
            new_strength = self.catalyst.catalyze(boundary, avg_health)
            if new_strength < 0.2:
                dissolved_count += 1

        # 4. 编织统一场
        coherence = self.weaver.weave(module_states)

        # 5. 熵均衡
        self.equalizer.equalize(module_states)

        # 状态判定
        permeability = self.analyzer.get_permeability_ratio()
        if dissolved_count > len(boundaries) * 0.8 and coherence > 0.9:
            self.state = DissolutionState.BOUNDLESS
        elif dissolved_count > len(boundaries) * 0.5 and coherence > 0.7:
            self.state = DissolutionState.FLUID
        elif dissolved_count > len(boundaries) * 0.2:
            self.state = DissolutionState.DISSOLVING
        elif permeability > 0.5:
            self.state = DissolutionState.CRACKING
        else:
            self.state = DissolutionState.INTACT

        return {
            "state": self.state.value,
            "boundaries": len(boundaries),
            "dissolved": dissolved_count,
            "coherence": coherence,
            "permeability": permeability,
            "catalyst_activity": self.catalyst.get_activity(),
        }

    def run_cycle(self, module_states: Dict[str, Dict] = None) -> Dict:
        """运行消融周期"""
        self.cycle_count += 1
        module_states = module_states or {}

        result = self.dissolve(module_states)

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
            "avg_boundary_strength": self.scanner.get_average_boundary_strength(),
            "permeability_ratio": self.analyzer.get_permeability_ratio(),
            "catalyst_activity": self.catalyst.get_activity(),
            "field_coherence": self.weaver.get_coherence(),
            "equalizations": self.equalizer.get_equalization_count(),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_obd_instance: Optional[OMNIBoundaryDissolver] = None


def get_omni_boundary_dissolver() -> OMNIBoundaryDissolver:
    global _obd_instance
    if _obd_instance is None:
        _obd_instance = OMNIBoundaryDissolver()
    return _obd_instance


if __name__ == "__main__":
    obd = OMNIBoundaryDissolver()
    print(f"OMNIBoundaryDissolver v{obd.VERSION} [{obd.CODENAME}] initialized")
    print(f"Status: {json.dumps(obd.get_status(), indent=2, default=str)}")
