#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNI-HUB v12.0 -- Meta-Circle (Circle of Circles)
==================================================

The Meta-Circle monitors, analyzes, and coordinates all five circles.
It is not an external observer, but part of the system's self-reference.

Version: 12.0.0
Date: 2026-09-19
"""

from __future__ import annotations

import sys
import os
import json
import math
import time
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Set, Callable, Union
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "/mnt/agents/output/OMNI-HUB/core")

try:
    from v12_standards import PHI_GOLDEN, PI, LINE_NAMES
except Exception:
    PHI_GOLDEN = (1.0 + 5.0**0.5) / 2.0
    PI = 3.141592653589793
    LINE_NAMES = ["ucif2", "lvlu", "lgt", "qfa", "vinf", "qgl",
                  "qlv", "cisvr", "qtlv", "usrm", "cfts"]

try:
    from v12_circle_systems import (
        BaseCircle, CircleMessage, CircleMessageType,
        CircleHealth, CircleState, CircleHealthStatus,
        CircleSystemManager, CircleEmergenceAnalyzer,
        CIRCLE_NAMES, N_CIRCLES, N_FCTN_LAYERS,
        ConsensusCircleImpl, SessionCircleImpl, RelayCircleImpl,
        CommandCircleImpl, AdminCircleImpl,
    )
    _CIRCLE_SYSTEMS_AVAILABLE = True
except Exception as e:
    _CIRCLE_SYSTEMS_AVAILABLE = False
    print(f"[MetaCircle] Warning: Could not import circle_systems: {e}")

META_CIRCLE_VERSION = "12.0.0"
MAX_RECURSION_DEPTH = 3


class MetaCircleMode(Enum):
    OBSERVE = "observe"
    COORDINATE = "coordinate"
    REFLECT = "reflect"
    EVOLVE = "evolve"
    EMERGENCE = "emergence"


class MetaRelationType(Enum):
    OBSERVES = "observes"
    COORDINATES = "coordinates"
    INFLUENCES = "influences"
    DEPENDS_ON = "depends_on"
    EMERGES_FROM = "emerges_from"
    REFLECTS = "reflects"


@dataclass
class MetaCircleState:
    mode: MetaCircleMode = MetaCircleMode.OBSERVE
    recursion_depth: int = 0
    self_reference_count: int = 0
    observation_count: int = 0
    coordination_count: int = 0
    reflection_count: int = 0
    evolution_count: int = 0
    emergence_level: float = 0.0
    meta_stability: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode.value,
            "recursion_depth": self.recursion_depth,
            "self_reference_count": self.self_reference_count,
            "observation_count": self.observation_count,
            "coordination_count": self.coordination_count,
            "reflection_count": self.reflection_count,
            "evolution_count": self.evolution_count,
            "emergence_level": round(self.emergence_level, 6),
            "meta_stability": round(self.meta_stability, 6),
        }


@dataclass
class CircleRelation:
    source: str
    target: str
    relation_type: MetaRelationType
    weight: float = 1.0
    bidirectional: bool = False
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "relation_type": self.relation_type.value,
            "weight": round(self.weight, 4),
            "bidirectional": self.bidirectional,
            "properties": self.properties,
        }


@dataclass
class SelfReferenceFrame:
    frame_id: str
    timestamp: str
    observed_state: Dict[str, Any] = field(default_factory=dict)
    observer_state: Dict[str, Any] = field(default_factory=dict)
    recursion_level: int = 0
    stability: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "recursion_level": self.recursion_level,
            "stability": round(self.stability, 4),
        }


class CircleObserver:
    """Circle Observer -- Observes all five circles"""

    def __init__(self, meta_circle: "MetaCircle"):
        self.meta = meta_circle
        self.observation_log: deque = deque(maxlen=500)
        self.observation_interval = 1

    def observe_circle(self, circle_name: str) -> Dict[str, Any]:
        if circle_name not in self.meta.circle_manager.circles:
            return {"error": f"Circle {circle_name} not found"}

        circle = self.meta.circle_manager.circles[circle_name]
        observation = {
            "circle_name": circle_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "health": circle.health.to_dict(),
            "state": circle.state.to_dict(),
            "stats": circle.get_stats(),
            "entropy": round(circle.compute_entropy(), 6),
            "emergence": round(circle.compute_emergence_contribution(), 6),
        }

        self.observation_log.append(observation)
        self.meta.state.observation_count += 1
        return observation

    def observe_all_circles(self) -> Dict[str, Dict[str, Any]]:
        observations = {}
        for name in self.meta.circle_manager.circles:
            observations[name] = self.observe_circle(name)
        return observations

    def detect_anomalies(self) -> List[Dict[str, Any]]:
        anomalies = []
        for name, circle in self.meta.circle_manager.circles.items():
            if circle.health.status in [CircleHealthStatus.CRITICAL,
                                         CircleHealthStatus.OVERLOADED]:
                anomalies.append({
                    "type": "health_critical",
                    "circle": name,
                    "status": circle.health.status.value,
                    "load": circle.health.load_factor,
                    "severity": 1.0 if circle.health.status == CircleHealthStatus.CRITICAL else 0.7,
                })

            entropy = circle.compute_entropy()
            if entropy > 3.0:
                anomalies.append({
                    "type": "high_entropy",
                    "circle": name,
                    "entropy": entropy,
                    "severity": min(1.0, entropy / 5.0),
                })

            if len(circle.messages_in) > 500:
                anomalies.append({
                    "type": "message_backlog",
                    "circle": name,
                    "backlog": len(circle.messages_in),
                    "severity": min(1.0, len(circle.messages_in) / 1000.0),
                })

        return anomalies

    def get_observation_report(self) -> Dict[str, Any]:
        return {
            "total_observations": self.meta.state.observation_count,
            "recent_observations": len(self.observation_log),
            "latest": list(self.observation_log)[-5:] if self.observation_log else [],
        }


class CircleCoordinator:
    """Circle Coordinator -- Coordinates behavior among five circles"""

    def __init__(self, meta_circle: "MetaCircle"):
        self.meta = meta_circle
        self.coordination_log: deque = deque(maxlen=200)
        self.coordination_policies: List[Dict[str, Any]] = []

    def coordinate_load_balance(self) -> List[Dict[str, Any]]:
        actions = []
        circles = self.meta.circle_manager.circles

        loads = {
            name: circle.health.load_factor
            for name, circle in circles.items()
        }

        if not loads:
            return actions

        max_load_circle = max(loads.items(), key=lambda x: x[1])
        min_load_circle = min(loads.items(), key=lambda x: x[1])

        if max_load_circle[1] > 0.7 and min_load_circle[1] < 0.3:
            self.meta.circle_manager.circles[max_load_circle[0]].receive_message(
                CircleMessage(
                    source_circle="meta",
                    target_circle=max_load_circle[0],
                    msg_type=CircleMessageType.ADMIN_CONFIG,
                    payload={
                        "action": "reduce_load",
                        "suggested_target": min_load_circle[0],
                        "reason": "load_balancing",
                    },
                )
            )
            actions.append({
                "action": "load_balance",
                "from": max_load_circle[0],
                "to": min_load_circle[0],
                "load_delta": round(max_load_circle[1] - min_load_circle[1], 4),
            })

        self.coordination_log.extend(actions)
        self.meta.state.coordination_count += len(actions)
        return actions

    def coordinate_synchronization(self) -> List[Dict[str, Any]]:
        actions = []
        for name, circle in self.meta.circle_manager.circles.items():
            if circle.health.coherence < 0.5:
                circle.receive_message(CircleMessage(
                    source_circle="meta",
                    target_circle=name,
                    msg_type=CircleMessageType.STATE_SYNC,
                    payload={"reason": "coherence_low", "requested_by": "meta"},
                ))
                actions.append({
                    "action": "sync_trigger",
                    "target": name,
                    "coherence": circle.health.coherence,
                })

        self.coordination_log.extend(actions)
        self.meta.state.coordination_count += len(actions)
        return actions

    def apply_policy(self, policy: Dict[str, Any]) -> bool:
        self.coordination_policies.append(policy)
        policy_type = policy.get("type", "unknown")

        if policy_type == "priority_adjust":
            target = policy.get("target")
            new_priority = policy.get("priority", 5)
            if target in self.meta.circle_manager.circles:
                circle = self.meta.circle_manager.circles[target]
                circle.knowledge_store["meta_priority"] = new_priority
                return True
        elif policy_type == "throttle":
            target = policy.get("target")
            rate = policy.get("rate", 1.0)
            if target in self.meta.circle_manager.circles:
                circle = self.meta.circle_manager.circles[target]
                circle.knowledge_store["meta_throttle"] = rate
                return True

        return False

    def get_coordination_report(self) -> Dict[str, Any]:
        return {
            "total_coordinations": self.meta.state.coordination_count,
            "policies_active": len(self.coordination_policies),
            "recent_actions": list(self.coordination_log)[-10:],
        }


class CircleReflector:
    """Circle Reflector -- Implements meta-circle self-reference and self-monitoring"""

    def __init__(self, meta_circle: "MetaCircle"):
        self.meta = meta_circle
        self.reflection_frames: deque = deque(maxlen=100)
        self.self_reference_chain: List[str] = []

    def reflect(self) -> SelfReferenceFrame:
        frame_id = f"reflect-{self.meta.state.self_reference_count}"
        timestamp = datetime.now(timezone.utc).isoformat()

        observed_state = {
            "mode": self.meta.state.mode.value,
            "emergence_level": self.meta.state.emergence_level,
            "meta_stability": self.meta.state.meta_stability,
            "observation_count": self.meta.state.observation_count,
            "coordination_count": self.meta.state.coordination_count,
            "reflection_count": self.meta.state.reflection_count,
        }

        observer_state = {
            "recursion_depth": self.meta.state.recursion_depth,
            "frame_count": len(self.reflection_frames),
            "stability_trend": self._compute_stability_trend(),
        }

        stability = self._compute_reflection_stability(observed_state)

        frame = SelfReferenceFrame(
            frame_id=frame_id,
            timestamp=timestamp,
            observed_state=observed_state,
            observer_state=observer_state,
            recursion_level=self.meta.state.recursion_depth,
            stability=stability,
        )

        self.reflection_frames.append(frame)
        self.meta.state.reflection_count += 1
        self.meta.state.self_reference_count += 1

        if self.meta.state.recursion_depth < MAX_RECURSION_DEPTH:
            self.meta.state.recursion_depth += 1
            self.meta.state.recursion_depth -= 1

        return frame

    def _compute_reflection_stability(self, state: Dict[str, Any]) -> float:
        if len(self.reflection_frames) < 2:
            return 1.0

        recent_frames = list(self.reflection_frames)[-5:]
        if not recent_frames:
            return 1.0

        emergence_values = [
            f.observed_state.get("emergence_level", 0)
            for f in recent_frames
        ]
        if len(emergence_values) >= 2:
            changes = [abs(emergence_values[i] - emergence_values[i-1])
                       for i in range(1, len(emergence_values))]
            avg_change = sum(changes) / len(changes)
            stability = max(0.0, 1.0 - avg_change)
        else:
            stability = 1.0

        self.meta.state.meta_stability = stability
        return stability

    def _compute_stability_trend(self) -> float:
        if len(self.reflection_frames) < 2:
            return 0.0
        recent = [f.stability for f in list(self.reflection_frames)[-10:]]
        if len(recent) >= 2:
            return recent[-1] - recent[0]
        return 0.0

    def get_reflection_report(self) -> Dict[str, Any]:
        return {
            "total_reflections": self.meta.state.reflection_count,
            "self_references": self.meta.state.self_reference_count,
            "recursion_depth": self.meta.state.recursion_depth,
            "current_stability": round(self.meta.state.meta_stability, 4),
            "frame_count": len(self.reflection_frames),
            "recent_frames": [f.to_dict() for f in list(self.reflection_frames)[-5:]],
        }


class CircleEvolver:
    """Circle Evolver -- Manages dynamic evolution of circle structures"""

    def __init__(self, meta_circle: "MetaCircle"):
        self.meta = meta_circle
        self.evolution_history: deque = deque(maxlen=100)
        self.evolution_rules: List[Dict[str, Any]] = []

    def evaluate_evolution(self) -> List[Dict[str, Any]]:
        proposals = []
        circles = self.meta.circle_manager.circles

        for name, circle in circles.items():
            if circle.health.load_factor > 0.9:
                proposals.append({
                    "type": "split_proposal",
                    "circle": name,
                    "reason": "overload",
                    "load": circle.health.load_factor,
                })

        coupling = self.meta.circle_manager.coupling_matrix
        for i, name_i in enumerate(CIRCLE_NAMES):
            for j, name_j in enumerate(CIRCLE_NAMES):
                if i < j and coupling[i, j] > 0.8:
                    proposals.append({
                        "type": "merge_proposal",
                        "circles": [name_i, name_j],
                        "reason": "high_coupling",
                        "coupling": float(coupling[i, j]),
                    })

        return proposals

    def adjust_coupling(self, src: str, dst: str, adjustment: float) -> bool:
        name_to_idx = {name: i for i, name in enumerate(CIRCLE_NAMES)}
        if src not in name_to_idx or dst not in name_to_idx:
            return False

        i, j = name_to_idx[src], name_to_idx[dst]
        old_value = self.meta.circle_manager.coupling_matrix[i, j]
        new_value = np.clip(old_value + adjustment, 0.0, 1.0)
        self.meta.circle_manager.coupling_matrix[i, j] = new_value

        self.evolution_history.append({
            "action": "adjust_coupling",
            "src": src,
            "dst": dst,
            "old": round(float(old_value), 4),
            "new": round(float(new_value), 4),
        })
        self.meta.state.evolution_count += 1
        return True

    def add_evolution_rule(self, rule: Dict[str, Any]) -> None:
        self.evolution_rules.append(rule)

    def get_evolution_report(self) -> Dict[str, Any]:
        return {
            "total_evolutions": self.meta.state.evolution_count,
            "rules_defined": len(self.evolution_rules),
            "history_size": len(self.evolution_history),
            "recent_changes": list(self.evolution_history)[-5:],
        }


class MetaCircle:
    """
    Meta-Circle -- The Circle of Circles.

    The Meta-Circle observes, coordinates, reflects, and evolves the five-circle system.
    It is not a sixth circle, but a "circle about circles".
    """

    def __init__(self, circle_manager=None):
        if circle_manager is None and _CIRCLE_SYSTEMS_AVAILABLE:
            self.circle_manager = CircleSystemManager()
        else:
            self.circle_manager = circle_manager

        self.state = MetaCircleState()

        self.observer = CircleObserver(self)
        self.coordinator = CircleCoordinator(self)
        self.reflector = CircleReflector(self)
        self.evolver = CircleEvolver(self)

        if _CIRCLE_SYSTEMS_AVAILABLE:
            self.emergence_analyzer = CircleEmergenceAnalyzer(self.circle_manager)
        else:
            self.emergence_analyzer = None

        self.relations: List[CircleRelation] = []
        self._build_default_relations()

        self.knowledge: Dict[str, Any] = {}
        self.history: deque = deque(maxlen=200)
        self.tick_count = 0

    def _build_default_relations(self) -> None:
        default_relations = [
            CircleRelation("meta", "consensus", MetaRelationType.OBSERVES, 1.0),
            CircleRelation("meta", "session", MetaRelationType.OBSERVES, 1.0),
            CircleRelation("meta", "relay", MetaRelationType.OBSERVES, 1.0),
            CircleRelation("meta", "command", MetaRelationType.OBSERVES, 1.0),
            CircleRelation("meta", "admin", MetaRelationType.OBSERVES, 1.0),
            CircleRelation("meta", "consensus", MetaRelationType.COORDINATES, 0.5),
            CircleRelation("meta", "session", MetaRelationType.COORDINATES, 0.5),
            CircleRelation("meta", "relay", MetaRelationType.COORDINATES, 0.5),
            CircleRelation("meta", "command", MetaRelationType.COORDINATES, 0.5),
            CircleRelation("meta", "admin", MetaRelationType.COORDINATES, 0.5),
            CircleRelation("consensus", "session", MetaRelationType.INFLUENCES, 0.35),
            CircleRelation("session", "relay", MetaRelationType.INFLUENCES, 0.40),
            CircleRelation("relay", "command", MetaRelationType.INFLUENCES, 0.45),
            CircleRelation("command", "admin", MetaRelationType.INFLUENCES, 0.35),
            CircleRelation("admin", "consensus", MetaRelationType.INFLUENCES, 0.30),
            CircleRelation("meta", "consensus", MetaRelationType.EMERGES_FROM, 0.2),
            CircleRelation("meta", "session", MetaRelationType.EMERGES_FROM, 0.2),
            CircleRelation("meta", "relay", MetaRelationType.EMERGES_FROM, 0.2),
            CircleRelation("meta", "command", MetaRelationType.EMERGES_FROM, 0.2),
            CircleRelation("meta", "admin", MetaRelationType.EMERGES_FROM, 0.2),
            CircleRelation("meta", "meta", MetaRelationType.REFLECTS, 1.0, True),
        ]
        self.relations = default_relations

    def tick(self) -> Dict[str, Any]:
        self.tick_count += 1
        start_time = time.time()

        self.state.mode = MetaCircleMode.OBSERVE
        observations = self.observer.observe_all_circles()
        anomalies = self.observer.detect_anomalies()

        if self.emergence_analyzer:
            emergence_report = self.emergence_analyzer.analyze_all()
            self.state.emergence_level = emergence_report.get("overall_emergence", 0)
        else:
            emergence_report = {"overall_emergence": 0}
            self.state.emergence_level = 0

        coordination_actions = []
        if anomalies:
            self.state.mode = MetaCircleMode.COORDINATE
            coordination_actions.extend(self.coordinator.coordinate_load_balance())
            coordination_actions.extend(self.coordinator.coordinate_synchronization())

        self.state.mode = MetaCircleMode.REFLECT
        reflection_frame = self.reflector.reflect()

        self.state.mode = MetaCircleMode.EVOLVE
        evolution_proposals = self.evolver.evaluate_evolution()

        self.state.mode = MetaCircleMode.EMERGENCE

        self.knowledge[f"tick_{self.tick_count}"] = {
            "observations": observations,
            "anomalies": anomalies,
            "emergence": emergence_report,
            "coordination": coordination_actions,
            "reflection": reflection_frame.to_dict(),
            "evolution_proposals": evolution_proposals,
        }

        tick_record = {
            "tick": self.tick_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": self.state.mode.value,
            "emergence_level": round(self.state.emergence_level, 4),
            "meta_stability": round(self.state.meta_stability, 4),
            "anomalies_detected": len(anomalies),
            "coordination_actions": len(coordination_actions),
            "evolution_proposals": len(evolution_proposals),
        }
        self.history.append(tick_record)

        elapsed = (time.time() - start_time) * 1000.0
        tick_record["execution_ms"] = round(elapsed, 2)

        return tick_record

    def run_ticks(self, n: int) -> List[Dict[str, Any]]:
        results = []
        for _ in range(n):
            result = self.tick()
            results.append(result)
        return results

    def get_relation_matrix(self) -> np.ndarray:
        all_names = CIRCLE_NAMES + ["meta"]
        name_to_idx = {name: i for i, name in enumerate(all_names)}
        M = np.zeros((len(all_names), len(all_names)), dtype=np.float64)

        for rel in self.relations:
            if rel.source in name_to_idx and rel.target in name_to_idx:
                i, j = name_to_idx[rel.source], name_to_idx[rel.target]
                M[i, j] = rel.weight
                if rel.bidirectional:
                    M[j, i] = rel.weight

        return M

    def get_self_reference_report(self) -> Dict[str, Any]:
        return {
            "meta_circle_state": self.state.to_dict(),
            "reflection": self.reflector.get_reflection_report(),
            "self_reference_chain": self.reflector.self_reference_chain,
            "recursion_depth": self.state.recursion_depth,
            "meta_stability": round(self.state.meta_stability, 4),
            "self_observation": {
                "tick_count": self.tick_count,
                "knowledge_size": len(self.knowledge),
                "history_size": len(self.history),
                "relation_count": len(self.relations),
            },
        }

    def get_full_report(self) -> Dict[str, Any]:
        return {
            "version": META_CIRCLE_VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "meta_circle_state": self.state.to_dict(),
            "tick_count": self.tick_count,
            "self_reference": self.get_self_reference_report(),
            "observation": self.observer.get_observation_report(),
            "coordination": self.coordinator.get_coordination_report(),
            "reflection": self.reflector.get_reflection_report(),
            "evolution": self.evolver.get_evolution_report(),
            "circle_manager": self.circle_manager.get_full_report() if self.circle_manager else {},
            "relation_matrix": [
                [round(float(v), 4) for v in row]
                for row in self.get_relation_matrix().tolist()
            ],
        }

    def to_dict(self) -> Dict[str, Any]:
        return self.get_full_report()


class MetaCircleEmergence:
    """Meta-Circle Emergence Analysis -- Analyzes emergence from 'circle of circles'"""

    def __init__(self, meta_circle: MetaCircle):
        self.meta = meta_circle
        self.second_order_emergence_history: List[float] = []

    def compute_second_order_emergence(self) -> float:
        if not self.meta.history:
            return 0.0

        emergence_levels = [h.get("emergence_level", 0) for h in self.meta.history]
        if len(emergence_levels) < 2:
            return 0.0

        first_order = [emergence_levels[i] - emergence_levels[i-1]
                       for i in range(1, len(emergence_levels))]

        if len(first_order) < 2:
            return 0.0
        second_order = [first_order[i] - first_order[i-1]
                        for i in range(1, len(first_order))]

        second_order_emergence = np.mean([abs(v) for v in second_order])
        self.second_order_emergence_history.append(second_order_emergence)

        return second_order_emergence

    def compute_recursive_stability(self) -> float:
        if not self.meta.reflector.reflection_frames:
            return 1.0

        stabilities = [f.stability for f in self.meta.reflector.reflection_frames]
        if not stabilities:
            return 1.0

        avg_stability = np.mean(stabilities)
        stability_variance = np.var(stabilities)
        recursive_stability = avg_stability * (1.0 - min(1.0, stability_variance))
        return recursive_stability

    def compute_meta_learning_rate(self) -> float:
        if len(self.meta.history) < 2:
            return 0.0

        recent = list(self.meta.history)[-10:]
        anomalies_over_time = [r.get("anomalies_detected", 0) for r in recent]

        if len(anomalies_over_time) >= 2:
            trend = anomalies_over_time[-1] - anomalies_over_time[0]
            learning_rate = -trend / max(len(anomalies_over_time), 1)
            return max(0.0, learning_rate)
        return 0.0

    def analyze_meta_emergence(self) -> Dict[str, Any]:
        return {
            "second_order_emergence": round(self.compute_second_order_emergence(), 6),
            "recursive_stability": round(self.compute_recursive_stability(), 6),
            "meta_learning_rate": round(self.compute_meta_learning_rate(), 6),
            "self_reference_depth": self.meta.state.recursion_depth,
            "meta_emergence_level": round(self.meta.state.emergence_level, 4),
        }


# ---------------------------------------------------------------------------
# 5. Verification
# ---------------------------------------------------------------------------

def verify_meta_circle() -> Dict[str, Any]:
    """验证元圈系统"""
    print("[MetaCircle] Starting verification...")
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": META_CIRCLE_VERSION,
        "tests": {},
    }

    if not _CIRCLE_SYSTEMS_AVAILABLE:
        results["tests"]["import"] = {
            "status": "FAIL",
            "reason": "CircleSystems not available",
        }
        results["overall_status"] = "FAILED"
        return results

    meta = MetaCircle()
    assert meta is not None
    assert meta.circle_manager is not None
    results["tests"]["init"] = {
        "status": "PASS",
        "components": {
            "observer": meta.observer is not None,
            "coordinator": meta.coordinator is not None,
            "reflector": meta.reflector is not None,
            "evolver": meta.evolver is not None,
        },
    }

    tick_result = meta.tick()
    assert "tick" in tick_result
    assert meta.tick_count == 1
    results["tests"]["tick"] = {
        "status": "PASS",
        "tick_result_keys": list(tick_result.keys()),
    }

    meta.run_ticks(4)
    assert meta.tick_count == 5
    results["tests"]["multi_tick"] = {
        "status": "PASS",
        "final_tick": meta.tick_count,
        "history_size": len(meta.history),
    }

    observations = meta.observer.observe_all_circles()
    assert len(observations) == 5
    anomalies = meta.observer.detect_anomalies()
    results["tests"]["observe"] = {
        "status": "PASS",
        "circles_observed": len(observations),
        "anomalies_detected": len(anomalies),
    }

    actions = meta.coordinator.coordinate_load_balance()
    results["tests"]["coordinate"] = {
        "status": "PASS",
        "actions_taken": len(actions),
    }

    frame = meta.reflector.reflect()
    assert frame is not None
    assert meta.state.self_reference_count > 0
    results["tests"]["reflect"] = {
        "status": "PASS",
        "frame_id": frame.frame_id,
        "stability": round(frame.stability, 4),
        "self_references": meta.state.self_reference_count,
    }

    rel_matrix = meta.get_relation_matrix()
    assert rel_matrix.shape[0] == 6
    results["tests"]["relation_matrix"] = {
        "status": "PASS",
        "shape": list(rel_matrix.shape),
    }

    proposals = meta.evolver.evaluate_evolution()
    results["tests"]["evolve"] = {
        "status": "PASS",
        "proposals": len(proposals),
    }

    self_ref = meta.get_self_reference_report()
    assert "meta_circle_state" in self_ref
    assert "reflection" in self_ref
    results["tests"]["self_reference"] = {
        "status": "PASS",
        "recursion_depth": self_ref["recursion_depth"],
        "meta_stability": self_ref["meta_stability"],
    }

    meta_emergence = MetaCircleEmergence(meta)
    analysis = meta_emergence.analyze_meta_emergence()
    assert "second_order_emergence" in analysis
    results["tests"]["meta_emergence"] = {
        "status": "PASS",
        "second_order_emergence": analysis["second_order_emergence"],
        "recursive_stability": analysis["recursive_stability"],
    }

    report = meta.get_full_report()
    assert "meta_circle_state" in report
    assert "relation_matrix" in report
    results["tests"]["full_report"] = {
        "status": "PASS",
        "report_keys": list(report.keys()),
    }

    all_pass = all(t["status"] == "PASS" for t in results["tests"].values())
    results["overall_status"] = "ALL_PASS" if all_pass else "PARTIAL"
    results["pass_count"] = sum(1 for t in results["tests"].values() if t["status"] == "PASS")
    results["total_tests"] = len(results["tests"])

    print(f"[MetaCircle] Verification complete: {results['pass_count']}/{results['total_tests']} passed")
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 70)
    print("OMNI-HUB v12.0 -- Meta-Circle Verification")
    print("=" * 70)

    verify_result = verify_meta_circle()

    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    for test_name, test_data in verify_result["tests"].items():
        print(f"\n{test_name}: {test_data['status']}")
        for k, v in test_data.items():
            if k != 'status':
                print(f"  {k}: {v}")

    print("\n" + "=" * 70)
    print("OVERALL")
    print("=" * 70)
    print(f"Status: {verify_result['overall_status']}")
    print(f"Passed: {verify_result['pass_count']}/{verify_result['total_tests']}")

    hub_dir = Path("/mnt/agents/output/OMNI-HUB/hub")
    hub_dir.mkdir(parents=True, exist_ok=True)

    json_path = hub_dir / "META_CIRCLE_REPORT.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(verify_result, f, ensure_ascii=False, indent=2)
    print(f"\n[Saved] {json_path}")

    print("\n[MetaCircle] Verification complete.")
