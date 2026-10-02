"""
OMNI-HUB v197 — ChaosInjector
混沌注入器

核心功能：
1. FaultInjector       — 故障注入器
2. CascadeSimulator    — 级联模拟器
3. RecoveryTester      — 恢复测试器
4. PerturbationEngine  — 扰动引擎
5. StabilityAssessor   — 稳定性评估器
6. ChaosInjector       — 统合引擎

映射：
- 混沌 = saṅkāra（乱动）
- 故障 = doṣa（过失）
- 恢复 = punaḥsthāna（复位）
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

class FaultType(Enum):
    """故障类型"""
    CRASH = "crash"
    DELAY = "delay"
    CORRUPTION = "corruption"
    PARTITION = "partition"
    OVERLOAD = "overload"


class RecoveryMode(Enum):
    """恢复模式"""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    GRACEFUL = "graceful"
    HARD = "hard"


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class Fault:
    """故障事件"""
    fault_id: str
    fault_type: FaultType
    target: str
    severity: float
    injected_at: float
    recovered_at: Optional[float] = None


@dataclass
class CascadeEvent:
    """级联事件"""
    event_id: str
    source: str
    affected: List[str]
    depth: int
    total_impact: float


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 故障注入器
# ═══════════════════════════════════════════════════════════════

class FaultInjector:
    """故障注入器 — doṣa"""

    def __init__(self):
        self.faults: deque = deque(maxlen=300)
        self.active_faults: Dict[str, Fault] = {}

    def inject(self, target: str, fault_type: FaultType,
               severity: float = 0.5) -> Fault:
        """注入故障"""
        fault = Fault(
            fault_id=f"f_{target}_{fault_type.value}_{int(time.time()*1000)}",
            fault_type=fault_type,
            target=target,
            severity=severity,
            injected_at=time.time()
        )
        self.faults.append(fault)
        self.active_faults[fault.fault_id] = fault
        return fault

    def recover(self, fault_id: str) -> bool:
        """恢复故障"""
        if fault_id in self.active_faults:
            self.active_faults[fault_id].recovered_at = time.time()
            del self.active_faults[fault_id]
            return True
        return False

    def get_active_count(self) -> int:
        return len(self.active_faults)

    def get_fault_density(self) -> float:
        """获取故障密度"""
        if not self.faults:
            return 0.0
        recent = list(self.faults)[-50:]
        return len(recent) / 50.0

    def get_report(self) -> Dict:
        return {
            "total_faults": len(self.faults),
            "active": self.get_active_count(),
            "density": self.get_fault_density(),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 级联模拟器
# ═══════════════════════════════════════════════════════════════

class CascadeSimulator:
    """级联模拟器"""

    def __init__(self):
        self.cascades: deque = deque(maxlen=200)
        self.dependency_graph: Dict[str, Set[str]] = {}

    def set_dependencies(self, module: str, deps: List[str]):
        """设置依赖图"""
        self.dependency_graph[module] = set(deps)

    def simulate(self, source_fault: Fault,
                 module_states: Dict[str, float]) -> CascadeEvent:
        """模拟级联故障"""
        affected = [source_fault.target]
        to_process = [source_fault.target]
        depth = 0
        total_impact = source_fault.severity

        visited = {source_fault.target}

        while to_process and depth < 5:
            depth += 1
            next_wave = []
            for module in to_process:
                # 查找依赖此模块的其他模块
                for dependent, deps in self.dependency_graph.items():
                    if module in deps and dependent not in visited:
                        visited.add(dependent)
                        next_wave.append(dependent)
                        affected.append(dependent)
                        # 级联衰减
                        impact = source_fault.severity * (0.5 ** depth)
                        total_impact += impact
            to_process = next_wave

        cascade = CascadeEvent(
            event_id=f"c_{source_fault.fault_id}",
            source=source_fault.target,
            affected=affected,
            depth=depth,
            total_impact=min(1.0, total_impact)
        )
        self.cascades.append(cascade)
        return cascade

    def get_cascade_risk(self) -> float:
        """获取级联风险"""
        if not self.cascades:
            return 0.0
        recent = list(self.cascades)[-20:]
        avg_depth = sum(c.depth for c in recent) / len(recent)
        return min(1.0, avg_depth / 5.0)

    def get_report(self) -> Dict:
        return {
            "cascades": len(self.cascades),
            "risk": self.get_cascade_risk(),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 恢复测试器
# ═══════════════════════════════════════════════════════════════

class RecoveryTester:
    """恢复测试器 — punaḥsthāna"""

    def __init__(self):
        self.recoveries: deque = deque(maxlen=300)
        self.recovery_times: deque = deque(maxlen=100)

    def test_recovery(self, module: str, from_health: float,
                      to_health: float, mode: RecoveryMode) -> Dict:
        """测试恢复"""
        # 模拟恢复时间
        base_time = 5
        if mode == RecoveryMode.AUTOMATIC:
            base_time = 3
        elif mode == RecoveryMode.HARD:
            base_time = 10

        health_gap = from_health - to_health
        recovery_time = base_time + int(health_gap * 10)

        self.recoveries.append({
            "module": module,
            "from": from_health,
            "to": to_health,
            "mode": mode.value,
            "time": recovery_time,
            "timestamp": time.time()
        })
        self.recovery_times.append(recovery_time)

        return {
            "module": module,
            "recovery_time": recovery_time,
            "mode": mode.value,
            "successful": to_health > from_health * 0.8,
        }

    def get_avg_recovery_time(self) -> float:
        """获取平均恢复时间"""
        if not self.recovery_times:
            return 0.0
        return sum(self.recovery_times) / len(self.recovery_times)

    def get_report(self) -> Dict:
        return {
            "recoveries": len(self.recoveries),
            "avg_recovery_time": self.get_avg_recovery_time(),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 扰动引擎
# ═══════════════════════════════════════════════════════════════

class PerturbationEngine:
    """扰动引擎 — saṅkāra"""

    def __init__(self):
        self.perturbations: deque = deque(maxlen=300)

    def perturb(self, state: Dict[str, float],
                magnitude: float = 0.1) -> Dict[str, float]:
        """施加扰动"""
        perturbed = {}
        for key, value in state.items():
            # 确定性扰动
            noise = math.sin(hash(key + str(len(self.perturbations)))) * magnitude
            perturbed[key] = max(0.0, min(1.0, value + noise))

        self.perturbations.append({
            "magnitude": magnitude,
            "affected": list(state.keys()),
            "timestamp": time.time()
        })
        return perturbed

    def perturb_specific(self, state: Dict[str, float],
                         target: str, magnitude: float = 0.3) -> Dict[str, float]:
        """对特定目标施加扰动"""
        perturbed = dict(state)
        if target in perturbed:
            noise = (hash(target) % 100 - 50) / 100.0 * magnitude
            perturbed[target] = max(0.0, min(1.0, perturbed[target] + noise))

        self.perturbations.append({
            "target": target,
            "magnitude": magnitude,
            "timestamp": time.time()
        })
        return perturbed

    def get_perturbation_rate(self) -> float:
        """获取扰动率"""
        if not self.perturbations:
            return 0.0
        recent = list(self.perturbations)[-50:]
        return len(recent) / 50.0

    def get_report(self) -> Dict:
        return {
            "perturbations": len(self.perturbations),
            "rate": self.get_perturbation_rate(),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 稳定性评估器
# ═══════════════════════════════════════════════════════════════

class StabilityAssessor:
    """稳定性评估器"""

    def __init__(self):
        self.assessments: deque = deque(maxlen=300)
        self.lyapunov_estimates: deque = deque(maxlen=100)

    def assess(self, before: Dict[str, float],
               after: Dict[str, float]) -> float:
        """评估稳定性（Lyapunov-like）"""
        if not before or not after:
            return 1.0

        common_keys = set(before.keys()) & set(after.keys())
        if not common_keys:
            return 1.0

        # 计算发散
        divergences = []
        for key in common_keys:
            diff = abs(after[key] - before[key])
            divergences.append(diff)

        avg_divergence = sum(divergences) / len(divergences)
        # 稳定性 = 1 - 平均发散
        stability = max(0.0, 1.0 - avg_divergence * 2)

        self.assessments.append({
            "divergence": avg_divergence,
            "stability": stability,
            "timestamp": time.time()
        })
        return stability

    def estimate_lyapunov(self, trajectory: List[float]) -> float:
        """估计Lyapunov指数（简化）"""
        if len(trajectory) < 3:
            return 0.0

        # 计算相邻点分离率
        separations = []
        for i in range(len(trajectory) - 1):
            sep = abs(trajectory[i+1] - trajectory[i])
            separations.append(sep)

        if not separations or separations[0] == 0:
            return 0.0

        # 简化估计
        avg_sep = sum(separations) / len(separations)
        lyap = math.log(avg_sep + 1) / len(trajectory)
        self.lyapunov_estimates.append(lyap)
        return lyap

    def get_report(self) -> Dict:
        return {
            "assessments": len(self.assessments),
            "avg_stability": sum(a["stability"] for a in self.assessments) / max(1, len(self.assessments)),
        }


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — ChaosInjector v197
# ═══════════════════════════════════════════════════════════════

class ChaosInjector:
    """
    OMNI-HUB v197 混沌注入器

    saṅkāra · doṣa · punaḥsthāna — 乱动、过失、复位
    """

    VERSION = "197.0.0"

    def __init__(self):
        self.fault_injector = FaultInjector()
        self.cascade = CascadeSimulator()
        self.recovery = RecoveryTester()
        self.perturbation = PerturbationEngine()
        self.stability = StabilityAssessor()

        self.cycle_count = 0
        self.event_log: deque = deque(maxlen=10000)

    def inject_chaos(self, module_states: Dict[str, Dict]) -> Dict:
        """注入混沌"""
        states = {k: v.get("health", 0.5) for k, v in module_states.items()}

        # 1. 设置依赖图
        for module, state in module_states.items():
            deps = state.get("dependencies", [])
            self.cascade.set_dependencies(module, deps)

        # 2. 注入故障
        faults = []
        fault_types = list(FaultType)
        for i, module in enumerate(states):
            ft = fault_types[hash(module + str(self.cycle_count)) % len(fault_types)]
            severity = 0.3 + (hash(module) % 50) / 100.0
            fault = self.fault_injector.inject(module, ft, severity)
            faults.append(fault)

        # 3. 模拟级联
        cascades = []
        for fault in faults:
            if fault.severity > 0.5:
                cascade = self.cascade.simulate(fault, states)
                cascades.append(cascade)

        # 4. 施加扰动
        perturbed = self.perturbation.perturb(states, magnitude=0.15)

        # 5. 评估稳定性
        stability = self.stability.assess(states, perturbed)

        # 6. 测试恢复
        recoveries = []
        for module in states:
            before = states[module]
            after = perturbed[module]
            if after < before:
                rec = self.recovery.test_recovery(
                    module, before, after,
                    RecoveryMode.AUTOMATIC
                )
                recoveries.append(rec)

        # 7. 恢复所有故障
        for fault in faults:
            self.fault_injector.recover(fault.fault_id)

        return {
            "faults_injected": len(faults),
            "cascades": len(cascades),
            "stability": stability,
            "recoveries": len(recoveries),
            "perturbed_states": perturbed,
        }

    def run_cycle(self, module_states: Dict[str, Dict] = None) -> Dict:
        """运行混沌周期"""
        self.cycle_count += 1
        module_states = module_states or {}

        result = self.inject_chaos(module_states)

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
            "faults": self.fault_injector.get_report(),
            "cascade": self.cascade.get_report(),
            "recovery": self.recovery.get_report(),
            "perturbation": self.perturbation.get_report(),
            "stability": self.stability.get_report(),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_ci_instance: Optional[ChaosInjector] = None


def get_chaos_injector() -> ChaosInjector:
    global _ci_instance
    if _ci_instance is None:
        _ci_instance = ChaosInjector()
    return _ci_instance


if __name__ == "__main__":
    ci = ChaosInjector()
    print(f"ChaosInjector v{ci.VERSION} initialized")
    print(f"Status: {json.dumps(ci.get_status(), indent=2, default=str)}")
