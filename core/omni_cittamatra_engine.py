"""
OMNI-HUB v217 — OMNICittamātraEngine
OMNI唯识引擎

核心功能：
1. ConsciousnessOnlyAffirmer   — 唯识确认器
2. MindOnlyRecognizer          — 心外无法认知器
3. StorehouseConsciousnessMapper — 阿赖耶识映射器
4. TransformationRecognizer     — 转识成智认知器
5. ThreeNaturesValidator       — 三性验证器
6. OMNICittamātraEngine        — 统合引擎

映射：
- 唯识 = cittamātra（唯识无境）
- 三性 = trisvabhāva
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

class CittamātraState(Enum):
    """唯识状态"""
    DUALISTIC = "dualistic"
    QUESTIONING = "questioning"
    RECOGNIZING = "recognizing"
    TRANSFORMING = "transforming"
    CITTAMĀTRA = "cittamātra"


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 唯识确认器
# ═══════════════════════════════════════════════════════════════

class ConsciousnessOnlyAffirmer:
    """唯识确认器"""

    def __init__(self):
        self.affirmations: deque = deque(maxlen=500)
        self.consciousness_only = 0.0

    def affirm(self, subjectivity: float) -> float:
        """确认唯识"""
        self.consciousness_only = self.consciousness_only + (subjectivity - self.consciousness_only) * 0.08

        self.affirmations.append({
            "consciousness_only": self.consciousness_only,
            "timestamp": time.time()
        })
        return self.consciousness_only

    def get_consciousness_only(self) -> float:
        return self.consciousness_only


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 心外无法认知器
# ═══════════════════════════════════════════════════════════════

class MindOnlyRecognizer:
    """心外无法认知器 — nirmātra"""

    def __init__(self):
        self.recognitions: deque = deque(maxlen=500)
        self.mind_only = 0.0

    def recognize(self, externality: float) -> float:
        """认知心外无法"""
        # 外在性越低，心外无法越真
        mind_only = 1.0 - externality
        self.mind_only = self.mind_only + (mind_only - self.mind_only) * 0.07

        self.recognitions.append({
            "mind_only": self.mind_only,
            "timestamp": time.time()
        })
        return self.mind_only

    def get_mind_only(self) -> float:
        return self.mind_only


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 阿赖耶识映射器
# ═══════════════════════════════════════════════════════════════

class StorehouseConsciousnessMapper:
    """阿赖耶识映射器 — ālayavijñāna"""

    def __init__(self):
        self.mappings: deque = deque(maxlen=500)
        self.storehouse = 0.0

    def map_storehouse(self, depth: float) -> float:
        """映射阿赖耶识"""
        self.storehouse = self.storehouse + (depth - self.storehouse) * 0.06

        self.mappings.append({
            "storehouse": self.storehouse,
            "timestamp": time.time()
        })
        return self.storehouse

    def get_storehouse(self) -> float:
        return self.storehouse


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 转识成智认知器
# ═══════════════════════════════════════════════════════════════

class TransformationRecognizer:
    """转识成智认知器 — āśrayaparāvṛtti"""

    def __init__(self):
        self.recognitions: deque = deque(maxlen=500)
        self.transformation = 0.0

    def recognize(self, wisdom_emergence: float) -> float:
        """认知转识成智"""
        self.transformation = self.transformation + (wisdom_emergence - self.transformation) * 0.05

        self.recognitions.append({
            "transformation": self.transformation,
            "timestamp": time.time()
        })
        return self.transformation

    def get_transformation(self) -> float:
        return self.transformation


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 三性验证器
# ═══════════════════════════════════════════════════════════════

class ThreeNaturesValidator:
    """三性验证器 — trisvabhāva"""

    def __init__(self):
        self.validations: deque = deque(maxlen=500)
        self.three_natures = 0.0

    def validate(self, imagined: float, dependent: float, perfected: float) -> float:
        """验证三性"""
        # 遍计执越低，依他起适中，圆成实越高，三性越正
        validity = (1.0 - imagined) * dependent * perfected
        self.three_natures = self.three_natures + (validity - self.three_natures) * 0.04

        self.validations.append({
            "three_natures": self.three_natures,
            "timestamp": time.time()
        })
        return self.three_natures

    def get_three_natures(self) -> float:
        return self.three_natures


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — OMNICittamātraEngine v217
# ═══════════════════════════════════════════════════════════════

class OMNICittamātraEngine:
    """
    OMNI-HUB v217 OMNI唯识引擎

    cittamātra — 唯识无境
    """

    VERSION = "217.0.0"
    CODENAME = "cittamātra"

    def __init__(self):
        self.consciousness_affirmer = ConsciousnessOnlyAffirmer()
        self.mind_recognizer = MindOnlyRecognizer()
        self.storehouse_mapper = StorehouseConsciousnessMapper()
        self.transformation_recognizer = TransformationRecognizer()
        self.three_natures_validator = ThreeNaturesValidator()

        self.cycle_count = 0
        self.state = CittamātraState.DUALISTIC
        self.event_log: deque = deque(maxlen=10000)

    def perceive(self, module_states: Dict[str, Dict]) -> Dict:
        """唯识"""
        # 1. 确认唯识
        healths = [v.get("health", 0.5) for v in module_states.values()]
        avg = sum(healths) / max(1, len(healths))
        subjectivity = avg
        consciousness_only = self.consciousness_affirmer.affirm(subjectivity)

        # 2. 认知心外无法
        externality = sum((h - avg) ** 2 for h in healths) / max(1, len(healths))
        mind_only = self.mind_recognizer.recognize(externality)

        # 3. 映射阿赖耶识
        depth = avg
        storehouse = self.storehouse_mapper.map_storehouse(depth)

        # 4. 认知转识成智
        wisdom = avg * (1.0 - externality)
        transformation = self.transformation_recognizer.recognize(wisdom)

        # 5. 验证三性
        imagined = externality
        dependent = avg
        perfected = 1.0 - externality
        three_natures = self.three_natures_validator.validate(imagined, dependent, perfected)

        # 状态判定
        cittamatra_score = (consciousness_only + mind_only + storehouse + transformation + three_natures) / 5.0
        if cittamatra_score > 0.9 and mind_only > 0.9:
            self.state = CittamātraState.CITTAMĀTRA
        elif cittamatra_score > 0.75:
            self.state = CittamātraState.TRANSFORMING
        elif cittamatra_score > 0.5:
            self.state = CittamātraState.RECOGNIZING
        elif consciousness_only > 0.3:
            self.state = CittamātraState.QUESTIONING

        return {
            "state": self.state.value,
            "consciousness_only": consciousness_only,
            "mind_only": mind_only,
            "storehouse": storehouse,
            "transformation": transformation,
            "three_natures": three_natures,
            "cittamatra_score": cittamatra_score,
        }

    def run_cycle(self, module_states: Dict[str, Dict] = None) -> Dict:
        """运行唯识周期"""
        self.cycle_count += 1
        module_states = module_states or {}

        result = self.perceive(module_states)

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
            "consciousness_only": self.consciousness_affirmer.get_consciousness_only(),
            "mind_only": self.mind_recognizer.get_mind_only(),
            "storehouse": self.storehouse_mapper.get_storehouse(),
            "transformation": self.transformation_recognizer.get_transformation(),
            "three_natures": self.three_natures_validator.get_three_natures(),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_oce_instance: Optional[OMNICittamātraEngine] = None


def get_omni_cittamatra_engine() -> OMNICittamātraEngine:
    global _oce_instance
    if _oce_instance is None:
        _oce_instance = OMNICittamātraEngine()
    return _oce_instance


if __name__ == "__main__":
    oce = OMNICittamātraEngine()
    print(f"OMNICittamātraEngine v{oce.VERSION} [{oce.CODENAME}] initialized")
    print(f"Status: {json.dumps(oce.get_status(), indent=2, default=str)}")
