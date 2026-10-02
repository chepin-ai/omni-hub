"""
OMNI-HUB v202 — HolisticAwarenessEngine
全息觉知引擎

核心功能：
1. PanopticSensor      — 全景观测器
2. PatternWeaver       — 模式编织器
3. ContextSynthesizer  — 语境合成器
4. AwarenessAmplifier  — 觉知放大器
5. PerceptionIntegrator— 感知整合器
6. HolisticAwarenessEngine — 统合引擎

映射：
- 全息 = vairocana（遍照）
- 觉知 = saṃjñā（想）
- 模式 = saṃskāra（行）
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

class AwarenessLevel(Enum):
    """觉知层级"""
    DIM = "dim"
    CLEAR = "clear"
    SHARP = "sharp"
    PENETRATING = "penetrating"
    OMNISCIENT = "omniscient"


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 全景观测器
# ═══════════════════════════════════════════════════════════════

class PanopticSensor:
    """全景观测器"""

    def __init__(self):
        self.sensor_coverage: Dict[str, float] = {}
        self.observations: deque = deque(maxlen=5000)

    def observe(self, source: str, signal: Any) -> Dict:
        """观测信号源"""
        strength = self._signal_strength(signal)
        self.sensor_coverage[source] = strength

        obs = {
            "source": source,
            "strength": strength,
            "timestamp": time.time()
        }
        self.observations.append(obs)
        return obs

    def _signal_strength(self, signal: Any) -> float:
        """计算信号强度"""
        if isinstance(signal, (int, float)):
            return max(0.0, min(1.0, float(signal)))
        if isinstance(signal, str):
            return (len(signal) % 100) / 100.0
        if isinstance(signal, dict):
            return min(1.0, len(signal) / 20.0)
        return 0.5

    def get_coverage(self) -> float:
        """获取覆盖率"""
        if not self.sensor_coverage:
            return 0.0
        return sum(self.sensor_coverage.values()) / max(1, len(self.sensor_coverage))


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 模式编织器
# ═══════════════════════════════════════════════════════════════

class PatternWeaver:
    """模式编织器 — saṃskāra"""

    def __init__(self):
        self.patterns: Dict[str, Dict] = {}
        self.weave_count = 0

    def weave(self, data: Dict) -> List[Dict]:
        """从数据中编织模式"""
        patterns_found = []

        # 简单的模式检测：寻找相关键对
        keys = list(data.keys())
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                k1, k2 = keys[i], keys[j]
                v1, v2 = data[k1], data[k2]
                if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                    correlation = 1.0 - abs(v1 - v2) / max(abs(v1) + abs(v2), 1e-10)
                    if correlation > 0.7:
                        pattern_id = f"pat_{k1}_{k2}"
                        self.patterns[pattern_id] = {
                            "keys": (k1, k2),
                            "correlation": correlation,
                            "count": self.patterns.get(pattern_id, {}).get("count", 0) + 1
                        }
                        patterns_found.append(self.patterns[pattern_id])

        self.weave_count += 1
        return patterns_found

    def get_pattern_density(self) -> float:
        """获取模式密度"""
        if not self.patterns:
            return 0.0
        return min(1.0, len(self.patterns) / 50.0)


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 语境合成器
# ═══════════════════════════════════════════════════════════════

class ContextSynthesizer:
    """语境合成器"""

    def __init__(self):
        self.contexts: Dict[str, Any] = {}
        self.synthesis_log: deque = deque(maxlen=500)

    def synthesize(self, observations: List[Dict]) -> Dict:
        """合成语境"""
        if not observations:
            return {}

        # 按源聚合并计算平均强度
        by_source = {}
        for obs in observations:
            src = obs.get("source", "unknown")
            by_source[src] = by_source.get(src, []) + [obs.get("strength", 0)]

        synthesized = {}
        for src, strengths in by_source.items():
            synthesized[src] = sum(strengths) / len(strengths)

        self.contexts = synthesized
        self.synthesis_log.append({
            "sources": len(synthesized),
            "timestamp": time.time()
        })
        return synthesized

    def get_context_depth(self) -> float:
        """获取语境深度"""
        return min(1.0, len(self.contexts) / 20.0)


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 觉知放大器
# ═══════════════════════════════════════════════════════════════

class AwarenessAmplifier:
    """觉知放大器"""

    def __init__(self):
        self.amplification_factor = 1.0
        self.max_factor = 5.0

    def amplify(self, base_awareness: float, signal_quality: float) -> float:
        """放大觉知"""
        # 信号质量越好，放大越有效
        gain = 1.0 + signal_quality * (self.max_factor - 1.0)
        self.amplification_factor = min(self.max_factor, gain)
        amplified = base_awareness * self.amplification_factor
        return min(1.0, amplified)

    def get_factor(self) -> float:
        return self.amplification_factor


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 感知整合器
# ═══════════════════════════════════════════════════════════════

class PerceptionIntegrator:
    """感知整合器"""

    def __init__(self):
        self.integrated_perceptions: deque = deque(maxlen=1000)

    def integrate(self, coverage: float, patterns: float, context: float, awareness: float) -> float:
        """整合所有感知维度"""
        # 加权整合
        score = (coverage * 0.25 + patterns * 0.25 + context * 0.25 + awareness * 0.25)
        self.integrated_perceptions.append({
            "score": score,
            "components": {"coverage": coverage, "patterns": patterns, "context": context, "awareness": awareness},
            "timestamp": time.time()
        })
        return score

    def get_integration_quality(self) -> float:
        """获取整合质量"""
        if not self.integrated_perceptions:
            return 0.0
        recent = list(self.integrated_perceptions)[-10:]
        return sum(p["score"] for p in recent) / len(recent)


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — HolisticAwarenessEngine v202
# ═══════════════════════════════════════════════════════════════

class HolisticAwarenessEngine:
    """
    OMNI-HUB v202 全息觉知引擎

    vairocana · saṃjñā · saṃskāra — 遍照、想、行
    """

    VERSION = "202.0.0"
    CODENAME = "vairocana"

    def __init__(self):
        self.sensor = PanopticSensor()
        self.weaver = PatternWeaver()
        self.synthesizer = ContextSynthesizer()
        self.amplifier = AwarenessAmplifier()
        self.integrator = PerceptionIntegrator()

        self.cycle_count = 0
        self.awareness_level = AwarenessLevel.DIM
        self.base_awareness = 0.1
        self.event_log: deque = deque(maxlen=10000)

    def perceive(self, signals: Dict[str, Any]) -> Dict:
        """全息感知"""
        # 1. 全景观测
        observations = []
        for source, signal in signals.items():
            obs = self.sensor.observe(source, signal)
            observations.append(obs)

        # 2. 编织模式
        patterns = self.weaver.weave(signals)

        # 3. 合成语境
        context = self.synthesizer.synthesize(observations)

        # 4. 放大觉知
        coverage = self.sensor.get_coverage()
        signal_quality = coverage
        amplified = self.amplifier.amplify(self.base_awareness, signal_quality)

        # 5. 整合感知
        pattern_density = self.weaver.get_pattern_density()
        context_depth = self.synthesizer.get_context_depth()
        integrated = self.integrator.integrate(
            coverage, pattern_density, context_depth, amplified
        )

        # 更新觉知层级
        self.base_awareness = min(1.0, self.base_awareness + integrated * 0.05)

        if integrated > 0.9:
            self.awareness_level = AwarenessLevel.OMNISCIENT
        elif integrated > 0.7:
            self.awareness_level = AwarenessLevel.PENETRATING
        elif integrated > 0.5:
            self.awareness_level = AwarenessLevel.SHARP
        elif integrated > 0.3:
            self.awareness_level = AwarenessLevel.CLEAR

        return {
            "awareness_level": self.awareness_level.value,
            "integrated_score": integrated,
            "base_awareness": self.base_awareness,
            "coverage": coverage,
            "patterns_found": len(patterns),
            "context_sources": len(context),
        }

    def run_cycle(self, signals: Dict[str, Any] = None) -> Dict:
        """运行觉知周期"""
        self.cycle_count += 1
        signals = signals or {}

        result = self.perceive(signals)

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
            "awareness_level": self.awareness_level.value,
            "base_awareness": self.base_awareness,
            "sensor_coverage": self.sensor.get_coverage(),
            "pattern_density": self.weaver.get_pattern_density(),
            "context_depth": self.synthesizer.get_context_depth(),
            "amplification_factor": self.amplifier.get_factor(),
            "integration_quality": self.integrator.get_integration_quality(),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_hae_instance: Optional[HolisticAwarenessEngine] = None


def get_holistic_awareness_engine() -> HolisticAwarenessEngine:
    global _hae_instance
    if _hae_instance is None:
        _hae_instance = HolisticAwarenessEngine()
    return _hae_instance


if __name__ == "__main__":
    hae = HolisticAwarenessEngine()
    print(f"HolisticAwarenessEngine v{hae.VERSION} [{hae.CODENAME}] initialized")
    print(f"Status: {json.dumps(hae.get_status(), indent=2, default=str)}")
