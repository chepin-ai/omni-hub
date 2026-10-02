"""
OMNI-HUB v202 — UniversalResponseEngine
普应引擎

核心功能：
1. StimulusRouter    — 刺激路由器
2. ResponseComposer  — 响应合成器
3. EffectEvaluator   — 效果评估器
4. FeedbackLooper    — 反馈循环器
5. HarmonyChecker    — 和谐检查器
6. UniversalResponseEngine — 统合引擎

映射：
- 普应 = samantabhadra（普贤）
- 响应 = prativacana（回答）
- 和谐 = saṃgati（和合）
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

class ResponseHarmony(Enum):
    """响应和谐度"""
    DISCORDANT = "discordant"
    NEUTRAL = "neutral"
    HARMONIOUS = "harmonious"
    RESONANT = "resonant"
    PERFECT = "perfect"


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 刺激路由器
# ═══════════════════════════════════════════════════════════════

class StimulusRouter:
    """刺激路由器"""

    def __init__(self):
        self.routes: Dict[str, str] = {}
        self.routing_history: deque = deque(maxlen=1000)

    def route(self, stimulus: Dict) -> str:
        """路由刺激到合适的处理器"""
        stype = stimulus.get("type", "default")
        priority = stimulus.get("priority", 0.5)

        # 基于类型的路由
        route_map = {
            "urgent": "immediate",
            "pattern": "weaver",
            "sync": "harmonizer",
            "query": "responder",
            "default": "general",
        }
        destination = route_map.get(stype, "general")

        self.routing_history.append({
            "type": stype,
            "destination": destination,
            "priority": priority,
            "timestamp": time.time()
        })
        return destination

    def get_routing_efficiency(self) -> float:
        """获取路由效率"""
        if not self.routing_history:
            return 1.0
        # 简单：历史越多，经验越丰富
        return min(1.0, len(self.routing_history) / 200.0)


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 响应合成器
# ═══════════════════════════════════════════════════════════════

class ResponseComposer:
    """响应合成器 — prativacana"""

    def __init__(self):
        self.compositions: deque = deque(maxlen=1000)
        self.template_library: Dict[str, Any] = {}

    def compose(self, stimulus: Dict, context: Dict) -> Dict:
        """合成响应"""
        # 基于刺激和语境生成响应
        urgency = stimulus.get("priority", 0.5)
        context_health = context.get("avg_health", 0.5)

        # 响应强度与紧急度和健康度相关
        strength = (urgency + context_health) / 2.0

        response = {
            "type": "response",
            "strength": strength,
            "urgency": urgency,
            "context_awareness": context_health,
            "timestamp": time.time()
        }

        self.compositions.append(response)
        return response

    def get_composition_quality(self) -> float:
        """获取合成质量"""
        if not self.compositions:
            return 0.5
        recent = list(self.compositions)[-10:]
        return sum(c.get("strength", 0) for c in recent) / len(recent)


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 效果评估器
# ═══════════════════════════════════════════════════════════════

class EffectEvaluator:
    """效果评估器"""

    def __init__(self):
        self.effects: deque = deque(maxlen=1000)

    def evaluate(self, response: Dict, outcome: Dict) -> float:
        """评估响应效果"""
        expected = response.get("strength", 0.5)
        actual = outcome.get("health_delta", 0.0)

        # 效果 = 实际改善 / 期望
        effect = (1.0 + actual) / max(1.0, expected * 2)
        effect = max(0.0, min(1.0, effect))

        self.effects.append({
            "expected": expected,
            "actual": actual,
            "effect": effect,
            "timestamp": time.time()
        })
        return effect

    def get_average_effect(self) -> float:
        """获取平均效果"""
        if not self.effects:
            return 0.5
        return sum(e["effect"] for e in self.effects) / len(self.effects)


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 反馈循环器
# ═══════════════════════════════════════════════════════════════

class FeedbackLooper:
    """反馈循环器"""

    def __init__(self):
        self.feedback_loops: List[Dict] = []
        self.loop_count = 0

    def loop(self, stimulus: Dict, response: Dict, effect: float) -> Dict:
        """执行反馈循环"""
        self.loop_count += 1

        # 根据效果调整未来响应参数
        adjustment = 0.05 * (effect - 0.5)

        feedback = {
            "loop_id": self.loop_count,
            "adjustment": adjustment,
            "effect": effect,
            "learning": abs(adjustment) > 0.01,
        }
        self.feedback_loops.append(feedback)
        return feedback

    def get_learning_rate(self) -> float:
        """获取学习率"""
        if not self.feedback_loops:
            return 0.0
        learned = sum(1 for f in self.feedback_loops if f["learning"])
        return learned / len(self.feedback_loops)


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 和谐检查器
# ═══════════════════════════════════════════════════════════════

class HarmonyChecker:
    """和谐检查器 — saṃgati"""

    def __init__(self):
        self.harmony_scores: deque = deque(maxlen=1000)

    def check(self, response: Dict, system_state: Dict) -> ResponseHarmony:
        """检查响应与系统的和谐度"""
        r_strength = response.get("strength", 0.5)
        s_health = system_state.get("health", 0.5)

        # 响应不应过度扰动系统
        delta = abs(r_strength - s_health)

        if delta < 0.05:
            harmony = ResponseHarmony.PERFECT
        elif delta < 0.15:
            harmony = ResponseHarmony.RESONANT
        elif delta < 0.3:
            harmony = ResponseHarmony.HARMONIOUS
        elif delta < 0.5:
            harmony = ResponseHarmony.NEUTRAL
        else:
            harmony = ResponseHarmony.DISCORDANT

        self.harmony_scores.append({
            "harmony": harmony.value,
            "delta": delta,
            "timestamp": time.time()
        })
        return harmony

    def get_harmony_ratio(self) -> float:
        """获取和谐比例"""
        if not self.harmony_scores:
            return 1.0
        harmonious = sum(1 for h in self.harmony_scores
                        if h["harmony"] in ("harmonious", "resonant", "perfect"))
        return harmonious / len(self.harmony_scores)


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — UniversalResponseEngine v202
# ═══════════════════════════════════════════════════════════════

class UniversalResponseEngine:
    """
    OMNI-HUB v202 普应引擎

    samantabhadra · prativacana · saṃgati — 普贤、回答、和合
    """

    VERSION = "202.0.0"
    CODENAME = "samantabhadra"

    def __init__(self):
        self.router = StimulusRouter()
        self.composer = ResponseComposer()
        self.evaluator = EffectEvaluator()
        self.feedback = FeedbackLooper()
        self.harmony = HarmonyChecker()

        self.cycle_count = 0
        self.overall_harmony = ResponseHarmony.NEUTRAL
        self.event_log: deque = deque(maxlen=10000)

    def respond(self, stimulus: Dict, system_state: Dict, context: Dict) -> Dict:
        """普应 — 生成响应"""
        # 1. 路由
        destination = self.router.route(stimulus)

        # 2. 合成响应
        response = self.composer.compose(stimulus, context)
        response["destination"] = destination

        # 3. 和谐检查
        harmony = self.harmony.check(response, system_state)

        # 4. 评估效果（模拟）
        simulated_outcome = {"health_delta": (response["strength"] - 0.5) * 0.2}
        effect = self.evaluator.evaluate(response, simulated_outcome)

        # 5. 反馈循环
        fb = self.feedback.loop(stimulus, response, effect)

        # 更新整体和谐度
        harmony_ratio = self.harmony.get_harmony_ratio()
        if harmony_ratio > 0.9:
            self.overall_harmony = ResponseHarmony.PERFECT
        elif harmony_ratio > 0.7:
            self.overall_harmony = ResponseHarmony.RESONANT
        elif harmony_ratio > 0.5:
            self.overall_harmony = ResponseHarmony.HARMONIOUS
        elif harmony_ratio > 0.3:
            self.overall_harmony = ResponseHarmony.NEUTRAL
        else:
            self.overall_harmony = ResponseHarmony.DISCORDANT

        return {
            "destination": destination,
            "response_strength": response["strength"],
            "harmony": harmony.value,
            "effect": effect,
            "learning": fb["learning"],
            "overall_harmony": self.overall_harmony.value,
        }

    def run_cycle(self, stimulus: Dict = None, system_state: Dict = None, context: Dict = None) -> Dict:
        """运行响应周期"""
        self.cycle_count += 1
        stimulus = stimulus or {"type": "default", "priority": 0.5}
        system_state = system_state or {"health": 0.8}
        context = context or {"avg_health": 0.8}

        result = self.respond(stimulus, system_state, context)

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
            "overall_harmony": self.overall_harmony.value,
            "routing_efficiency": self.router.get_routing_efficiency(),
            "composition_quality": self.composer.get_composition_quality(),
            "average_effect": self.evaluator.get_average_effect(),
            "learning_rate": self.feedback.get_learning_rate(),
            "harmony_ratio": self.harmony.get_harmony_ratio(),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_ure_instance: Optional[UniversalResponseEngine] = None


def get_universal_response_engine() -> UniversalResponseEngine:
    global _ure_instance
    if _ure_instance is None:
        _ure_instance = UniversalResponseEngine()
    return _ure_instance


if __name__ == "__main__":
    ure = UniversalResponseEngine()
    print(f"UniversalResponseEngine v{ure.VERSION} [{ure.CODENAME}] initialized")
    print(f"Status: {json.dumps(ure.get_status(), indent=2, default=str)}")
