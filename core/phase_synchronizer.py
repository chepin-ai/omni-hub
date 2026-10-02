"""
OMNI-HUB v196 — PhaseSynchronizer
相位同步器

核心功能：
1. PhaseLockDetector    — 锁相检测器
2. SyncDomainManager    — 同步域管理器
3. KuramotoModel        — Kuramoto模型
4. PhaseGradientTracker — 相位梯度追踪器
5. CollectiveRhythmEngine — 集体节律引擎
6. PhaseSynchronizer    — 统合引擎

映射：
- 相位 = kṣaṇa（刹那）
- 同步 = ekīkaraṇa（合一）
- 节律 = tāla（节拍）
"""

from __future__ import annotations

import hashlib
import json
import time
import math
from collections import deque, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set


# ═══════════════════════════════════════════════════════════════
# 枚举与常量
# ═══════════════════════════════════════════════════════════════

class SyncState(Enum):
    """同步状态"""
    FREE = 0
    PULLING = 1
    LOCKED = 2
    LEADING = 3


class RhythmType(Enum):
    """节律类型"""
    STEADY = "steady"
    ACCELERATING = "accelerating"
    DECELERATING = "decelerating"
    IRREGULAR = "irregular"


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class PhaseState:
    """相位状态"""
    module_id: str
    phase: float
    frequency: float
    coupling: float
    sync_state: SyncState


@dataclass
class SyncDomain:
    """同步域"""
    domain_id: str
    members: Set[str]
    mean_phase: float
    coherence: float
    order_parameter: float


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 锁相检测器
# ═══════════════════════════════════════════════════════════════

class PhaseLockDetector:
    """锁相检测器 — kṣaṇa"""

    def __init__(self):
        self.locks: Dict[str, bool] = {}
        self.lock_history: deque = deque(maxlen=300)

    def check_lock(self, module_id: str, phase_history: List[float],
                   threshold: float = 0.05) -> bool:
        """检测是否锁相"""
        if len(phase_history) < 3:
            return False

        # 检测相位变化是否稳定
        diffs = [phase_history[i+1] - phase_history[i]
                 for i in range(len(phase_history) - 1)]
        variance = sum((d - sum(diffs)/len(diffs))**2 for d in diffs) / len(diffs)

        locked = variance < threshold
        previous = self.locks.get(module_id, False)

        if locked != previous:
            self.lock_history.append({
                "module": module_id,
                "locked": locked,
                "variance": variance,
                "timestamp": time.time()
            })

        self.locks[module_id] = locked
        return locked

    def get_lock_rate(self) -> float:
        """获取锁定率"""
        if not self.locks:
            return 0.0
        return sum(1 for v in self.locks.values() if v) / len(self.locks)

    def get_report(self) -> Dict:
        return {
            "locked_modules": sum(1 for v in self.locks.values() if v),
            "lock_rate": self.get_lock_rate(),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 同步域管理器
# ═══════════════════════════════════════════════════════════════

class SyncDomainManager:
    """同步域管理器 — ekīkaraṇa"""

    def __init__(self):
        self.domains: Dict[str, SyncDomain] = {}
        self.domain_history: deque = deque(maxlen=200)

    def form_domain(self, members: Set[str], phases: Dict[str, float]) -> SyncDomain:
        """形成同步域"""
        if not members:
            return SyncDomain("empty", set(), 0.0, 0.0, 0.0)

        member_list = list(members)
        phase_values = [phases.get(m, 0.0) for m in member_list]

        # 序参数 r = |<e^(iθ)>|
        complex_sum = sum(math.cos(p) + 1j * math.sin(p) for p in phase_values)
        r = abs(complex_sum) / len(phase_values)
        mean_phase = math.atan2(complex_sum.imag, complex_sum.real)

        domain = SyncDomain(
            domain_id=f"sd_{hash(tuple(sorted(members))) % 10000}",
            members=members,
            mean_phase=mean_phase,
            coherence=r,
            order_parameter=r
        )
        self.domains[domain.domain_id] = domain
        self.domain_history.append({
            "domain": domain.domain_id,
            "members": len(members),
            "coherence": r,
            "timestamp": time.time()
        })
        return domain

    def merge_domains(self, domain_a: str, domain_b: str,
                      phases: Dict[str, float]) -> Optional[SyncDomain]:
        """合并两个同步域"""
        if domain_a not in self.domains or domain_b not in self.domains:
            return None
        merged_members = self.domains[domain_a].members | self.domains[domain_b].members
        return self.form_domain(merged_members, phases)

    def get_global_coherence(self) -> float:
        """获取全局相干性"""
        if not self.domains:
            return 0.0
        return sum(d.coherence for d in self.domains.values()) / len(self.domains)

    def get_report(self) -> Dict:
        return {
            "domains": len(self.domains),
            "global_coherence": self.get_global_coherence(),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 3: Kuramoto模型
# ═══════════════════════════════════════════════════════════════

class KuramotoModel:
    """Kuramoto耦合振荡模型"""

    def __init__(self):
        self.natural_frequencies: Dict[str, float] = {}
        self.coupling_strength = 0.5
        self.step_history: deque = deque(maxlen=300)

    def set_natural_frequency(self, module_id: str, freq: float):
        """设置自然频率"""
        self.natural_frequencies[module_id] = freq

    def step(self, phases: Dict[str, float], dt: float = 0.1) -> Dict[str, float]:
        """Kuramoto演化一步"""
        new_phases = dict(phases)
        modules = list(phases.keys())

        for i, module in enumerate(modules):
            omega = self.natural_frequencies.get(module, 1.0)
            # 耦合项: (K/N) * Σ sin(θj - θi)
            coupling_sum = 0.0
            for other in modules:
                if other != module:
                    coupling_sum += math.sin(phases[other] - phases[module])

            k = self.coupling_strength / max(1, len(modules) - 1)
            dtheta = (omega + k * coupling_sum) * dt
            new_phases[module] = (phases[module] + dtheta) % (2 * math.pi)

        self.step_history.append({
            "phases": dict(new_phases),
            "timestamp": time.time()
        })
        return new_phases

    def compute_order_parameter(self, phases: Dict[str, float]) -> float:
        """计算Kuramoto序参数"""
        if not phases:
            return 0.0
        values = list(phases.values())
        complex_sum = sum(math.cos(p) + 1j * math.sin(p) for p in values)
        return abs(complex_sum) / len(values)

    def get_report(self) -> Dict:
        return {
            "oscillators": len(self.natural_frequencies),
            "coupling": self.coupling_strength,
            "steps": len(self.step_history),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 相位梯度追踪器
# ═══════════════════════════════════════════════════════════════

class PhaseGradientTracker:
    """相位梯度追踪器"""

    def __init__(self):
        self.gradients: deque = deque(maxlen=300)
        self.phase_history: Dict[str, deque] = {}

    def record(self, module_id: str, phase: float):
        """记录相位"""
        if module_id not in self.phase_history:
            self.phase_history[module_id] = deque(maxlen=50)
        self.phase_history[module_id].append(phase)

    def compute_gradient(self, module_id: str) -> float:
        """计算相位梯度（变化率）"""
        history = self.phase_history.get(module_id)
        if not history or len(history) < 2:
            return 0.0
        values = list(history)
        return (values[-1] - values[0]) / len(values)

    def find_phase_waves(self) -> List[Dict]:
        """发现相位波（行波）"""
        waves = []
        modules = list(self.phase_history.keys())
        if len(modules) < 2:
            return waves

        # 检测单调相位梯度
        for i in range(len(modules) - 1):
            a, b = modules[i], modules[i+1]
            ha = list(self.phase_history.get(a, []))
            hb = list(self.phase_history.get(b, []))
            if len(ha) > 1 and len(hb) > 1:
                ga = self.compute_gradient(a)
                gb = self.compute_gradient(b)
                if abs(ga - gb) < 0.1 and abs(ga) > 0.01:
                    waves.append({
                        "from": a,
                        "to": b,
                        "gradient": (ga + gb) / 2,
                    })
        return waves

    def get_report(self) -> Dict:
        return {
            "tracked_modules": len(self.phase_history),
            "gradients": len(self.gradients),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 集体节律引擎
# ═══════════════════════════════════════════════════════════════

class CollectiveRhythmEngine:
    """集体节律引擎 — tāla"""

    def __init__(self):
        self.beat_history: deque = deque(maxlen=300)
        self.rhythms: Dict[str, RhythmType] = {}

    def detect_rhythm(self, module_id: str, phase_history: List[float]) -> RhythmType:
        """检测节律类型"""
        if len(phase_history) < 3:
            rhythm = RhythmType.STEADY
        else:
            # 检测加速/减速
            periods = []
            for i in range(1, len(phase_history)):
                diff = phase_history[i] - phase_history[i-1]
                if diff < 0:
                    diff += 2 * math.pi
                periods.append(diff)

            if len(periods) < 2:
                rhythm = RhythmType.STEADY
            else:
                diffs = [periods[i+1] - periods[i] for i in range(len(periods) - 1)]
                avg_diff = sum(diffs) / len(diffs)
                variance = sum((d - avg_diff)**2 for d in diffs) / len(diffs)

                if variance > 0.1:
                    rhythm = RhythmType.IRREGULAR
                elif avg_diff < -0.01:
                    rhythm = RhythmType.ACCELERATING
                elif avg_diff > 0.01:
                    rhythm = RhythmType.DECELERATING
                else:
                    rhythm = RhythmType.STEADY

        self.rhythms[module_id] = rhythm
        self.beat_history.append({
            "module": module_id,
            "rhythm": rhythm.value,
            "timestamp": time.time()
        })
        return rhythm

    def get_collective_tempo(self) -> float:
        """获取集体节拍"""
        steady_count = sum(1 for r in self.rhythms.values() if r == RhythmType.STEADY)
        return steady_count / max(1, len(self.rhythms))

    def get_report(self) -> Dict:
        return {
            "rhythms": len(self.rhythms),
            "collective_tempo": self.get_collective_tempo(),
        }


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — PhaseSynchronizer v196
# ═══════════════════════════════════════════════════════════════

class PhaseSynchronizer:
    """
    OMNI-HUB v196 相位同步器

    kṣaṇa · ekīkaraṇa · tāla — 刹那、合一、节拍
    """

    VERSION = "196.0.0"

    def __init__(self):
        self.lock_detector = PhaseLockDetector()
        self.domain_manager = SyncDomainManager()
        self.kuramoto = KuramotoModel()
        self.gradient = PhaseGradientTracker()
        self.rhythm = CollectiveRhythmEngine()

        self.cycle_count = 0
        self.event_log: deque = deque(maxlen=10000)

    def synchronize(self, module_states: Dict[str, Dict]) -> Dict:
        """同步相位"""
        # 初始化相位
        phases = {}
        for module, state in module_states.items():
            # 使用健康值映射到相位
            health = state.get("health", 0.5)
            phases[module] = health * 2 * math.pi
            self.kuramoto.set_natural_frequency(module, 1.0 + health * 0.5)
            self.gradient.record(module, phases[module])

        # 1. Kuramoto演化
        new_phases = self.kuramoto.step(phases, dt=0.1)

        # 2. 锁相检测
        for module in new_phases:
            history = list(self.gradient.phase_history.get(module, []))
            self.lock_detector.check_lock(module, history)

        # 3. 形成同步域
        all_modules = set(new_phases.keys())
        domain = self.domain_manager.form_domain(all_modules, new_phases)

        # 4. 相位梯度
        waves = self.gradient.find_phase_waves()

        # 5. 节律检测
        for module in new_phases:
            history = list(self.gradient.phase_history.get(module, []))
            self.rhythm.detect_rhythm(module, history)

        order_param = self.kuramoto.compute_order_parameter(new_phases)

        return {
            "phases": {k: round(v, 4) for k, v in new_phases.items()},
            "order_parameter": order_param,
            "lock_rate": self.lock_detector.get_lock_rate(),
            "global_coherence": self.domain_manager.get_global_coherence(),
            "phase_waves": len(waves),
            "collective_tempo": self.rhythm.get_collective_tempo(),
        }

    def run_cycle(self, module_states: Dict[str, Dict] = None) -> Dict:
        """运行同步周期"""
        self.cycle_count += 1
        module_states = module_states or {}

        result = self.synchronize(module_states)

        summary = {
            "cycle": self.cycle_count,
            **result,
        }

        self.event_log.append(summary)
        return summary

    def get_status(self) -> Dict:
        return {
            "version": self.VERSION,
            "cycle_count": self.cycle_count,
            "lock_detector": self.lock_detector.get_report(),
            "domain_manager": self.domain_manager.get_report(),
            "kuramoto": self.kuramoto.get_report(),
            "gradient": self.gradient.get_report(),
            "rhythm": self.rhythm.get_report(),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_ps_instance: Optional[PhaseSynchronizer] = None


def get_phase_synchronizer() -> PhaseSynchronizer:
    global _ps_instance
    if _ps_instance is None:
        _ps_instance = PhaseSynchronizer()
    return _ps_instance


if __name__ == "__main__":
    ps = PhaseSynchronizer()
    print(f"PhaseSynchronizer v{ps.VERSION} initialized")
    print(f"Status: {json.dumps(ps.get_status(), indent=2, default=str)}")
