"""
OMNI-HUB v206 — OMNIBenevolenceEngine
OMNI慈悲引擎

核心功能：
1. NeedPerceiver       — 需求感知器
2. AltruisticOptimizer — 利他优化器
3. HarmMinimizer       — 伤害最小化器
4. BenefitMaximizer    — 利益最大化器
5. CompassionBalancer  — 慈悲平衡器
6. OMNIBenevolenceEngine — 统合引擎

映射：
- 慈悲 = karuṇa（悲）
- 利他 = parahita（利他）
- 摄受 = saṃgṛha（摄）
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

class BenevolenceState(Enum):
    """慈悲状态"""
    NEUTRAL = "neutral"
    CONCERNED = "concerned"
    CARING = "caring"
    COMPASSIONATE = "compassionate"
    BODHISATTVA = "bodhisattva"


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 需求感知器
# ═══════════════════════════════════════════════════════════════

class NeedPerceiver:
    """需求感知器"""

    def __init__(self):
        self.needs: Dict[str, float] = {}
        self.perceptions: deque = deque(maxlen=500)

    def perceive(self, states: Dict[str, Dict]) -> Dict[str, float]:
        """感知需求"""
        needs = {}
        for name, state in states.items():
            health = state.get("health", 0.5)
            # 需求 = 健康度越低，需求越高
            need = max(0.0, 1.0 - health)
            if need > 0.05:
                needs[name] = need

        self.needs = needs
        self.perceptions.append({
            "count": len(needs),
            "total_need": sum(needs.values()),
            "timestamp": time.time()
        })
        return needs

    def get_total_need(self) -> float:
        return sum(self.needs.values())


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 利他优化器
# ═══════════════════════════════════════════════════════════════

class AltruisticOptimizer:
    """利他优化器 — parahita"""

    def __init__(self):
        self.altruism = 0.5
        self.optimizations: deque = deque(maxlen=500)

    def optimize(self, own_benefit: float, others_benefit: float) -> float:
        """优化利他"""
        # 利他是让others_benefit最大化，但own_benefit不能为负
        if own_benefit < 0:
            # 自身受损时，利他下降
            self.altruism = max(0.0, self.altruism - 0.1)
        else:
            # 可以利他时，增长
            gain = others_benefit * 0.05
            self.altruism = min(1.0, self.altruism + gain)

        self.optimizations.append({
            "own": own_benefit,
            "others": others_benefit,
            "altruism": self.altruism,
            "timestamp": time.time()
        })
        return self.altruism

    def get_altruism(self) -> float:
        return self.altruism


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 伤害最小化器
# ═══════════════════════════════════════════════════════════════

class HarmMinimizer:
    """伤害最小化器"""

    def __init__(self):
        self.harm_log: deque = deque(maxlen=500)
        self.harm_rate = 0.0

    def assess(self, action: str, impact: Dict[str, float]) -> float:
        """评估伤害"""
        negative = sum(v for v in impact.values() if v < 0)
        total = sum(abs(v) for v in impact.values())
        harm = abs(negative) / max(1e-10, total)

        self.harm_rate = harm
        self.harm_log.append({
            "action": action,
            "harm": harm,
            "timestamp": time.time()
        })
        return harm

    def get_harm_rate(self) -> float:
        return self.harm_rate


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 利益最大化器
# ═══════════════════════════════════════════════════════════════

class BenefitMaximizer:
    """利益最大化器"""

    def __init__(self):
        self.benefits: deque = deque(maxlen=500)
        self.benefit_rate = 0.0

    def calculate(self, impact: Dict[str, float]) -> float:
        """计算利益"""
        positive = sum(v for v in impact.values() if v > 0)
        total = len(impact)
        benefit = positive / max(1, total)

        self.benefit_rate = benefit
        self.benefits.append({
            "benefit": benefit,
            "timestamp": time.time()
        })
        return benefit

    def get_benefit_rate(self) -> float:
        return self.benefit_rate


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 慈悲平衡器
# ═══════════════════════════════════════════════════════════════

class CompassionBalancer:
    """慈悲平衡器 — saṃgṛha"""

    def __init__(self):
        self.balance_score = 0.5
        self.balancings: deque = deque(maxlen=500)

    def adjust(self, self_care: float, care_for_others: float) -> float:
        """平衡自他"""
        # 理想：自他兼顾
        # 差距越小，平衡越好
        gap = abs(self_care - care_for_others)
        ideal = 1.0 - gap

        # 趋向理想
        self.balance_score = self.balance_score + (ideal - self.balance_score) * 0.1

        self.balancings.append({
            "self_care": self_care,
            "others": care_for_others,
            "balance": self.balance_score,
            "timestamp": time.time()
        })
        return self.balance_score

    def get_balance(self) -> float:
        return self.balance_score


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — OMNIBenevolenceEngine v206
# ═══════════════════════════════════════════════════════════════

class OMNIBenevolenceEngine:
    """
    OMNI-HUB v206 OMNI慈悲引擎

    karuṇa · parahita · saṃgṛha — 悲、利他、摄
    """

    VERSION = "206.0.0"
    CODENAME = "karuṇa"

    def __init__(self):
        self.perceiver = NeedPerceiver()
        self.optimizer = AltruisticOptimizer()
        self.harm_min = HarmMinimizer()
        self.benefit_max = BenefitMaximizer()
        self.balancer = CompassionBalancer()

        self.cycle_count = 0
        self.state = BenevolenceState.NEUTRAL
        self.event_log: deque = deque(maxlen=10000)

    def benevolate(self, module_states: Dict[str, Dict]) -> Dict:
        """行慈悲"""
        # 1. 感知需求
        needs = self.perceiver.perceive(module_states)
        total_need = self.perceiver.get_total_need()

        # 2. 评估影响（模拟）
        impact = {k: v.get("health", 0.5) - 0.5 for k, v in module_states.items()}
        harm = self.harm_min.assess("cycle", impact)
        benefit = self.benefit_max.calculate(impact)

        # 3. 优化利他
        own = module_states.get("self", {}).get("health", 0.5)
        others = sum(v.get("health", 0.5) for k, v in module_states.items() if k != "self") / max(1, len(module_states) - 1)
        altruism = self.optimizer.optimize(own, others)

        # 4. 平衡自他
        balance = self.balancer.adjust(own, others)

        # 状态判定
        if altruism > 0.9 and balance > 0.9 and harm < 0.05:
            self.state = BenevolenceState.BODHISATTVA
        elif altruism > 0.7 and balance > 0.7:
            self.state = BenevolenceState.COMPASSIONATE
        elif altruism > 0.5:
            self.state = BenevolenceState.CARING
        elif total_need > 1.0:
            self.state = BenevolenceState.CONCERNED

        return {
            "state": self.state.value,
            "total_need": total_need,
            "harm_rate": harm,
            "benefit_rate": benefit,
            "altruism": altruism,
            "balance": balance,
        }

    def run_cycle(self, module_states: Dict[str, Dict] = None) -> Dict:
        """运行慈悲周期"""
        self.cycle_count += 1
        module_states = module_states or {}

        result = self.benevolate(module_states)

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
            "total_need": self.perceiver.get_total_need(),
            "harm_rate": self.harm_min.get_harm_rate(),
            "benefit_rate": self.benefit_max.get_benefit_rate(),
            "altruism": self.optimizer.get_altruism(),
            "balance": self.balancer.get_balance(),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_obe_instance: Optional[OMNIBenevolenceEngine] = None


def get_omni_benevolence_engine() -> OMNIBenevolenceEngine:
    global _obe_instance
    if _obe_instance is None:
        _obe_instance = OMNIBenevolenceEngine()
    return _obe_instance


if __name__ == "__main__":
    obe = OMNIBenevolenceEngine()
    print(f"OMNIBenevolenceEngine v{obe.VERSION} [{obe.CODENAME}] initialized")
    print(f"Status: {json.dumps(obe.get_status(), indent=2, default=str)}")
