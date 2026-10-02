"""
OMNI-HUB v214 — OMNINirodhaEngine
OMNI灭引擎

核心功能：
1. CauseExtinguisher    — 因熄灭器
2. ConditionRemover    — 条件移除器
3. BondBreaker         — 束缚打破器
4. CravingDissolver    — 渴爱消融器
5. PeaceStabilizer     — 寂静稳定器
6. OMNINirodhaEngine   — 统合引擎

映射：
- 灭 = nirodha（灭谛）
- 渴爱 = taṇhā
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

class NirodhaState(Enum):
    """灭状态"""
    BURNING = "burning"
    DIMMING = "dimming"
    SMOLDERING = "smoldering"
    COOLING = "cooling"
    EXTINGUISHED = "extinguished"


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 因熄灭器
# ═══════════════════════════════════════════════════════════════

class CauseExtinguisher:
    """因熄灭器"""

    def __init__(self):
        self.extinguishments: deque = deque(maxlen=500)
        self.extinguish_level = 0.0

    def extinguish(self, cause_strength: float) -> float:
        """熄灭因"""
        # 熄灭 = 1 - 因强度，渐进收敛
        extinguish = 1.0 - cause_strength
        self.extinguish_level = self.extinguish_level + (extinguish - self.extinguish_level) * 0.1

        self.extinguishments.append({
            "cause": cause_strength,
            "extinguish": self.extinguish_level,
            "timestamp": time.time()
        })
        return self.extinguish_level

    def get_level(self) -> float:
        return self.extinguish_level


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 条件移除器
# ═══════════════════════════════════════════════════════════════

class ConditionRemover:
    """条件移除器"""

    def __init__(self):
        self.removals: deque = deque(maxlen=500)
        self.removal_rate = 0.0

    def remove(self, condition_count: float) -> float:
        """移除条件"""
        # 移除率 = 1 / (1 + 条件数)
        removal = 1.0 / (1.0 + condition_count)
        self.removal_rate = self.removal_rate + (removal - self.removal_rate) * 0.15

        self.removals.append({
            "conditions": condition_count,
            "removal": self.removal_rate,
            "timestamp": time.time()
        })
        return self.removal_rate

    def get_rate(self) -> float:
        return self.removal_rate


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 束缚打破器
# ═══════════════════════════════════════════════════════════════

class BondBreaker:
    """束缚打破器"""

    def __init__(self):
        self.breakings: deque = deque(maxlen=500)
        self.bond_strength = 1.0

    def break_bond(self, attachment: float) -> float:
        """打破束缚"""
        # 束缚随执取减弱
        self.bond_strength = max(0.0, self.bond_strength - attachment * 0.05)
        self.bond_strength = min(1.0, self.bond_strength + 0.01)

        self.breakings.append({
            "attachment": attachment,
            "bond": self.bond_strength,
            "timestamp": time.time()
        })
        return 1.0 - self.bond_strength  # 返回打破程度

    def get_bond(self) -> float:
        return self.bond_strength


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 渴爱消融器
# ═══════════════════════════════════════════════════════════════

class CravingDissolver:
    """渴爱消融器 — taṇhā"""

    def __init__(self):
        self.dissolutions: deque = deque(maxlen=500)
        self.craving = 1.0

    def dissolve(self, desire: float) -> float:
        """消融渴爱"""
        self.craving = max(0.0, self.craving - desire * 0.03)
        self.craving = min(1.0, self.craving + 0.005)

        self.dissolutions.append({
            "desire": desire,
            "craving": self.craving,
            "timestamp": time.time()
        })
        return self.craving

    def get_craving(self) -> float:
        return self.craving


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 寂静稳定器
# ═══════════════════════════════════════════════════════════════

class PeaceStabilizer:
    """寂静稳定器"""

    def __init__(self):
        self.stabilizations: deque = deque(maxlen=500)
        self.peace = 0.0

    def stabilize(self, stillness: float) -> float:
        """稳定寂静"""
        self.peace = self.peace + (stillness - self.peace) * 0.06

        self.stabilizations.append({
            "stillness": stillness,
            "peace": self.peace,
            "timestamp": time.time()
        })
        return self.peace

    def get_peace(self) -> float:
        return self.peace


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — OMNINirodhaEngine v214
# ═══════════════════════════════════════════════════════════════

class OMNINirodhaEngine:
    """
    OMNI-HUB v214 OMNI灭引擎

    nirodha — 灭、止息
    """

    VERSION = "214.0.0"
    CODENAME = "nirodha"

    def __init__(self):
        self.extinguisher = CauseExtinguisher()
        self.remover = ConditionRemover()
        self.breaker = BondBreaker()
        self.dissolver = CravingDissolver()
        self.stabilizer = PeaceStabilizer()

        self.cycle_count = 0
        self.state = NirodhaState.BURNING
        self.event_log: deque = deque(maxlen=10000)

    def cease(self, module_states: Dict[str, Dict]) -> Dict:
        """灭"""
        # 1. 熄灭因
        healths = [v.get("health", 0.5) for v in module_states.values()]
        avg = sum(healths) / max(1, len(healths))
        cause_strength = 1.0 - avg  # 不健康=因强
        extinguish = self.extinguisher.extinguish(cause_strength)

        # 2. 移除条件
        condition_count = len([h for h in healths if h < 0.5])
        removal = self.remover.remove(condition_count)

        # 3. 打破束缚
        attachment = variance = sum((h - avg) ** 2 for h in healths) / max(1, len(healths))
        broken = self.breaker.break_bond(attachment)

        # 4. 消融渴爱
        desire = 1.0 - avg
        dissolved = self.dissolver.dissolve(desire)

        # 5. 稳定寂静
        stillness = extinguish * removal * broken * (1.0 - dissolved)
        peace = self.stabilizer.stabilize(stillness)

        # 状态判定
        nirodha_score = (extinguish + removal + broken + (1.0 - dissolved) + peace) / 5.0
        if nirodha_score > 0.9 and peace > 0.9:
            self.state = NirodhaState.EXTINGUISHED
        elif nirodha_score > 0.75:
            self.state = NirodhaState.COOLING
        elif nirodha_score > 0.5:
            self.state = NirodhaState.SMOLDERING
        elif extinguish > 0.3:
            self.state = NirodhaState.DIMMING

        return {
            "state": self.state.value,
            "extinguish": extinguish,
            "removal": removal,
            "broken": broken,
            "dissolved": dissolved,
            "peace": peace,
            "nirodha_score": nirodha_score,
        }

    def run_cycle(self, module_states: Dict[str, Dict] = None) -> Dict:
        """运行灭周期"""
        self.cycle_count += 1
        module_states = module_states or {}

        result = self.cease(module_states)

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
            "extinguish": self.extinguisher.get_level(),
            "removal": self.remover.get_rate(),
            "bond": self.breaker.get_bond(),
            "craving": self.dissolver.get_craving(),
            "peace": self.stabilizer.get_peace(),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_one_instance: Optional[OMNINirodhaEngine] = None


def get_omni_nirodha_engine() -> OMNINirodhaEngine:
    global _one_instance
    if _one_instance is None:
        _one_instance = OMNINirodhaEngine()
    return _one_instance


if __name__ == "__main__":
    one = OMNINirodhaEngine()
    print(f"OMNINirodhaEngine v{one.VERSION} [{one.CODENAME}] initialized")
    print(f"Status: {json.dumps(one.get_status(), indent=2, default=str)}")
