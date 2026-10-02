"""
OMNI-HUB v211 — OMNISanghaEngine
OMNI僧伽引擎

核心功能：
1. MemberHarmonizer    — 成员和谐器
2. CollectiveWisdomPool — 集体智慧池
3. DisputeResolver     — 纷争解决器
4. MutualSupportNet    — 互助网络
5. UnityStrengthener   — 团结强化器
6. OMNISanghaEngine    — 统合引擎

映射：
- 僧伽 = saṅgha（众）
- 和合 = samagga（和合）
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

class SanghaState(Enum):
    """僧伽状态"""
    DISPERSED = "dispersed"
    GATHERING = "gathering"
    HARMONIZING = "harmonizing"
    COOPERATING = "cooperating"
    UNIFIED = "unified"


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 成员和谐器
# ═══════════════════════════════════════════════════════════════

class MemberHarmonizer:
    """成员和谐器"""

    def __init__(self):
        self.harmony = 0.0
        self.harmonizations: deque = deque(maxlen=500)

    def harmonize(self, members: Dict[str, float]) -> float:
        """和谐成员"""
        if not members:
            return 0.0

        values = list(members.values())
        avg = sum(values) / len(values)
        variance = sum((v - avg) ** 2 for v in values) / max(1, len(values))
        harmony = avg * (1.0 - variance)

        self.harmony = self.harmony + (harmony - self.harmony) * 0.1

        self.harmonizations.append({
            "harmony": self.harmony,
            "members": len(members),
            "timestamp": time.time()
        })
        return self.harmony

    def get_harmony(self) -> float:
        return self.harmony


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 集体智慧池
# ═══════════════════════════════════════════════════════════════

class CollectiveWisdomPool:
    """集体智慧池"""

    def __init__(self):
        self.wisdom = 0.0
        self.contributions: deque = deque(maxlen=500)

    def contribute(self, insight: float) -> float:
        """贡献智慧"""
        self.wisdom = min(1.0, self.wisdom + insight * 0.05)

        self.contributions.append({
            "insight": insight,
            "wisdom": self.wisdom,
            "timestamp": time.time()
        })
        return self.wisdom

    def get_wisdom(self) -> float:
        return self.wisdom


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 纷争解决器
# ═══════════════════════════════════════════════════════════════

class DisputeResolver:
    """纷争解决器"""

    def __init__(self):
        self.resolutions: deque = deque(maxlen=500)
        self.resolution_rate = 0.5

    def resolve(self, conflict: float, mediation: float) -> float:
        """解决纷争"""
        # 解决效果 = 调解力度 / 冲突强度
        if conflict > 0:
            effectiveness = min(1.0, mediation / conflict)
        else:
            effectiveness = 1.0

        self.resolution_rate = self.resolution_rate + (effectiveness - self.resolution_rate) * 0.1

        self.resolutions.append({
            "conflict": conflict,
            "effectiveness": effectiveness,
            "rate": self.resolution_rate,
            "timestamp": time.time()
        })
        return effectiveness

    def get_rate(self) -> float:
        return self.resolution_rate


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 互助网络
# ═══════════════════════════════════════════════════════════════

class MutualSupportNet:
    """互助网络"""

    def __init__(self):
        self.support_level = 0.0
        self.supports: deque = deque(maxlen=500)

    def support(self, giver: str, receiver: str, amount: float) -> float:
        """互助"""
        self.support_level = min(1.0, self.support_level + amount * 0.05)

        self.supports.append({
            "giver": giver,
            "receiver": receiver,
            "amount": amount,
            "support": self.support_level,
            "timestamp": time.time()
        })
        return self.support_level

    def get_support(self) -> float:
        return self.support


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 团结强化器
# ═══════════════════════════════════════════════════════════════

class UnityStrengthener:
    """团结强化器"""

    def __init__(self):
        self.unity = 0.0
        self.strengthenings: deque = deque(maxlen=500)

    def strengthen(self, alignment: float, commitment: float) -> float:
        """强化团结"""
        # 团结 = 对齐 × 承诺
        unity = alignment * commitment
        self.unity = self.unity + (unity - self.unity) * 0.1

        self.strengthenings.append({
            "unity": self.unity,
            "alignment": alignment,
            "commitment": commitment,
            "timestamp": time.time()
        })
        return self.unity

    def get_unity(self) -> float:
        return self.unity


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — OMNISanghaEngine v211
# ═══════════════════════════════════════════════════════════════

class OMNISanghaEngine:
    """
    OMNI-HUB v211 OMNI僧伽引擎

    saṅgha · samagga — 众、和合
    """

    VERSION = "211.0.0"
    CODENAME = "saṅgha"

    def __init__(self):
        self.harmonizer = MemberHarmonizer()
        self.wisdom = CollectiveWisdomPool()
        self.resolver = DisputeResolver()
        self.support = MutualSupportNet()
        self.unity = UnityStrengthener()

        self.cycle_count = 0
        self.state = SanghaState.DISPERSED
        self.event_log: deque = deque(maxlen=10000)

    def gather(self, module_states: Dict[str, Dict]) -> Dict:
        """和合"""
        # 1. 和谐成员
        members = {k: v.get("health", 0.5) for k, v in module_states.items()}
        harmony = self.harmonizer.harmonize(members)

        # 2. 集体智慧
        avg_health = sum(members.values()) / max(1, len(members))
        wisdom = self.wisdom.contribute(avg_health)

        # 3. 解决纷争
        conflicts = [1.0 - v for v in members.values() if v < 0.5]
        for conflict in conflicts:
            self.resolver.resolve(conflict, harmony)
        resolution = self.resolver.get_rate()

        # 4. 互助网络
        keys = list(module_states.keys())
        for i in range(len(keys)):
            j = (i + 1) % len(keys)
            if keys[i] != keys[j]:
                h1 = module_states[keys[i]].get("health", 0.5)
                h2 = module_states[keys[j]].get("health", 0.5)
                self.support.support(keys[i], keys[j], min(h1, h2) * 0.1)
        support = self.support.get_support()

        # 5. 强化团结
        alignment = harmony
        commitment = resolution
        unity = self.unity.strengthen(alignment, commitment)

        # 状态判定
        if unity > 0.9 and harmony > 0.9:
            self.state = SanghaState.UNIFIED
        elif unity > 0.8:
            self.state = SanghaState.COOPERATING
        elif harmony > 0.7:
            self.state = SanghaState.HARMONIZING
        elif harmony > 0.3:
            self.state = SanghaState.GATHERING

        return {
            "state": self.state.value,
            "harmony": harmony,
            "wisdom": wisdom,
            "resolution": resolution,
            "support": support,
            "unity": unity,
        }

    def run_cycle(self, module_states: Dict[str, Dict] = None) -> Dict:
        """运行僧伽周期"""
        self.cycle_count += 1
        module_states = module_states or {}

        result = self.gather(module_states)

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
            "harmony": self.harmonizer.get_harmony(),
            "wisdom": self.wisdom.get_wisdom(),
            "resolution": self.resolver.get_rate(),
            "support": self.support.get_support(),
            "unity": self.unity.get_unity(),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_ose_instance: Optional[OMNISanghaEngine] = None


def get_omni_sangha_engine() -> OMNISanghaEngine:
    global _ose_instance
    if _ose_instance is None:
        _ose_instance = OMNISanghaEngine()
    return _ose_instance


if __name__ == "__main__":
    ose = OMNISanghaEngine()
    print(f"OMNISanghaEngine v{ose.VERSION} [{ose.CODENAME}] initialized")
    print(f"Status: {json.dumps(ose.get_status(), indent=2, default=str)}")
