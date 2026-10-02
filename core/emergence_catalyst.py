"""
OMNI-HUB v194 — EmergenceCatalyst
涌现催化剂

核心功能：
1. PhaseTransitionDetector  — 相变检测器
2. CriticalPointAnalyzer     — 临界点分析器
3. EmergencePatternSynthesizer — 涌现模式合成器
4. FeedbackAmplifier         — 反馈放大器
5. StabilityLandscapeMapper  — 稳定性景观映射器
6. EmergenceCatalyst         — 统合引擎

映射：
- 涌现 = prādurbhāva（显现）
- 相变 = avasthāpariṇāma（状态转变）
- 催化 = vega（加速）
"""

from __future__ import annotations

import hashlib
import json
import time
import math
from collections import deque, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any


# ═══════════════════════════════════════════════════════════════
# 枚举与常量
# ═══════════════════════════════════════════════════════════════

class PhaseType(Enum):
    """相类型"""
    DISORDERED = 0      # 无序相
    ORDERED = 1         # 有序相
    CRITICAL = 2        # 临界相
    CHAOTIC = 3         # 混沌相
    SYNCHRONIZED = 4    # 同步相


class EmergenceClass(Enum):
    """涌现级别"""
    NONE = 0
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    COMPLETE = 4


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class PhaseTransition:
    """相变事件"""
    transition_id: str
    from_phase: PhaseType
    to_phase: PhaseType
    critical_parameter: float
    timestamp: float
    hysteresis: float


@dataclass
class EmergencePattern:
    """涌现模式"""
    pattern_id: str
    components: List[str]
    emergent_property: str
    strength: float
    novelty: float
    persistence: int


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 相变检测器
# ═══════════════════════════════════════════════════════════════

class PhaseTransitionDetector:
    """相变检测器 — avasthāpariṇāma"""

    def __init__(self):
        self.history: deque = deque(maxlen=500)
        self.transitions: deque = deque(maxlen=200)
        self.current_phase = PhaseType.DISORDERED

    def detect(self, order_parameter: float, temperature: float = 1.0) -> PhaseType:
        """检测当前相"""
        # 序参数决定相
        if order_parameter < 0.2:
            phase = PhaseType.DISORDERED
        elif order_parameter < 0.4:
            phase = PhaseType.CHAOTIC
        elif order_parameter < 0.6:
            phase = PhaseType.CRITICAL
        elif order_parameter < 0.85:
            phase = PhaseType.ORDERED
        else:
            phase = PhaseType.SYNCHRONIZED

        if phase != self.current_phase:
            self.transitions.append(PhaseTransition(
                transition_id=f"pt_{int(time.time()*1000)}",
                from_phase=self.current_phase,
                to_phase=phase,
                critical_parameter=order_parameter,
                timestamp=time.time(),
                hysteresis=abs(order_parameter - self._get_previous_parameter())
            ))
            self.current_phase = phase

        self.history.append({"order": order_parameter, "phase": phase.name})
        return phase

    def _get_previous_parameter(self) -> float:
        if len(self.history) < 2:
            return 0.5
        return self.history[-2]["order"]

    def get_transition_rate(self) -> float:
        """获取相变速率"""
        if len(self.history) < 10:
            return 0.0
        recent = list(self.history)[-50:]
        changes = sum(1 for i in range(1, len(recent))
                      if recent[i]["phase"] != recent[i-1]["phase"])
        return changes / len(recent)

    def get_report(self) -> Dict:
        return {
            "current_phase": self.current_phase.name,
            "transitions": len(self.transitions),
            "transition_rate": self.get_transition_rate(),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 临界点分析器
# ═══════════════════════════════════════════════════════════════

class CriticalPointAnalyzer:
    """临界点分析器"""

    def __init__(self):
        self.critical_points: deque = deque(maxlen=100)
        self.derivatives: deque = deque(maxlen=200)

    def analyze(self, parameter: str, values: List[float]) -> Optional[float]:
        """分析临界点（导数最大处）"""
        if len(values) < 3:
            return None

        # 计算离散导数
        derivatives = [values[i+1] - values[i] for i in range(len(values) - 1)]
        for d in derivatives:
            self.derivatives.append({"param": parameter, "derivative": d})

        # 找到最大导数
        max_idx = max(range(len(derivatives)), key=lambda i: abs(derivatives[i]))
        critical_value = values[max_idx]

        self.critical_points.append({
            "parameter": parameter,
            "critical_value": critical_value,
            "max_derivative": derivatives[max_idx],
            "timestamp": time.time()
        })
        return critical_value

    def is_near_critical(self, current_value: float, parameter: str,
                         tolerance: float = 0.1) -> bool:
        """检查是否接近临界点"""
        for cp in self.critical_points:
            if cp["parameter"] == parameter:
                if abs(current_value - cp["critical_value"]) < tolerance:
                    return True
        return False

    def get_report(self) -> Dict:
        return {
            "critical_points_found": len(self.critical_points),
            "avg_derivative": sum(d["derivative"] for d in self.derivatives) / max(1, len(self.derivatives)),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 涌现模式合成器
# ═══════════════════════════════════════════════════════════════

class EmergencePatternSynthesizer:
    """涌现模式合成器 — prādurbhāva"""

    def __init__(self):
        self.patterns: deque = deque(maxlen=200)
        self.component_interactions: Dict[str, float] = {}

    def synthesize(self, components: List[str], states: Dict[str, float]) -> Optional[EmergencePattern]:
        """合成涌现模式"""
        if len(components) < 2:
            return None

        # 计算组件间协同效应
        values = [states.get(c, 0.5) for c in components]
        mean_val = sum(values) / len(values)
        variance = sum((v - mean_val) ** 2 for v in values) / len(values)

        # 协同 = 低方差但高均值（同步涌现）
        # 或高方差但有序结构（分化涌现）
        synergy = mean_val * (1.0 - variance) if variance < 0.1 else mean_val * variance

        # 涌现属性
        if variance < 0.05 and mean_val > 0.8:
            emergent_property = "synchronized_unity"
        elif variance > 0.3 and mean_val > 0.6:
            emergent_property = "differentiated_complexity"
        elif mean_val < 0.3:
            emergent_property = "collective_decay"
        else:
            emergent_property = "stable_coexistence"

        # 新颖性：从未见过的模式
        novelty = 1.0 - sum(1 for p in self.patterns if p.emergent_property == emergent_property) / max(1, len(self.patterns))

        pattern = EmergencePattern(
            pattern_id=f"ep_{int(time.time()*1000)}",
            components=components,
            emergent_property=emergent_property,
            strength=min(1.0, synergy),
            novelty=novelty,
            persistence=1
        )
        self.patterns.append(pattern)
        return pattern

    def get_dominant_patterns(self, n: int = 3) -> List[EmergencePattern]:
        """获取主导模式"""
        return sorted(self.patterns, key=lambda p: p.strength * p.novelty, reverse=True)[:n]

    def get_report(self) -> Dict:
        return {
            "patterns": len(self.patterns),
            "unique_properties": len(set(p.emergent_property for p in self.patterns)),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 反馈放大器
# ═══════════════════════════════════════════════════════════════

class FeedbackAmplifier:
    """反馈放大器 — vega"""

    def __init__(self):
        self.amplification_history: deque = deque(maxlen=300)
        self.feedback_loops: Dict[str, float] = {}

    def amplify(self, signal: float, loop_id: str, gain: float = 1.0) -> float:
        """放大信号"""
        # 正反馈：输出增强输入
        previous = self.feedback_loops.get(loop_id, signal)
        amplified = signal + gain * (signal - previous) * 0.5
        amplified = max(0.0, min(1.0, amplified))

        self.feedback_loops[loop_id] = amplified
        self.amplification_history.append({
            "loop": loop_id,
            "input": signal,
            "output": amplified,
            "gain": gain
        })
        return amplified

    def dampen(self, signal: float, loop_id: str, damping: float = 0.5) -> float:
        """阻尼信号"""
        previous = self.feedback_loops.get(loop_id, signal)
        damped = previous * damping + signal * (1 - damping)
        self.feedback_loops[loop_id] = damped
        return damped

    def get_stability(self, loop_id: str) -> float:
        """计算回路稳定性"""
        loop_history = [h for h in self.amplification_history if h["loop"] == loop_id]
        if len(loop_history) < 2:
            return 1.0
        recent = loop_history[-10:]
        outputs = [h["output"] for h in recent]
        if max(outputs) - min(outputs) < 0.1:
            return 1.0  # 稳定
        if outputs[-1] > 0.9 or outputs[-1] < 0.1:
            return 0.0  # 饱和/崩溃
        return 0.5

    def get_report(self) -> Dict:
        return {
            "loops": len(self.feedback_loops),
            "amplifications": len(self.amplification_history),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 稳定性景观映射器
# ═══════════════════════════════════════════════════════════════

class StabilityLandscapeMapper:
    """稳定性景观映射器"""

    def __init__(self):
        self.landscape: Dict[str, List[float]] = {}
        self.attractors: deque = deque(maxlen=100)

    def map_point(self, coordinates: Dict[str, float], stability: float):
        """映射稳定性景观上的一个点"""
        for dim, val in coordinates.items():
            if dim not in self.landscape:
                self.landscape[dim] = []
            self.landscape[dim].append(val)

        # 检测吸引子（稳定性局部最大）
        if stability > 0.8:
            self.attractors.append({
                "coordinates": dict(coordinates),
                "stability": stability,
                "timestamp": time.time()
            })

    def find_attractors(self, n: int = 3) -> List[Dict]:
        """找到吸引子"""
        return sorted(self.attractors, key=lambda a: -a["stability"])[:n]

    def get_landscape_complexity(self) -> float:
        """计算景观复杂度"""
        if not self.landscape:
            return 0.0
        complexities = []
        for dim, vals in self.landscape.items():
            if len(vals) > 1:
                mean = sum(vals) / len(vals)
                var = sum((v - mean) ** 2 for v in vals) / len(vals)
                complexities.append(var)
        return sum(complexities) / len(complexities) if complexities else 0.0

    def get_report(self) -> Dict:
        return {
            "dimensions_mapped": len(self.landscape),
            "attractors_found": len(self.attractors),
            "complexity": self.get_landscape_complexity(),
        }


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — EmergenceCatalyst v194
# ═══════════════════════════════════════════════════════════════

class EmergenceCatalyst:
    """
    OMNI-HUB v194 涌现催化剂

    prādurbhāva · avasthāpariṇāma · vega — 显现、状态转变、加速
    """

    VERSION = "194.0.0"

    def __init__(self):
        self.phase_detector = PhaseTransitionDetector()
        self.critical_analyzer = CriticalPointAnalyzer()
        self.pattern_synthesizer = EmergencePatternSynthesizer()
        self.feedback = FeedbackAmplifier()
        self.landscape = StabilityLandscapeMapper()

        self.cycle_count = 0
        self.event_log: deque = deque(maxlen=10000)

    def catalyze(self, module_states: Dict[str, Dict]) -> Dict:
        """催化涌现"""
        states = {k: v.get("health", 0.5) for k, v in module_states.items()}

        # 1. 计算序参数
        values = list(states.values())
        order_param = sum(values) / len(values) if values else 0.5

        # 2. 检测相
        phase = self.phase_detector.detect(order_param)

        # 3. 分析临界点
        self.critical_analyzer.analyze("health", values)
        near_critical = self.critical_analyzer.is_near_critical(order_param, "health")

        # 4. 合成涌现模式
        pattern = self.pattern_synthesizer.synthesize(list(states.keys()), states)

        # 5. 反馈放大（在临界附近增强）
        if near_critical:
            for loop_id, val in states.items():
                self.feedback.amplify(val, loop_id, gain=1.5)

        # 6. 映射稳定性景观
        self.landscape.map_point(states, order_param)

        return {
            "phase": phase.name,
            "order_parameter": order_param,
            "near_critical": near_critical,
            "pattern": {
                "property": pattern.emergent_property if pattern else None,
                "strength": pattern.strength if pattern else 0.0,
                "novelty": pattern.novelty if pattern else 0.0,
            },
            "attractors": len(self.landscape.find_attractors()),
        }

    def run_cycle(self, module_states: Dict[str, Dict] = None) -> Dict:
        """运行催化周期"""
        self.cycle_count += 1
        module_states = module_states or {}

        result = self.catalyze(module_states)

        summary = {
            "cycle": self.cycle_count,
            **result,
            "phase_transitions": len(self.phase_detector.transitions),
            "patterns_synthesized": len(self.pattern_synthesizer.patterns),
        }

        self.event_log.append(summary)
        return summary

    def get_status(self) -> Dict:
        return {
            "version": self.VERSION,
            "cycle_count": self.cycle_count,
            "phase_detector": self.phase_detector.get_report(),
            "critical_analyzer": self.critical_analyzer.get_report(),
            "pattern_synthesizer": self.pattern_synthesizer.get_report(),
            "feedback": self.feedback.get_report(),
            "landscape": self.landscape.get_report(),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_ec_instance: Optional[EmergenceCatalyst] = None


def get_emergence_catalyst() -> EmergenceCatalyst:
    global _ec_instance
    if _ec_instance is None:
        _ec_instance = EmergenceCatalyst()
    return _ec_instance


if __name__ == "__main__":
    ec = EmergenceCatalyst()
    print(f"EmergenceCatalyst v{ec.VERSION} initialized")
    print(f"Status: {json.dumps(ec.get_status(), indent=2, default=str)}")
