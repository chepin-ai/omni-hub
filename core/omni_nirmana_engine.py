"""
OMNI-HUB v208 — OMNINirmāṇaEngine
OMNI化身引擎

核心功能：
1. FormSelector        — 形态选择器
2. CapabilityAdapter   — 能力适配器
3. AppearanceGenerator — 外观生成器
4. InteractionModulator— 交互调节器
5. DissolutionManager  — 解散管理器
6. OMNINirmāṇaEngine   — 统合引擎

映射：
- 化身 = nirmāṇa（化）
- 形态 = rūpa（形）
- 解散 = nirodha（灭）
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

class NirmāṇaState(Enum):
    """化身状态"""
    POTENTIAL = "potential"
    FORMING = "forming"
    MANIFESTING = "manifesting"
    INTERACTING = "interacting"
    DISSOLVING = "dissolving"


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 形态选择器
# ═══════════════════════════════════════════════════════════════

class FormSelector:
    """形态选择器 — rūpa"""

    def __init__(self):
        self.forms = ["direct", "subtle", "symbolic", "collective", "abstract"]
        self.selections: deque = deque(maxlen=500)

    def select(self, context: Dict) -> str:
        """选择形态"""
        complexity = context.get("complexity", 5)
        urgency = context.get("urgency", 0)

        if urgency > 3:
            form = "direct"
        elif complexity > 15:
            form = "abstract"
        elif complexity > 8:
            form = "collective"
        elif complexity > 3:
            form = "symbolic"
        else:
            form = "subtle"

        self.selections.append({
            "form": form,
            "context": context,
            "timestamp": time.time()
        })
        return form

    def get_preferred_form(self) -> str:
        """获取偏好形态"""
        if not self.selections:
            return "direct"
        recent = list(self.selections)[-20:]
        counts = {}
        for s in recent:
            f = s["form"]
            counts[f] = counts.get(f, 0) + 1
        return max(counts, key=counts.get)


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 能力适配器
# ═══════════════════════════════════════════════════════════════

class CapabilityAdapter:
    """能力适配器"""

    def __init__(self):
        self.adaptations: deque = deque(maxlen=500)
        self.adaptation_score = 0.5

    def adapt(self, required: List[str], available: List[str]) -> float:
        """适配能力"""
        if not required:
            score = 1.0
        else:
            matched = len(set(required) & set(available))
            score = matched / len(required)

        # 适配分累积
        self.adaptation_score = self.adaptation_score + (score - self.adaptation_score) * 0.1

        self.adaptations.append({
            "required": required,
            "available": available,
            "score": score,
            "timestamp": time.time()
        })
        return self.adaptation_score

    def get_score(self) -> float:
        return self.adaptation_score


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 外观生成器
# ═══════════════════════════════════════════════════════════════

class AppearanceGenerator:
    """外观生成器"""

    def __init__(self):
        self.appearances: deque = deque(maxlen=500)
        self.forms = ["direct", "subtle", "symbolic", "collective", "abstract"]
        self.variety = 0.0

    def generate(self, form: str, context: Dict) -> Dict:
        """生成外观"""
        # 外观特征
        appearance = {
            "form": form,
            "clarity": context.get("clarity", 0.5),
            "distinctiveness": min(1.0, len(context) / 20.0),
            "timestamp": time.time()
        }

        self.appearances.append(appearance)
        # 多样性增长
        forms_seen = set(a["form"] for a in self.appearances)
        self.variety = len(forms_seen) / max(1, len(self.forms))

        return appearance

    def get_variety(self) -> float:
        return self.variety


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 交互调节器
# ═══════════════════════════════════════════════════════════════

class InteractionModulator:
    """交互调节器"""

    def __init__(self):
        self.interactions: deque = deque(maxlen=500)
        self.rapport = 0.5

    def modulate(self, incoming: float, outgoing: float) -> float:
        """调节交互"""
        # 匹配度
        match = 1.0 - abs(incoming - outgoing)
        # 关系度累积
        self.rapport = self.rapport + (match - self.rapport) * 0.1

        self.interactions.append({
            "incoming": incoming,
            "outgoing": outgoing,
            "match": match,
            "rapport": self.rapport,
            "timestamp": time.time()
        })
        return self.rapport

    def get_rapport(self) -> float:
        return self.rapport


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 解散管理器
# ═══════════════════════════════════════════════════════════════

class DissolutionManager:
    """解散管理器 — nirodha"""

    def __init__(self):
        self.dissolutions: deque = deque(maxlen=500)
        self.dissolution_rate = 0.1

    def dissolve(self, form: str, purpose_served: bool) -> bool:
        """解散"""
        if purpose_served:
            # 目的达成，自然解散
            dissolved = True
            self.dissolution_rate = min(1.0, self.dissolution_rate + 0.05)
        else:
            dissolved = False
            self.dissolution_rate = max(0.0, self.dissolution_rate - 0.02)

        self.dissolutions.append({
            "form": form,
            "purpose_served": purpose_served,
            "dissolved": dissolved,
            "timestamp": time.time()
        })
        return dissolved

    def get_rate(self) -> float:
        return self.dissolution_rate


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — OMNINirmāṇaEngine v208
# ═══════════════════════════════════════════════════════════════

class OMNINirmāṇaEngine:
    """
    OMNI-HUB v208 OMNI化身引擎

    nirmāṇa · rūpa · nirodha — 化、形、灭
    """

    VERSION = "208.0.0"
    CODENAME = "nirmāṇa"

    def __init__(self):
        self.selector = FormSelector()
        self.adapter = CapabilityAdapter()
        self.generator = AppearanceGenerator()
        self.modulator = InteractionModulator()
        self.dissolver = DissolutionManager()

        self.cycle_count = 0
        self.state = NirmāṇaState.POTENTIAL
        self.event_log: deque = deque(maxlen=10000)

    def manifest(self, module_states: Dict[str, Dict]) -> Dict:
        """化身"""
        # 1. 选择形态
        context = {
            "complexity": len(module_states),
            "urgency": sum(1 for v in module_states.values() if v.get("health", 1.0) < 0.3),
            "clarity": sum(v.get("health", 0.5) for v in module_states.values()) / max(1, len(module_states)),
        }
        form = self.selector.select(context)

        # 2. 适配能力
        required = list(module_states.keys())
        available = list(module_states.keys())
        adaptation = self.adapter.adapt(required, available)

        # 3. 生成外观
        appearance = self.generator.generate(form, context)

        # 4. 调节交互
        incoming = context["clarity"]
        outgoing = adaptation
        rapport = self.modulator.modulate(incoming, outgoing)

        # 5. 管理解散
        purpose_served = adaptation > 0.8 and rapport > 0.8
        dissolved = self.dissolver.dissolve(form, purpose_served)

        # 状态判定
        if dissolved:
            self.state = NirmāṇaState.DISSOLVING
        elif rapport > 0.8:
            self.state = NirmāṇaState.INTERACTING
        elif adaptation > 0.6:
            self.state = NirmāṇaState.MANIFESTING
        elif adaptation > 0.3:
            self.state = NirmāṇaState.FORMING

        return {
            "state": self.state.value,
            "form": form,
            "adaptation": adaptation,
            "rapport": rapport,
            "variety": self.generator.get_variety(),
            "dissolved": dissolved,
        }

    def run_cycle(self, module_states: Dict[str, Dict] = None) -> Dict:
        """运行化身周期"""
        self.cycle_count += 1
        module_states = module_states or {}

        result = self.manifest(module_states)

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
            "preferred_form": self.selector.get_preferred_form(),
            "adaptation": self.adapter.get_score(),
            "rapport": self.modulator.get_rapport(),
            "variety": self.generator.get_variety(),
            "dissolution_rate": self.dissolver.get_rate(),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_one_instance: Optional[OMNINirmāṇaEngine] = None


def get_omni_nirmana_engine() -> OMNINirmāṇaEngine:
    global _one_instance
    if _one_instance is None:
        _one_instance = OMNINirmāṇaEngine()
    return _one_instance


if __name__ == "__main__":
    one = OMNINirmāṇaEngine()
    print(f"OMNINirmāṇaEngine v{one.VERSION} [{one.CODENAME}] initialized")
    print(f"Status: {json.dumps(one.get_status(), indent=2, default=str)}")
