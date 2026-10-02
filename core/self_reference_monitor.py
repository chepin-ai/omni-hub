"""
OMNI-HUB v186 — SelfReferenceMonitor
递归自指监控

核心功能：
1. MetaObservationLog     — 元观测日志（系统观察自身的观察）
2. RecursiveDepthGuard    — 递归深度守卫
3. SelfConsistencyChecker — 自一致性检查
4. ObserverEffectTracker  — 观察者效应追踪
5. ReflexiveLoopDetector  — 反射循环检测
6. SelfReferenceMonitor   — 统合引擎

映射：
- 自指 = svasaṃvedana（自证分）
- 递归 = saṃsāra（轮回）
- 观察者效应 = draṣṭṛ-bhāva（观者性）
- 反射 = pratibimba（镜像）
"""

from __future__ import annotations

import json
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Callable


# ═══════════════════════════════════════════════════════════════
# 枚举与常量
# ═══════════════════════════════════════════════════════════════

class ObservationLevel(Enum):
    """观测层级"""
    OBJECT = 0          # 对象层 — 观察外部
    META = 1            # 元层 — 观察对象层
    META_META = 2       # 元元层 — 观察元层
    TRANSCENDENT = 3    # 超越层 — 观察整个观测链条


class LoopStatus(Enum):
    """循环状态"""
    STABLE = 0          # 稳定
    OSCILLATING = 1     # 振荡
    DIVERGING = 2       # 发散
    CONVERGING = 3      # 收敛
    STRANGE = 4         # 奇异吸引子


class ReflexType(Enum):
    """反射类型"""
    DIRECT = 0          # 直接自指
    INDIRECT = 1        # 间接自指
    MUTUAL = 2          # 互指
    HIERARCHICAL = 3    # 层级反射


MAX_RECURSION_DEPTH = 5


# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class Observation:
    """观测记录"""
    obs_id: str
    observer: str
    target: str
    level: ObservationLevel
    timestamp: float
    result: Any = None
    duration_ms: float = 0.0


@dataclass
class MetaObservation:
    """元观测 — 对观测的观测"""
    meta_id: str
    observer: str
    target_observation: str
    level: ObservationLevel
    reflex_type: ReflexType
    timestamp: float
    recursion_depth: int = 0


@dataclass
class RecursionFrame:
    """递归栈帧"""
    frame_id: str
    caller: str
    callee: str
    depth: int
    timestamp: float
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SelfConsistencyReport:
    """自一致性报告"""
    report_id: str
    module_id: str
    consistency_score: float
    contradictions: List[Dict]
    stable_predicates: List[str]
    unstable_predicates: List[str]
    timestamp: float


@dataclass
class ObserverEffect:
    """观察者效应"""
    effect_id: str
    observer: str
    observed_before: Any
    observed_after: Any
    delta: float
    significance: float
    timestamp: float


# ═══════════════════════════════════════════════════════════════
# 子系统 1: 元观测日志
# ═══════════════════════════════════════════════════════════════

class MetaObservationLog:
    """
    元观测日志 — svasaṃvedana
    记录系统观察自身的观察
    """

    def __init__(self, max_depth: int = MAX_RECURSION_DEPTH):
        self.observations: deque = deque(maxlen=5000)
        self.meta_observations: deque = deque(maxlen=5000)
        self.max_depth = max_depth
        self.depth_counts: Dict[int, int] = {}

    def observe(self, observer: str, target: str, result: Any,
                level: ObservationLevel = ObservationLevel.OBJECT) -> Observation:
        """记录观测"""
        obs = Observation(
            obs_id=f"obs_{int(time.time()*1000)}_{len(self.observations)}",
            observer=observer,
            target=target,
            level=level,
            timestamp=time.time(),
            result=result
        )
        self.observations.append(obs)
        return obs

    def observe_observation(self, observer: str, target_obs: str,
                           reflex_type: ReflexType = ReflexType.DIRECT) -> MetaObservation:
        """记录元观测（对观测的观测）"""
        depth = self._compute_depth(observer, target_obs)
        if depth > self.max_depth:
            depth = self.max_depth

        meta = MetaObservation(
            meta_id=f"meta_{int(time.time()*1000)}_{len(self.meta_observations)}",
            observer=observer,
            target_observation=target_obs,
            level=self._depth_to_level(depth),
            reflex_type=reflex_type,
            timestamp=time.time(),
            recursion_depth=depth
        )
        self.meta_observations.append(meta)
        self.depth_counts[depth] = self.depth_counts.get(depth, 0) + 1
        return meta

    def _compute_depth(self, observer: str, target: str) -> int:
        """计算递归深度"""
        # 简化：如果observer和target相同或互为观测，深度+1
        depth = 0
        for meta in reversed(self.meta_observations):
            if meta.observer == observer or meta.target_observation == target:
                depth = max(depth, meta.recursion_depth + 1)
        return depth

    def _depth_to_level(self, depth: int) -> ObservationLevel:
        if depth == 0:
            return ObservationLevel.OBJECT
        elif depth == 1:
            return ObservationLevel.META
        elif depth == 2:
            return ObservationLevel.META_META
        else:
            return ObservationLevel.TRANSCENDENT

    def get_depth_distribution(self) -> Dict[int, int]:
        return dict(self.depth_counts)

    def get_report(self) -> Dict:
        return {
            "observations": len(self.observations),
            "meta_observations": len(self.meta_observations),
            "max_depth": self.max_depth,
            "depth_distribution": self.get_depth_distribution(),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 2: 递归深度守卫
# ═══════════════════════════════════════════════════════════════

class RecursiveDepthGuard:
    """
    递归深度守卫
    防止无限递归和栈溢出
    """

    def __init__(self, max_depth: int = MAX_RECURSION_DEPTH):
        self.max_depth = max_depth
        self.stack: List[RecursionFrame] = []
        self.violations: deque = deque(maxlen=500)
        self.depth_history: deque = deque(maxlen=1000)

    def enter(self, caller: str, callee: str, context: Dict = None) -> bool:
        """进入递归帧"""
        current_depth = len(self.stack)
        if current_depth >= self.max_depth:
            self.violations.append({
                "caller": caller,
                "callee": callee,
                "attempted_depth": current_depth + 1,
                "time": time.time(),
                "context": context or {}
            })
            return False

        frame = RecursionFrame(
            frame_id=f"frame_{int(time.time()*1000)}_{current_depth}",
            caller=caller,
            callee=callee,
            depth=current_depth + 1,
            timestamp=time.time(),
            context=context or {}
        )
        self.stack.append(frame)
        self.depth_history.append({"time": time.time(), "depth": current_depth + 1})
        return True

    def exit(self):
        """退出递归帧"""
        if self.stack:
            self.stack.pop()

    def current_depth(self) -> int:
        return len(self.stack)

    def is_safe(self) -> bool:
        return len(self.stack) < self.max_depth

    def get_report(self) -> Dict:
        return {
            "current_depth": self.current_depth(),
            "max_depth": self.max_depth,
            "total_violations": len(self.violations),
            "recent_violations": list(self.violations)[-5:],
            "avg_depth": sum(h["depth"] for h in self.depth_history) / max(1, len(self.depth_history)),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 3: 自一致性检查
# ═══════════════════════════════════════════════════════════════

class SelfConsistencyChecker:
    """
    自一致性检查
    检查系统陈述的自洽性
    """

    def __init__(self):
        self.reports: deque = deque(maxlen=500)
        self.predicate_history: Dict[str, deque] = {}

    def record_predicate(self, module_id: str, predicate: str, value: Any):
        """记录谓词值"""
        key = f"{module_id}:{predicate}"
        if key not in self.predicate_history:
            self.predicate_history[key] = deque(maxlen=100)
        self.predicate_history[key].append({
            "time": time.time(),
            "value": value,
        })

    def check_consistency(self, module_id: str) -> SelfConsistencyReport:
        """检查某模块的自一致性"""
        contradictions = []
        stable = []
        unstable = []

        # 检查该模块的所有谓词
        module_keys = [k for k in self.predicate_history if k.startswith(f"{module_id}:")]
        for key in module_keys:
            history = list(self.predicate_history[key])
            if len(history) < 2:
                continue

            values = [h["value"] for h in history]
            # 检查布尔一致性（先于数值，因为bool是int子类）
            if all(isinstance(v, bool) for v in values):
                if len(set(values)) == 1:
                    stable.append(key.split(":", 1)[1])
                else:
                    unstable.append(key.split(":", 1)[1])
                    contradictions.append({
                        "predicate": key.split(":", 1)[1],
                        "values": values[-5:],
                        "variance": 1.0,
                    })
            # 检查数值稳定性
            elif all(isinstance(v, (int, float)) for v in values):
                variance = sum((v - sum(values)/len(values))**2 for v in values) / len(values)
                if variance < 0.01:
                    stable.append(key.split(":", 1)[1])
                else:
                    unstable.append(key.split(":", 1)[1])
                    if variance > 0.5:
                        contradictions.append({
                            "predicate": key.split(":", 1)[1],
                            "values": values[-5:],
                            "variance": variance,
                        })

        total = len(stable) + len(unstable)
        score = len(stable) / max(1, total)

        report = SelfConsistencyReport(
            report_id=f"scr_{module_id}_{int(time.time())}",
            module_id=module_id,
            consistency_score=score,
            contradictions=contradictions,
            stable_predicates=stable,
            unstable_predicates=unstable,
            timestamp=time.time()
        )
        self.reports.append(report)
        return report

    def get_report(self) -> Dict:
        if not self.reports:
            return {"checks": 0}
        recent = list(self.reports)[-10:]
        return {
            "checks": len(self.reports),
            "avg_consistency": sum(r.consistency_score for r in recent) / len(recent),
            "total_contradictions": sum(len(r.contradictions) for r in recent),
            "modules_checked": len(set(r.module_id for r in self.reports)),
        }


# ═══════════════════════════════════════════════════════════════
# 子系统 4: 观察者效应追踪
# ═══════════════════════════════════════════════════════════════

class ObserverEffectTracker:
    """
    观察者效应追踪
    draṣṭṛ-bhāva — 观测行为对被观测对象的影响
    """

    def __init__(self):
        self.effects: deque = deque(maxlen=1000)
        self.state_snapshots: Dict[str, deque] = {}  # target -> snapshots

    def snapshot(self, target: str, state: Any):
        """记录状态快照"""
        if target not in self.state_snapshots:
            self.state_snapshots[target] = deque(maxlen=100)
        self.state_snapshots[target].append({
            "time": time.time(),
            "state": state,
        })

    def observe(self, observer: str, target: str, post_state: Any) -> Optional[ObserverEffect]:
        """追踪观测效应"""
        if target not in self.state_snapshots or not self.state_snapshots[target]:
            self.snapshot(target, post_state)
            return None

        before = self.state_snapshots[target][-1]["state"]
        self.snapshot(target, post_state)

        # 计算变化
        delta = compute_delta(before, post_state)
        if abs(delta) < 0.01:
            return None  # 无显著效应

        effect = ObserverEffect(
            effect_id=f"effect_{int(time.time()*1000)}",
            observer=observer,
            observed_before=before,
            observed_after=post_state,
            delta=delta,
            significance=min(1.0, abs(delta) * 2),
            timestamp=time.time()
        )
        self.effects.append(effect)
        return effect

    def get_report(self) -> Dict:
        base = {
            "total_effects": len(self.effects),
            "targets_observed": len(self.state_snapshots),
        }
        if not self.effects:
            return base
        base.update({
            "avg_significance": sum(e.significance for e in self.effects) / len(self.effects),
            "recent_effects": [
                {"observer": e.observer, "target": e.target if hasattr(e, 'target') else "",
                 "delta": e.delta, "significance": e.significance}
                for e in list(self.effects)[-5:]
            ],
        })
        return base


def compute_delta(before: Any, after: Any) -> float:
    """计算变化量"""
    if isinstance(before, (int, float)) and isinstance(after, (int, float)):
        return after - before
    if isinstance(before, dict) and isinstance(after, dict):
        # 比较字典的相似度
        keys = set(before.keys()) | set(after.keys())
        if not keys:
            return 0.0
        diffs = sum(1 for k in keys if before.get(k) != after.get(k))
        return diffs / len(keys)
    return 0.0 if before == after else 1.0


# ═══════════════════════════════════════════════════════════════
# 子系统 5: 反射循环检测
# ═══════════════════════════════════════════════════════════════

class ReflexiveLoopDetector:
    """
    反射循环检测
    检测A观察B，B观察A的循环结构
    """

    def __init__(self):
        self.observation_graph: Dict[str, List[str]] = {}  # observer -> [targets]
        self.loops: deque = deque(maxlen=500)
        self.loop_history: deque = deque(maxlen=1000)

    def add_edge(self, observer: str, target: str):
        """添加观测边"""
        if observer not in self.observation_graph:
            self.observation_graph[observer] = []
        if target not in self.observation_graph[observer]:
            self.observation_graph[observer].append(target)

        # 检测循环
        self._detect_loops(observer, target)

    def _detect_loops(self, start: str, target: str):
        """检测从start到target的循环"""
        # 简单检测：如果target观察start，则形成互指
        if target in self.observation_graph and start in self.observation_graph[target]:
            loop = {
                "type": "mutual",
                "nodes": [start, target],
                "time": time.time(),
            }
            self.loops.append(loop)
            self.loop_history.append(loop)

        # 检测三元循环
        for mid in self.observation_graph.get(target, []):
            if mid in self.observation_graph and start in self.observation_graph[mid]:
                loop = {
                    "type": "triadic",
                    "nodes": [start, target, mid],
                    "time": time.time(),
                }
                self.loops.append(loop)
                self.loop_history.append(loop)

    def analyze_loop_dynamics(self) -> LoopStatus:
        """分析循环动态"""
        if len(self.loop_history) < 10:
            return LoopStatus.STABLE

        recent = list(self.loop_history)[-20:]
        times = [l["time"] for l in recent]
        if len(times) < 2:
            return LoopStatus.STABLE

        intervals = [times[i+1] - times[i] for i in range(len(times)-1)]
        avg_interval = sum(intervals) / len(intervals)

        if avg_interval < 1.0:
            return LoopStatus.STRANGE  # 高频循环
        elif avg_interval < 5.0:
            return LoopStatus.OSCILLATING
        elif avg_interval > 30.0:
            return LoopStatus.CONVERGING
        else:
            return LoopStatus.STABLE

    def get_report(self) -> Dict:
        return {
            "total_loops": len(self.loops),
            "loop_history": len(self.loop_history),
            "current_dynamics": self.analyze_loop_dynamics().name,
            "observation_graph_size": len(self.observation_graph),
            "recent_loops": list(self.loops)[-5:],
        }


# ═══════════════════════════════════════════════════════════════
# 统合引擎 — SelfReferenceMonitor v186
# ═══════════════════════════════════════════════════════════════

class SelfReferenceMonitor:
    """
    OMNI-HUB v186 递归自指监控

    svasaṃvedana — 自证分
    """

    VERSION = "186.0.0"

    def __init__(self):
        self.meta_log = MetaObservationLog()
        self.depth_guard = RecursiveDepthGuard()
        self.consistency = SelfConsistencyChecker()
        self.effect_tracker = ObserverEffectTracker()
        self.loop_detector = ReflexiveLoopDetector()

        self.cycle_count = 0
        self.event_log: deque = deque(maxlen=10000)

    def run_cycle(self, module_states: Dict[str, Dict] = None,
                 omni_result: Dict = None) -> Dict:
        """运行完整自指监控周期"""
        self.cycle_count += 1
        module_states = module_states or {}

        # 1. 记录元观测
        for module_id, state in module_states.items():
            self.meta_log.observe(
                observer="self_reference_monitor",
                target=module_id,
                result=state,
                level=ObservationLevel.OBJECT
            )
            # 元观测：监控器观察自己对模块的观察
            self.meta_log.observe_observation(
                observer="self_reference_monitor",
                target_obs=module_id,
                reflex_type=ReflexType.DIRECT
            )

        # 2. 递归深度检查
        depth_safe = self.depth_guard.is_safe()
        if not depth_safe:
            self.event_log.append({
                "type": "recursion_warning",
                "current_depth": self.depth_guard.current_depth(),
                "time": time.time()
            })

        # 3. 自一致性检查
        consistency_results = {}
        for module_id in module_states:
            # 记录谓词
            state = module_states[module_id]
            if isinstance(state, dict):
                for k, v in state.items():
                    self.consistency.record_predicate(module_id, k, v)
            report = self.consistency.check_consistency(module_id)
            consistency_results[module_id] = {
                "score": report.consistency_score,
                "contradictions": len(report.contradictions),
            }

        # 4. 观察者效应追踪
        effects = []
        for module_id, state in module_states.items():
            if isinstance(state, dict):
                effect = self.effect_tracker.observe(
                    observer="self_reference_monitor",
                    target=module_id,
                    post_state=state
                )
                if effect:
                    effects.append({"target": module_id, "delta": effect.delta,
                                   "significance": effect.significance})

        # 5. 反射循环检测
        for module_id in module_states:
            self.loop_detector.add_edge("self_reference_monitor", module_id)
            # 如果模块也观察监控器，则形成循环
            if isinstance(module_states.get(module_id), dict):
                watches = module_states[module_id].get("watches", [])
                if "self_reference_monitor" in watches:
                    self.loop_detector.add_edge(module_id, "self_reference_monitor")

        loop_dynamics = self.loop_detector.analyze_loop_dynamics()

        # 6. 结果
        result = {
            "cycle": self.cycle_count,
            "recursion_safe": depth_safe,
            "current_depth": self.depth_guard.current_depth(),
            "meta_observations": len(self.meta_log.meta_observations),
            "consistency": consistency_results,
            "observer_effects": len(effects),
            "loop_dynamics": loop_dynamics.name,
            "depth_distribution": self.meta_log.get_depth_distribution(),
        }

        self.event_log.append(result)
        return result

    def get_status(self) -> Dict:
        return {
            "version": self.VERSION,
            "cycle_count": self.cycle_count,
            "meta_log": self.meta_log.get_report(),
            "depth_guard": self.depth_guard.get_report(),
            "consistency": self.consistency.get_report(),
            "effect_tracker": self.effect_tracker.get_report(),
            "loop_detector": self.loop_detector.get_report(),
            "event_log_size": len(self.event_log),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════════════════════════

_srm_instance: Optional[SelfReferenceMonitor] = None


def get_self_reference_monitor() -> SelfReferenceMonitor:
    global _srm_instance
    if _srm_instance is None:
        _srm_instance = SelfReferenceMonitor()
    return _srm_instance


if __name__ == "__main__":
    srm = SelfReferenceMonitor()
    print(f"SelfReferenceMonitor v{srm.VERSION} initialized")
    print(f"Status: {json.dumps(srm.get_status(), indent=2, default=str)}")
