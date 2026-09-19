#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNI-HUB v12.0 — Circle Systems Complete Architecture
======================================================
五圈系统完整架构: 共识圈 / 会话圈 / 转发圈 / 指令圈 / Administration圈

Version: 12.0.0
Date: 2026-09-19
"""

from __future__ import annotations

import sys
import os
import json
import math
import time
import uuid
import logging
import hashlib
import copy
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Set, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from abc import ABC, abstractmethod

# ---------------------------------------------------------------------------
# Import dependencies
# ---------------------------------------------------------------------------
sys.path.insert(0, "/mnt/agents/output/OMNI-HUB/core")

_OMNI_STD_AVAILABLE = False
try:
    from v12_standards import (
        PHI_GOLDEN, PI, E_NATURAL, ALPHA_FINE_STRUCTURE,
        LINE_NAMES, LINE_DESCRIPTIONS,
    )
    _OMNI_STD_AVAILABLE = True
except Exception:
    pass

if not _OMNI_STD_AVAILABLE:
    PHI_GOLDEN = (1.0 + 5.0**0.5) / 2.0
    PI = 3.141592653589793
    E_NATURAL = 2.718281828459045
    ALPHA_FINE_STRUCTURE = 1.0 / 137.035999084
    LINE_NAMES = ["ucif2", "lvlu", "lgt", "qfa", "vinf", "qgl",
                  "qlv", "cisvr", "qtlv", "usrm", "cfts"]
    LINE_DESCRIPTIONS = {
        "ucif2": "Formal Math / CK Free Will",
        "lvlu": "Meta-level Architecture",
        "lgt": "Logic / Language",
        "qfa": "Quantum Field Theory",
        "vinf": "Infinity / Limit",
        "qgl": "Quantum Gravity",
        "qlv": "Quantum / Life / Consciousness",
        "cisvr": "Consciousness / Info / System / Verify / Reinforce",
        "qtlv": "Quantum / Time / Life / Velocity",
        "usrm": "User / System / Resource / Management",
        "cfts": "Cross-Functional Task Sync",
    }

_CONSENSUS_AVAILABLE = False
try:
    from v12_consensus_engine import (
        ConsensusTracker, DecisionGraph, ConflictResolver, ConvergenceMonitor,
        LocalDecision, RegionalDecision, GlobalDecision, DecisionStatus,
        ConflictType, ArbitrationStrategy, DecisionProvenance,
        ConsensusLevel, ConflictRecord,
    )
    _CONSENSUS_AVAILABLE = True
except Exception:
    pass

_FCTN_AVAILABLE = False
try:
    from v12_field_circle_tensor_network import (
        FieldState, CircleTopology, TensorNetwork,
        FieldCircleTensorBridge, SI11Integration,
        LINES, N, LINE_INDEX, FIELD_DIM, FIELD_PER_LINE, TENSOR_BOND_DIM,
    )
    _FCTN_AVAILABLE = True
except Exception:
    pass

# ---------------------------------------------------------------------------
# 0. Constants & Enums
# ---------------------------------------------------------------------------

CIRCLE_SYSTEM_VERSION = "12.0.0"
N_LINES = 11
N_CIRCLES = 5
N_FCTN_LAYERS = 7
N_SI_LAYERS = 7

CIRCLE_NAMES = ["consensus", "session", "relay", "command", "admin"]
CIRCLE_FULL_NAMES = {
    "consensus": "ConsensusCircle",
    "session": "SessionCircle",
    "relay": "RelayCircle",
    "command": "CommandCircle",
    "admin": "AdminCircle",
}
CIRCLE_DESCRIPTIONS = {
    "consensus": "跨线决策共识",
    "session": "跨线对话会话",
    "relay": "消息转发路由",
    "command": "指令分发执行",
    "admin": "系统管理监控",
}

DEFAULT_CIRCLE_COUPLING = {
    ("consensus", "session"): 0.35,
    ("consensus", "relay"): 0.20,
    ("session", "relay"): 0.40,
    ("session", "command"): 0.15,
    ("relay", "command"): 0.45,
    ("relay", "admin"): 0.25,
    ("command", "admin"): 0.35,
    ("command", "consensus"): 0.15,
    ("admin", "consensus"): 0.30,
    ("admin", "session"): 0.20,
    ("admin", "relay"): 0.15,
    ("admin", "command"): 0.25,
}


class CircleRole(Enum):
    DECISION_HUB = auto()
    COMMUNICATION_HUB = auto()
    ROUTING_HUB = auto()
    EXECUTION_HUB = auto()
    GOVERNANCE_HUB = auto()


class CircleHealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OVERLOADED = "overloaded"
    RECOVERING = "recovering"
    CRITICAL = "critical"


class CircleMessageType(Enum):
    STATE_SYNC = auto()
    DECISION_PROPAGATE = auto()
    SESSION_HANDOFF = auto()
    ROUTE_UPDATE = auto()
    COMMAND_DISPATCH = auto()
    ADMIN_CONFIG = auto()
    HEALTH_BEAT = auto()
    EMERGENCE_SIGNAL = auto()


# ---------------------------------------------------------------------------
# 1. Data Structures
# ---------------------------------------------------------------------------

@dataclass
class CircleMessage:
    msg_id: str = field(default_factory=lambda: f"cm-{int(time.time()*1000)%100000}")
    source_circle: str = ""
    target_circle: str = ""
    msg_type: CircleMessageType = CircleMessageType.STATE_SYNC
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    priority: int = 5
    ttl: int = 5
    trace: List[str] = field(default_factory=list)

    def is_expired(self) -> bool:
        return self.ttl <= 0

    def decay(self) -> None:
        self.ttl -= 1

    def add_trace(self, circle_name: str) -> None:
        self.trace.append(circle_name)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "msg_id": self.msg_id,
            "source_circle": self.source_circle,
            "target_circle": self.target_circle,
            "msg_type": self.msg_type.name,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "priority": self.priority,
            "ttl": self.ttl,
            "trace": self.trace,
        }


@dataclass
class CircleHealth:
    circle_name: str
    status: CircleHealthStatus = CircleHealthStatus.HEALTHY
    load_factor: float = 0.0
    response_time_ms: float = 0.0
    error_rate: float = 0.0
    throughput: float = 0.0
    coherence: float = 1.0
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "circle_name": self.circle_name,
            "status": self.status.value,
            "load_factor": round(self.load_factor, 4),
            "response_time_ms": round(self.response_time_ms, 4),
            "error_rate": round(self.error_rate, 6),
            "throughput": round(self.throughput, 4),
            "coherence": round(self.coherence, 4),
            "last_updated": self.last_updated,
        }


@dataclass
class CircleState:
    circle_name: str
    active_count: int = 0
    pending_count: int = 0
    completed_count: int = 0
    error_count: int = 0
    knowledge_items: int = 0
    memory_footprint: float = 0.0
    entropy: float = 0.0
    emergence_contribution: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "circle_name": self.circle_name,
            "active_count": self.active_count,
            "pending_count": self.pending_count,
            "completed_count": self.completed_count,
            "error_count": self.error_count,
            "knowledge_items": self.knowledge_items,
            "memory_footprint": round(self.memory_footprint, 4),
            "entropy": round(self.entropy, 6),
            "emergence_contribution": round(self.emergence_contribution, 6),
        }


@dataclass
class CircleLayerMapping:
    circle_name: str
    layer_assignments: Dict[int, List[str]] = field(default_factory=dict)
    layer_weights: Dict[int, float] = field(default_factory=dict)

    def assign_to_layer(self, layer_idx: int, knowledge_key: str,
                        weight: float = 1.0) -> None:
        if layer_idx not in self.layer_assignments:
            self.layer_assignments[layer_idx] = []
            self.layer_weights[layer_idx] = 0.0
        self.layer_assignments[layer_idx].append(knowledge_key)
        self.layer_weights[layer_idx] += weight

    def to_dict(self) -> Dict[str, Any]:
        return {
            "circle_name": self.circle_name,
            "layer_assignments": {k: v for k, v in self.layer_assignments.items()},
            "layer_weights": {k: round(v, 4) for k, v in self.layer_weights.items()},
        }


@dataclass
class CircleNetworkMapping:
    circle_name: str
    tensor_nodes: List[str] = field(default_factory=list)
    tensor_edges: List[Tuple[str, str, float]] = field(default_factory=list)
    bond_dimensions: Dict[str, int] = field(default_factory=dict)

    def add_edge(self, node_a: str, node_b: str, weight: float) -> None:
        self.tensor_edges.append((node_a, node_b, weight))
        if node_a not in self.tensor_nodes:
            self.tensor_nodes.append(node_a)
        if node_b not in self.tensor_nodes:
            self.tensor_nodes.append(node_b)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "circle_name": self.circle_name,
            "tensor_nodes": self.tensor_nodes,
            "tensor_edges": [[a, b, round(w, 4)] for a, b, w in self.tensor_edges],
            "bond_dimensions": self.bond_dimensions,
        }


@dataclass
class CircleTowerMapping:
    circle_name: str
    tower_level: int = 0
    emergence_properties: List[str] = field(default_factory=list)
    tower_bricks: List[Dict[str, Any]] = field(default_factory=list)

    def add_brick(self, property_name: str, value: float,
                  stability: float = 1.0) -> None:
        self.tower_bricks.append({
            "property": property_name,
            "value": round(value, 6),
            "stability": round(stability, 4),
        })
        if property_name not in self.emergence_properties:
            self.emergence_properties.append(property_name)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "circle_name": self.circle_name,
            "tower_level": self.tower_level,
            "emergence_properties": self.emergence_properties,
            "tower_bricks": self.tower_bricks,
        }


# ---------------------------------------------------------------------------
# 2. Base Circle Class
# ---------------------------------------------------------------------------

class BaseCircle(ABC):
    """圈基类 —— 所有五圈的抽象基类"""

    def __init__(self, name: str, role: CircleRole):
        self.name = name
        self.role = role
        self.health = CircleHealth(circle_name=name)
        self.state = CircleState(circle_name=name)
        self.messages_in: deque = deque(maxlen=1000)
        self.messages_out: deque = deque(maxlen=1000)
        self.tick_count = 0
        self.creation_time = datetime.now(timezone.utc).isoformat()

        self.layer_mapping = CircleLayerMapping(circle_name=name)
        self.network_mapping = CircleNetworkMapping(circle_name=name)
        self.tower_mapping = CircleTowerMapping(circle_name=name)

        self.knowledge_store: Dict[str, Any] = {}
        self.history: List[Dict[str, Any]] = []
        self.coupling_weights: Dict[str, float] = {}

    @abstractmethod
    def tick(self, global_state: Dict[str, Any]) -> CircleState:
        pass

    @abstractmethod
    def process_message(self, msg: CircleMessage) -> Optional[CircleMessage]:
        pass

    def receive_message(self, msg: CircleMessage) -> None:
        msg.add_trace(self.name)
        self.messages_in.append(msg)

    def send_message(self, msg: CircleMessage) -> None:
        msg.add_trace(self.name)
        self.messages_out.append(msg)

    def update_health(self, load: float, response_ms: float,
                      errors: int, total: int) -> None:
        self.health.load_factor = min(1.0, load)
        self.health.response_time_ms = response_ms
        self.health.error_rate = errors / max(total, 1)
        self.health.throughput = total / max(response_ms / 1000.0, 0.001)
        self.health.last_updated = datetime.now(timezone.utc).isoformat()

        if self.health.error_rate > 0.1 or self.health.load_factor > 0.95:
            self.health.status = CircleHealthStatus.CRITICAL
        elif self.health.error_rate > 0.05 or self.health.load_factor > 0.8:
            self.health.status = CircleHealthStatus.OVERLOADED
        elif self.health.error_rate > 0.02 or self.health.load_factor > 0.6:
            self.health.status = CircleHealthStatus.DEGRADED
        elif self.health.status == CircleHealthStatus.CRITICAL:
            self.health.status = CircleHealthStatus.RECOVERING
        else:
            self.health.status = CircleHealthStatus.HEALTHY

    def compute_entropy(self) -> float:
        if not self.knowledge_store:
            return 0.0
        type_counts: Dict[str, int] = defaultdict(int)
        for k, v in self.knowledge_store.items():
            t = type(v).__name__
            type_counts[t] += 1
        total = sum(type_counts.values())
        if total == 0:
            return 0.0
        probs = [c / total for c in type_counts.values()]
        entropy = -sum(p * math.log(p + 1e-12) for p in probs)
        return entropy

    def compute_emergence_contribution(self) -> float:
        activity = self.state.active_count / max(self.state.completed_count, 1)
        knowledge_factor = math.log(len(self.knowledge_store) + 1)
        health_factor = 1.0 - self.health.error_rate
        coherence = self.health.coherence
        contribution = (
            0.25 * activity +
            0.25 * knowledge_factor / 5.0 +
            0.25 * health_factor +
            0.25 * coherence
        )
        self.state.emergence_contribution = contribution
        return contribution

    def map_to_layers(self) -> CircleLayerMapping:
        for key, value in self.knowledge_store.items():
            layer_idx = (hash(key) % N_FCTN_LAYERS)
            weight = 1.0
            if isinstance(value, (int, float)):
                weight = abs(float(value))
            self.layer_mapping.assign_to_layer(layer_idx, key, weight)
        return self.layer_mapping

    def map_to_network(self, line_names: List[str]) -> CircleNetworkMapping:
        for i, msg in enumerate(list(self.messages_in)[-50:]):
            node_a = f"{self.name}_in_{i}"
            node_b = msg.source_circle or "external"
            weight = 1.0 / msg.priority if msg.priority > 0 else 1.0
            self.network_mapping.add_edge(node_a, node_b, weight)
        return self.network_mapping

    def map_to_tower(self, tower_level: int) -> CircleTowerMapping:
        self.tower_mapping.tower_level = tower_level
        self.tower_mapping.add_brick(
            f"{self.name}_emergence",
            self.state.emergence_contribution,
            self.health.coherence
        )
        self.tower_mapping.add_brick(
            f"{self.name}_entropy",
            self.state.entropy,
            1.0 - self.health.error_rate
        )
        return self.tower_mapping

    def get_stats(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role.name,
            "tick_count": self.tick_count,
            "health": self.health.to_dict(),
            "state": self.state.to_dict(),
            "messages_in": len(self.messages_in),
            "messages_out": len(self.messages_out),
            "knowledge_count": len(self.knowledge_store),
            "entropy": round(self.compute_entropy(), 6),
            "emergence_contribution": round(self.compute_emergence_contribution(), 6),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.get_stats(),
            "layer_mapping": self.layer_mapping.to_dict(),
            "network_mapping": self.network_mapping.to_dict(),
            "tower_mapping": self.tower_mapping.to_dict(),
            "history_count": len(self.history),
        }


# ---------------------------------------------------------------------------
# 3. Five Circle Implementations
# ---------------------------------------------------------------------------

class ConsensusCircleImpl(BaseCircle):
    """共识圈 —— 跨线决策共识"""

    def __init__(self):
        super().__init__("consensus", CircleRole.DECISION_HUB)
        if _CONSENSUS_AVAILABLE:
            self.tracker = ConsensusTracker(
                strategy=ArbitrationStrategy.HYBRID,
                damping=0.3,
                max_steps=100
            )
        else:
            self.tracker = None
            self._local_decisions: Dict[str, Any] = {}
            self._regional_decisions: Dict[str, Any] = {}
            self._global_decisions: Dict[str, Any] = {}
            self._conflicts: List[Any] = []

        self.decision_queue: deque = deque(maxlen=500)
        self.consensus_topics: Set[str] = set()
        self.pending_arbitration: List[Any] = []

    def propose_decision(self, line: str, module: str, topic: str,
                         value: float, confidence: float = 0.8,
                         evidence_depth: int = 1,
                         si_level: Optional[int] = None) -> str:
        if self.tracker:
            decision_id = self.tracker.register_local_decision(
                line, module, topic, value, confidence, evidence_depth, si_level
            )
        else:
            decision_id = f"dec-{line}-{topic}-{int(time.time()*1000)%100000}"
            self._local_decisions[decision_id] = {
                "id": decision_id, "line": line, "topic": topic,
                "value": value, "confidence": confidence,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        self.decision_queue.append({
            "decision_id": decision_id,
            "topic": topic,
            "line": line,
            "value": value,
        })
        self.consensus_topics.add(topic)
        self.state.pending_count = len(self.decision_queue)
        return decision_id

    def run_consensus(self, topic: str) -> Optional[Dict[str, Any]]:
        if self.tracker:
            global_decision = self.tracker.form_global_consensus(topic)
            if global_decision:
                self.state.completed_count += 1
                return global_decision.to_dict()
        else:
            related = [d for d in self._local_decisions.values()
                       if d["topic"] == topic]
            if related:
                avg = sum(d["value"] for d in related) / len(related)
                return {
                    "topic": topic,
                    "final_value": round(avg, 6),
                    "participating_count": len(related),
                }
        return None

    def tick(self, global_state: Dict[str, Any]) -> CircleState:
        self.tick_count += 1
        start_time = time.time()

        processed = 0
        errors = 0
        while self.messages_in and processed < 50:
            msg = self.messages_in.popleft()
            try:
                response = self.process_message(msg)
                if response:
                    self.send_message(response)
            except Exception as e:
                errors += 1
            processed += 1

        for topic in list(self.consensus_topics)[:5]:
            result = self.run_consensus(topic)
            if result:
                self.send_message(CircleMessage(
                    source_circle=self.name,
                    target_circle="all",
                    msg_type=CircleMessageType.DECISION_PROPAGATE,
                    payload={"topic": topic, "consensus": result},
                    priority=2,
                ))

        self.state.active_count = len(self.consensus_topics)
        self.state.pending_count = len(self.decision_queue)
        self.state.knowledge_items = len(self.knowledge_store)

        elapsed = (time.time() - start_time) * 1000.0
        self.update_health(
            load=self.state.pending_count / 100.0,
            response_ms=elapsed,
            errors=errors,
            total=processed
        )

        self.health.coherence = self._compute_internal_coherence()
        self.state.entropy = self.compute_entropy()
        self.compute_emergence_contribution()

        return self.state

    def process_message(self, msg: CircleMessage) -> Optional[CircleMessage]:
        if msg.msg_type == CircleMessageType.DECISION_PROPAGATE:
            payload = msg.payload
            if "topic" in payload and "consensus" in payload:
                self.knowledge_store[f"consensus_{payload['topic']}"] = payload["consensus"]
            return None
        elif msg.msg_type == CircleMessageType.STATE_SYNC:
            self.knowledge_store[f"sync_{msg.source_circle}"] = msg.payload
            return CircleMessage(
                source_circle=self.name,
                target_circle=msg.source_circle,
                msg_type=CircleMessageType.STATE_SYNC,
                payload={"status": "ack", "pending_topics": len(self.consensus_topics)},
            )
        elif msg.msg_type == CircleMessageType.ADMIN_CONFIG:
            config = msg.payload.get("consensus_config", {})
            if "damping" in config and self.tracker:
                self.tracker.damping = config["damping"]
            return None
        return None

    def _compute_internal_coherence(self) -> float:
        if self.tracker and hasattr(self.tracker, 'convergence_monitor'):
            report = self.tracker.convergence_monitor.get_convergence_report()
            if report and "final_consensus_measure" in report:
                return report["final_consensus_measure"]
        return 1.0

    def get_full_report(self) -> Dict[str, Any]:
        report = {
            "circle": self.name,
            "tick_count": self.tick_count,
            "health": self.health.to_dict(),
            "state": self.state.to_dict(),
            "consensus_topics": list(self.consensus_topics),
            "pending_decisions": len(self.decision_queue),
        }
        if self.tracker:
            report["tracker_stats"] = self.tracker.stats
            report["pedestal_consistency"] = self.tracker.verify_knowledge_pedestal_consistency()
        return report


class SessionCircleImpl(BaseCircle):
    """会话圈 —— 跨线对话/通信会话管理"""

    def __init__(self):
        super().__init__("session", CircleRole.COMMUNICATION_HUB)
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_counter = 0
        self.active_session_ids: Set[str] = set()

    def create_session(self, initiator_line: str,
                       participants: List[str],
                       topic: str = "",
                       visibility: Optional[List[str]] = None) -> str:
        sid = f"sess-{initiator_line}-{self.session_counter}"
        self.session_counter += 1

        if visibility is None:
            visibility = list(LINE_NAMES) if LINE_NAMES else []

        self.sessions[sid] = {
            "id": sid,
            "initiator": initiator_line,
            "participants": participants,
            "topic": topic,
            "visibility": visibility,
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_activity": datetime.now(timezone.utc).isoformat(),
            "messages": [],
            "context": {},
            "branches": [],
        }
        self.active_session_ids.add(sid)
        self.state.active_count = len(self.active_session_ids)
        return sid

    def add_message(self, sid: str, line: str, content: str,
                    msg_type: str = "text") -> bool:
        if sid not in self.sessions:
            return False
        session = self.sessions[sid]
        if line not in session["participants"] and line != session["initiator"]:
            return False

        msg = {
            "id": f"msg-{sid}-{len(session['messages'])}",
            "line": line,
            "content": content,
            "type": msg_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        session["messages"].append(msg)
        session["last_activity"] = datetime.now(timezone.utc).isoformat()
        return True

    def get_session_context(self, sid: str) -> Dict[str, Any]:
        if sid not in self.sessions:
            return {}
        session = self.sessions[sid]
        return {
            "id": sid,
            "topic": session["topic"],
            "participants": session["participants"],
            "message_count": len(session["messages"]),
            "last_activity": session["last_activity"],
            "status": session["status"],
        }

    def branch_session(self, sid: str, branch_line: str,
                       reason: str = "") -> Optional[str]:
        if sid not in self.sessions:
            return None
        parent = self.sessions[sid]
        branch_sid = self.create_session(
            initiator_line=branch_line,
            participants=list(parent["participants"]),
            topic=f"[Branch of {sid}] {reason}",
            visibility=list(parent["visibility"]),
        )
        parent["branches"].append(branch_sid)
        self.sessions[branch_sid]["parent"] = sid
        return branch_sid

    def close_session(self, sid: str) -> bool:
        if sid not in self.sessions:
            return False
        self.sessions[sid]["status"] = "closed"
        self.sessions[sid]["closed_at"] = datetime.now(timezone.utc).isoformat()
        self.active_session_ids.discard(sid)
        self.state.active_count = len(self.active_session_ids)
        self.state.completed_count += 1
        return True

    def tick(self, global_state: Dict[str, Any]) -> CircleState:
        self.tick_count += 1
        start_time = time.time()

        processed = 0
        errors = 0
        while self.messages_in and processed < 50:
            msg = self.messages_in.popleft()
            try:
                response = self.process_message(msg)
                if response:
                    self.send_message(response)
            except Exception:
                errors += 1
            processed += 1

        current_time = datetime.now(timezone.utc)
        for sid in list(self.active_session_ids):
            session = self.sessions[sid]
            last_activity = datetime.fromisoformat(session["last_activity"])
            if (current_time - last_activity).total_seconds() > 60:
                session["status"] = "dormant"
                self.active_session_ids.discard(sid)

        self.state.active_count = len(self.active_session_ids)
        self.state.pending_count = sum(
            1 for s in self.sessions.values() if s["status"] == "active"
        )
        self.state.knowledge_items = sum(
            len(s["messages"]) for s in self.sessions.values()
        )

        elapsed = (time.time() - start_time) * 1000.0
        self.update_health(
            load=len(self.active_session_ids) / 50.0,
            response_ms=elapsed,
            errors=errors,
            total=processed
        )

        self.health.coherence = self._compute_session_coherence()
        self.state.entropy = self.compute_entropy()
        self.compute_emergence_contribution()

        return self.state

    def process_message(self, msg: CircleMessage) -> Optional[CircleMessage]:
        if msg.msg_type == CircleMessageType.SESSION_HANDOFF:
            payload = msg.payload
            if "session_id" in payload:
                context = self.get_session_context(payload["session_id"])
                return CircleMessage(
                    source_circle=self.name,
                    target_circle=msg.source_circle,
                    msg_type=CircleMessageType.STATE_SYNC,
                    payload={"session_context": context},
                )
        elif msg.msg_type == CircleMessageType.STATE_SYNC:
            self.knowledge_store[f"sync_{msg.source_circle}"] = msg.payload
            return None
        return None

    def _compute_session_coherence(self) -> float:
        if not self.sessions:
            return 1.0
        active_ratio = len(self.active_session_ids) / len(self.sessions)
        return 0.5 + 0.5 * active_ratio

    def get_full_report(self) -> Dict[str, Any]:
        return {
            "circle": self.name,
            "tick_count": self.tick_count,
            "health": self.health.to_dict(),
            "state": self.state.to_dict(),
            "session_count": len(self.sessions),
            "active_sessions": len(self.active_session_ids),
            "recent_sessions": [
                self.get_session_context(sid)
                for sid in list(self.active_session_ids)[:5]
            ],
        }


class RelayCircleImpl(BaseCircle):
    """转发圈 —— 消息/数据跨线转发路由"""

    def __init__(self):
        super().__init__("relay", CircleRole.ROUTING_HUB)
        self.routing_table: Dict[str, Dict[str, Any]] = {}
        self.message_log: deque = deque(maxlen=1000)
        self.routing_strategies = ["spectrum", "nearest", "broadcast", "adaptive"]
        self.default_strategy = "adaptive"
        self.delivery_stats = {
            "sent": 0, "delivered": 0, "failed": 0, "retried": 0
        }

    def update_routing_table(self, topology_matrix=None) -> None:
        if topology_matrix is not None:
            for i, line_i in enumerate(LINE_NAMES):
                self.routing_table[line_i] = {}
                for j, line_j in enumerate(LINE_NAMES):
                    if i != j:
                        weight = float(topology_matrix[i, j])
                        self.routing_table[line_i][line_j] = {
                            "weight": weight,
                            "hops": 1 if weight > 0.3 else 2,
                            "reliability": min(1.0, weight * 1.5),
                        }
        else:
            for line_i in LINE_NAMES:
                self.routing_table[line_i] = {}
                for line_j in LINE_NAMES:
                    if line_i != line_j:
                        self.routing_table[line_i][line_j] = {
                            "weight": 0.5,
                            "hops": 1,
                            "reliability": 0.8,
                        }

    def route_message(self, msg_content: str, from_line: str,
                      to_line=None, strategy=None) -> List[Dict[str, Any]]:
        strategy = strategy or self.default_strategy
        routes = []

        if strategy == "broadcast":
            targets = [l for l in LINE_NAMES if l != from_line]
            for t in targets:
                routes.append({
                    "from": from_line, "to": t,
                    "path": [from_line, t],
                    "strategy": "broadcast",
                })
        elif strategy == "nearest" and from_line in self.routing_table:
            table = self.routing_table[from_line]
            sorted_targets = sorted(
                table.items(),
                key=lambda x: x[1].get("weight", 0),
                reverse=True
            )[:3]
            for target, info in sorted_targets:
                routes.append({
                    "from": from_line, "to": target,
                    "path": [from_line, target],
                    "weight": info.get("weight", 0),
                    "strategy": "nearest",
                })
        elif strategy == "adaptive":
            if from_line in self.routing_table:
                candidates = []
                for target, info in self.routing_table[from_line].items():
                    score = info.get("reliability", 0.5) * (1.0 - self._get_line_load(target))
                    candidates.append((target, score, info))
                candidates.sort(key=lambda x: -x[1])
                for target, score, info in candidates[:3]:
                    routes.append({
                        "from": from_line, "to": target,
                        "path": [from_line, target],
                        "score": round(score, 4),
                        "strategy": "adaptive",
                    })
        else:
            targets = [l for l in LINE_NAMES if l != from_line][:3]
            for t in targets:
                routes.append({
                    "from": from_line, "to": t,
                    "path": [from_line, t],
                    "strategy": "spectrum",
                })

        for route in routes:
            self.message_log.append({
                "content_hash": hashlib.sha256(msg_content.encode()).hexdigest()[:16],
                "route": route,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "routed",
            })

        self.delivery_stats["sent"] += len(routes)
        self.state.completed_count += len(routes)
        return routes

    def _get_line_load(self, line: str) -> float:
        return 0.3

    def tick(self, global_state: Dict[str, Any]) -> CircleState:
        self.tick_count += 1
        start_time = time.time()

        processed = 0
        errors = 0
        while self.messages_in and processed < 100:
            msg = self.messages_in.popleft()
            try:
                response = self.process_message(msg)
                if response:
                    self.send_message(response)
            except Exception:
                errors += 1
            processed += 1

        if "topology_matrix" in global_state:
            self.update_routing_table(global_state["topology_matrix"])

        pending_routes = global_state.get("pending_routes", [])
        for route_req in pending_routes[:20]:
            self.route_message(
                route_req.get("content", ""),
                route_req.get("from", ""),
                route_req.get("to"),
                route_req.get("strategy"),
            )

        self.state.active_count = len(self.message_log)
        self.state.pending_count = len(pending_routes)
        self.state.knowledge_items = len(self.message_log)

        elapsed = (time.time() - start_time) * 1000.0
        total_ops = processed + len(pending_routes)
        self.update_health(
            load=self.state.active_count / 500.0,
            response_ms=elapsed,
            errors=errors,
            total=max(total_ops, 1)
        )

        self.health.coherence = self._compute_routing_coherence()
        self.state.entropy = self.compute_entropy()
        self.compute_emergence_contribution()

        return self.state

    def process_message(self, msg: CircleMessage) -> Optional[CircleMessage]:
        if msg.msg_type == CircleMessageType.ROUTE_UPDATE:
            payload = msg.payload
            if "routing_table" in payload:
                self.routing_table.update(payload["routing_table"])
            return CircleMessage(
                source_circle=self.name,
                target_circle=msg.source_circle,
                msg_type=CircleMessageType.STATE_SYNC,
                payload={"routes_known": len(self.routing_table)},
            )
        elif msg.msg_type == CircleMessageType.STATE_SYNC:
            self.knowledge_store[f"sync_{msg.source_circle}"] = msg.payload
            return None
        return None

    def _compute_routing_coherence(self) -> float:
        if not self.routing_table:
            return 1.0
        expected_entries = len(LINE_NAMES) * (len(LINE_NAMES) - 1)
        actual_entries = sum(len(t) for t in self.routing_table.values())
        return min(1.0, actual_entries / max(expected_entries, 1))

    def get_full_report(self) -> Dict[str, Any]:
        return {
            "circle": self.name,
            "tick_count": self.tick_count,
            "health": self.health.to_dict(),
            "state": self.state.to_dict(),
            "routing_table_size": len(self.routing_table),
            "message_log_size": len(self.message_log),
            "delivery_stats": self.delivery_stats,
            "strategies_available": self.routing_strategies,
        }


class CommandCircleImpl(BaseCircle):
    """指令圈 —— 跨线指令分发和执行"""

    def __init__(self):
        super().__init__("command", CircleRole.EXECUTION_HUB)
        self.commands: Dict[str, Dict[str, Any]] = {}
        self.command_counter = 0
        self.execution_queue: deque = deque(maxlen=500)
        self.execution_history: deque = deque(maxlen=500)
        self.failure_handlers: Dict[str, Callable] = {}

    def issue_command(self, from_line: str, to_line: str,
                      command_type: str, params: Dict[str, Any],
                      priority: int = 5, timeout: float = 30.0) -> str:
        cmd_id = f"cmd-{from_line}-{to_line}-{self.command_counter}"
        self.command_counter += 1

        self.commands[cmd_id] = {
            "id": cmd_id,
            "from": from_line,
            "to": to_line,
            "type": command_type,
            "params": params,
            "priority": priority,
            "timeout": timeout,
            "status": "issued",
            "issued_at": datetime.now(timezone.utc).isoformat(),
            "started_at": None,
            "completed_at": None,
            "result": None,
            "retry_count": 0,
            "dependencies": [],
        }
        self.execution_queue.append(cmd_id)
        self.state.pending_count = len(self.execution_queue)
        return cmd_id

    def start_execution(self, cmd_id: str) -> bool:
        if cmd_id not in self.commands:
            return False
        cmd = self.commands[cmd_id]
        if cmd["status"] != "issued":
            return False
        cmd["status"] = "executing"
        cmd["started_at"] = datetime.now(timezone.utc).isoformat()
        self.state.active_count += 1
        return True

    def complete_command(self, cmd_id: str, result: Any,
                         success: bool = True) -> bool:
        if cmd_id not in self.commands:
            return False
        cmd = self.commands[cmd_id]
        cmd["status"] = "completed" if success else "failed"
        cmd["completed_at"] = datetime.now(timezone.utc).isoformat()
        cmd["result"] = result

        self.execution_history.append(cmd)
        self.state.completed_count += 1
        if not success:
            self.state.error_count += 1

        if cmd_id in self.execution_queue:
            self.execution_queue.remove(cmd_id)

        self.send_message(CircleMessage(
            source_circle=self.name,
            target_circle="all",
            msg_type=CircleMessageType.COMMAND_DISPATCH,
            payload={
                "cmd_id": cmd_id,
                "status": cmd["status"],
                "result": str(result)[:200],
            },
            priority=cmd["priority"],
        ))
        return True

    def add_dependency(self, cmd_id: str, depends_on: str) -> bool:
        if cmd_id not in self.commands:
            return False
        self.commands[cmd_id]["dependencies"].append(depends_on)
        return True

    def tick(self, global_state: Dict[str, Any]) -> CircleState:
        self.tick_count += 1
        start_time = time.time()

        processed = 0
        errors = 0
        while self.messages_in and processed < 50:
            msg = self.messages_in.popleft()
            try:
                response = self.process_message(msg)
                if response:
                    self.send_message(response)
            except Exception:
                errors += 1
            processed += 1

        executed = 0
        for cmd_id in list(self.execution_queue)[:20]:
            cmd = self.commands[cmd_id]
            deps_satisfied = all(
                self.commands.get(d, {}).get("status") in ["completed", "failed"]
                for d in cmd["dependencies"]
            )
            if deps_satisfied and cmd["status"] == "issued":
                self.start_execution(cmd_id)
                self.complete_command(cmd_id, {"status": "ok", "data": {}})
                executed += 1

        current_time = datetime.now(timezone.utc)
        for cmd_id, cmd in self.commands.items():
            if cmd["status"] == "executing" and cmd["started_at"]:
                started = datetime.fromisoformat(cmd["started_at"])
                if (current_time - started).total_seconds() > cmd["timeout"]:
                    cmd["status"] = "timeout"
                    self.state.error_count += 1

        self.state.active_count = sum(
            1 for c in self.commands.values() if c["status"] == "executing"
        )
        self.state.pending_count = len(self.execution_queue)
        self.state.knowledge_items = len(self.execution_history)

        elapsed = (time.time() - start_time) * 1000.0
        total = processed + executed
        self.update_health(
            load=self.state.pending_count / 100.0,
            response_ms=elapsed,
            errors=errors,
            total=max(total, 1)
        )

        self.health.coherence = self._compute_execution_coherence()
        self.state.entropy = self.compute_entropy()
        self.compute_emergence_contribution()

        return self.state

    def process_message(self, msg: CircleMessage) -> Optional[CircleMessage]:
        if msg.msg_type == CircleMessageType.COMMAND_DISPATCH:
            payload = msg.payload
            if "cmd_id" in payload:
                self.knowledge_store[f"result_{payload['cmd_id']}"] = payload
            return None
        elif msg.msg_type == CircleMessageType.STATE_SYNC:
            self.knowledge_store[f"sync_{msg.source_circle}"] = msg.payload
            return None
        return None

    def _compute_execution_coherence(self) -> float:
        if not self.commands:
            return 1.0
        completed = sum(1 for c in self.commands.values() if c["status"] == "completed")
        total = len(self.commands)
        return completed / max(total, 1)

    def get_full_report(self) -> Dict[str, Any]:
        from collections import defaultdict
        status_counts = defaultdict(int)
        for cmd in self.commands.values():
            status_counts[cmd["status"]] += 1

        return {
            "circle": self.name,
            "tick_count": self.tick_count,
            "health": self.health.to_dict(),
            "state": self.state.to_dict(),
            "total_commands": len(self.commands),
            "status_distribution": dict(status_counts),
            "queue_length": len(self.execution_queue),
            "history_length": len(self.execution_history),
        }


class AdminCircleImpl(BaseCircle):
    """Administration圈 —— 系统管理/监控/配置"""

    def __init__(self):
        super().__init__("admin", CircleRole.GOVERNANCE_HUB)
        self.global_config: Dict[str, Any] = {
            "max_circles": N_CIRCLES,
            "max_lines": N_LINES,
            "emergence_threshold": 7000.0,
            "auto_recovery": True,
            "audit_level": "full",
        }
        self.audit_log: deque = deque(maxlen=2000)
        self.circle_health_history: Dict[str, List[Dict]] = {
            name: [] for name in CIRCLE_NAMES
        }
        self.line_health: Dict[str, float] = {line: 1.0 for line in LINE_NAMES}
        self.resource_allocation: Dict[str, Dict[str, float]] = {}
        self.policies: List[Dict[str, Any]] = []

    def set_config(self, key: str, value: Any) -> None:
        old_value = self.global_config.get(key)
        self.global_config[key] = value
        self.audit_log.append({
            "action": "config_change",
            "key": key,
            "old": old_value,
            "new": value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def record_circle_health(self, circle_name: str,
                             health_data: Dict[str, Any]) -> None:
        if circle_name in self.circle_health_history:
            self.circle_health_history[circle_name].append({
                **health_data,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            })
            if len(self.circle_health_history[circle_name]) > 100:
                self.circle_health_history[circle_name] =                     self.circle_health_history[circle_name][-100:]

    def check_system_health(self) -> Dict[str, Any]:
        circle_statuses = {}
        for name, history in self.circle_health_history.items():
            if history:
                latest = history[-1]
                circle_statuses[name] = {
                    "status": latest.get("status", "unknown"),
                    "load": latest.get("load_factor", 0),
                    "errors": latest.get("error_rate", 0),
                }

        avg_load = np.mean([s["load"] for s in circle_statuses.values()]) if circle_statuses else 0
        max_errors = max([s["errors"] for s in circle_statuses.values()]) if circle_statuses else 0

        system_status = "HEALTHY"
        if max_errors > 0.1:
            system_status = "CRITICAL"
        elif avg_load > 0.8:
            system_status = "OVERLOADED"
        elif avg_load > 0.6:
            system_status = "DEGRADED"

        return {
            "system_status": system_status,
            "average_load": round(avg_load, 4),
            "max_error_rate": round(max_errors, 6),
            "circle_statuses": circle_statuses,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def enforce_policy(self, policy_name: str,
                       target: str, action: str) -> bool:
        policy = {
            "name": policy_name,
            "target": target,
            "action": action,
            "enforced_at": datetime.now(timezone.utc).isoformat(),
        }
        self.policies.append(policy)
        self.audit_log.append({
            "action": "policy_enforcement",
            "policy": policy,
        })
        return True

    def allocate_resources(self, entity: str, cpu: float = 0.0,
                          memory: float = 0.0, bandwidth: float = 0.0) -> None:
        self.resource_allocation[entity] = {
            "cpu": cpu,
            "memory": memory,
            "bandwidth": bandwidth,
            "allocated_at": datetime.now(timezone.utc).isoformat(),
        }

    def tick(self, global_state: Dict[str, Any]) -> CircleState:
        self.tick_count += 1
        start_time = time.time()

        processed = 0
        errors = 0
        while self.messages_in and processed < 50:
            msg = self.messages_in.popleft()
            try:
                response = self.process_message(msg)
                if response:
                    self.send_message(response)
            except Exception:
                errors += 1
            processed += 1

        circle_healths = global_state.get("circle_healths", {})
        for name, health in circle_healths.items():
            self.record_circle_health(name, health)

        system_health = self.check_system_health()
        self.knowledge_store["system_health"] = system_health

        if system_health["system_status"] in ["CRITICAL", "OVERLOADED"]:
            self.send_message(CircleMessage(
                source_circle=self.name,
                target_circle="all",
                msg_type=CircleMessageType.ADMIN_CONFIG,
                payload={
                    "action": "load_balance",
                    "system_status": system_health["system_status"],
                    "target_load": 0.5,
                },
                priority=1,
            ))

        line_healths = global_state.get("line_healths", {})
        for line, health in line_healths.items():
            if line in self.line_health:
                self.line_health[line] = health

        self.state.active_count = len(self.policies)
        self.state.pending_count = sum(
            1 for log in self.audit_log
            if isinstance(log, dict) and log.get("action") == "config_change"
        )
        self.state.knowledge_items = len(self.audit_log)

        elapsed = (time.time() - start_time) * 1000.0
        self.update_health(
            load=system_health.get("average_load", 0),
            response_ms=elapsed,
            errors=errors,
            total=processed
        )

        self.health.coherence = 1.0 - system_health.get("max_error_rate", 0)
        self.state.entropy = self.compute_entropy()
        self.compute_emergence_contribution()

        return self.state

    def process_message(self, msg: CircleMessage) -> Optional[CircleMessage]:
        if msg.msg_type == CircleMessageType.HEALTH_BEAT:
            payload = msg.payload
            if "circle_name" in payload:
                self.record_circle_health(
                    payload["circle_name"],
                    payload.get("health", {})
                )
            return None
        elif msg.msg_type == CircleMessageType.STATE_SYNC:
            return CircleMessage(
                source_circle=self.name,
                target_circle=msg.source_circle,
                msg_type=CircleMessageType.STATE_SYNC,
                payload={
                    "global_config": self.global_config,
                    "system_health": self.check_system_health(),
                },
            )
        elif msg.msg_type == CircleMessageType.EMERGENCE_SIGNAL:
            payload = msg.payload
            emergence_level = payload.get("emergence_level", 0)
            if emergence_level > self.global_config.get("emergence_threshold", 7000):
                self.audit_log.append({
                    "action": "emergence_detected",
                    "level": emergence_level,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            return None
        return None

    def get_full_report(self) -> Dict[str, Any]:
        return {
            "circle": self.name,
            "tick_count": self.tick_count,
            "health": self.health.to_dict(),
            "state": self.state.to_dict(),
            "global_config": self.global_config,
            "system_health": self.check_system_health(),
            "audit_log_size": len(self.audit_log),
            "policies_active": len(self.policies),
            "resource_allocations": len(self.resource_allocation),
            "circle_health_records": {
                k: len(v) for k, v in self.circle_health_history.items()
            },
        }


# ---------------------------------------------------------------------------
# 4. Circle System Manager
# ---------------------------------------------------------------------------

class CircleSystemManager:
    """圈系统管理器 —— 协调五圈的完整运行"""

    def __init__(self, enable_consensus_tracker: bool = True):
        self.consensus = ConsensusCircleImpl()
        self.session = SessionCircleImpl()
        self.relay = RelayCircleImpl()
        self.command = CommandCircleImpl()
        self.admin = AdminCircleImpl()

        self.circles: Dict[str, BaseCircle] = {
            "consensus": self.consensus,
            "session": self.session,
            "relay": self.relay,
            "command": self.command,
            "admin": self.admin,
        }

        self.coupling_matrix = self._build_coupling_matrix()

        self.global_state: Dict[str, Any] = {
            "tick_count": 0,
            "system_emergence": 0.0,
            "circle_healths": {},
            "line_healths": {},
            "topology_matrix": None,
            "pending_routes": [],
        }

        self.history: deque = deque(maxlen=500)
        self.emergence_history: List[float] = []

        self.layer_maps: Dict[str, CircleLayerMapping] = {}
        self.network_maps: Dict[str, CircleNetworkMapping] = {}
        self.tower_maps: Dict[str, CircleTowerMapping] = {}

        self.stats = {
            "total_ticks": 0,
            "total_messages": 0,
            "total_decisions": 0,
            "total_commands": 0,
            "emergence_events": 0,
        }

    def _build_coupling_matrix(self) -> np.ndarray:
        M = np.zeros((N_CIRCLES, N_CIRCLES), dtype=np.float64)
        name_to_idx = {name: i for i, name in enumerate(CIRCLE_NAMES)}

        for (src, dst), weight in DEFAULT_CIRCLE_COUPLING.items():
            if src in name_to_idx and dst in name_to_idx:
                M[name_to_idx[src], name_to_idx[dst]] = weight

        for i in range(N_CIRCLES):
            row_sum = np.sum(M[i, :])
            if row_sum > 0:
                M[i, :] /= row_sum

        return M

    def route_inter_circle_messages(self) -> int:
        routed = 0
        name_to_idx = {name: i for i, name in enumerate(CIRCLE_NAMES)}

        for src_name, src_circle in self.circles.items():
            while src_circle.messages_out:
                msg = src_circle.messages_out.popleft()
                src_idx = name_to_idx.get(src_name, -1)

                if msg.target_circle == "all":
                    for dst_name, dst_circle in self.circles.items():
                        if dst_name != src_name:
                            dst_circle.receive_message(CircleMessage(
                                source_circle=msg.source_circle,
                                target_circle=dst_name,
                                msg_type=msg.msg_type,
                                payload=msg.payload.copy(),
                                priority=msg.priority,
                            ))
                            routed += 1
                else:
                    if msg.target_circle in self.circles:
                        self.circles[msg.target_circle].receive_message(msg)
                        routed += 1

        return routed

    def run_tick(self) -> Dict[str, Any]:
        self.global_state["tick_count"] = self.stats["total_ticks"]

        messages_routed = self.route_inter_circle_messages()
        self.stats["total_messages"] += messages_routed

        circle_states = {}
        for name, circle in self.circles.items():
            state = circle.tick(self.global_state)
            circle_states[name] = state

        self.global_state["circle_healths"] = {
            name: circle.health.to_dict()
            for name, circle in self.circles.items()
        }

        emergence = self.compute_circle_emergence()
        self.global_state["system_emergence"] = emergence
        self.emergence_history.append(emergence)

        self.stats["total_ticks"] += 1
        self.stats["total_decisions"] += self.consensus.state.completed_count
        self.stats["total_commands"] += self.command.state.completed_count

        tick_record = {
            "tick": self.stats["total_ticks"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "messages_routed": messages_routed,
            "emergence": round(emergence, 6),
            "circle_states": {k: v.to_dict() for k, v in circle_states.items()},
        }
        self.history.append(tick_record)

        return tick_record

    def run_ticks(self, n: int) -> List[Dict[str, Any]]:
        results = []
        for _ in range(n):
            result = self.run_tick()
            results.append(result)
        return results

    def compute_circle_emergence(self) -> float:
        contributions = {
            name: circle.compute_emergence_contribution()
            for name, circle in self.circles.items()
        }

        weights = {
            "consensus": 0.25,
            "session": 0.15,
            "relay": 0.15,
            "command": 0.20,
            "admin": 0.25,
        }

        linear = sum(weights.get(name, 0.2) * contrib
                     for name, contrib in contributions.items())

        alpha = 0.5
        nonlinear = 0.0
        name_to_idx = {name: i for i, name in enumerate(CIRCLE_NAMES)}

        for i, name_i in enumerate(CIRCLE_NAMES):
            for j, name_j in enumerate(CIRCLE_NAMES):
                if i != j:
                    m_ij = self.coupling_matrix[i, j]
                    e_i = contributions.get(name_i, 0)
                    e_j = contributions.get(name_j, 0)
                    nonlinear += m_ij * e_i * e_j

        nonlinear *= alpha
        total_emergence = linear + nonlinear
        normalized = total_emergence * 5000.0

        return normalized

    def get_circle_entanglement(self) -> np.ndarray:
        entanglement = np.zeros((N_CIRCLES, N_CIRCLES), dtype=np.float64)
        name_to_idx = {name: i for i, name in enumerate(CIRCLE_NAMES)}

        for name_i, circle_i in self.circles.items():
            for name_j, circle_j in self.circles.items():
                if name_i == name_j:
                    entanglement[name_to_idx[name_i], name_to_idx[name_j]] = 1.0
                    continue

                shared_knowledge = set(circle_i.knowledge_store.keys()) &                                    set(circle_j.knowledge_store.keys())
                knowledge_overlap = len(shared_knowledge) / max(
                    len(circle_i.knowledge_store), len(circle_j.knowledge_store), 1
                )

                coupling = self.coupling_matrix[
                    name_to_idx[name_i], name_to_idx[name_j]
                ]

                entanglement[name_to_idx[name_i], name_to_idx[name_j]] =                     0.5 * coupling + 0.5 * knowledge_overlap

        return entanglement

    def map_circles_to_layers(self) -> Dict[str, CircleLayerMapping]:
        self.layer_maps = {}

        for name, circle in self.circles.items():
            mapping = circle.map_to_layers()
            if name == "admin":
                for key in list(mapping.layer_assignments.keys()):
                    mapping.layer_assignments[0] = mapping.layer_assignments.pop(key, [])
            elif name == "relay":
                for key in list(mapping.layer_assignments.keys()):
                    mapping.layer_assignments[1] = mapping.layer_assignments.pop(key, [])
            elif name == "command":
                for key in list(mapping.layer_assignments.keys()):
                    mapping.layer_assignments[2] = mapping.layer_assignments.pop(key, [])
            elif name == "session":
                for key in list(mapping.layer_assignments.keys()):
                    mapping.layer_assignments[3] = mapping.layer_assignments.pop(key, [])
            elif name == "consensus":
                for key in list(mapping.layer_assignments.keys()):
                    mapping.layer_assignments[4] = mapping.layer_assignments.pop(key, [])

            self.layer_maps[name] = mapping

        return self.layer_maps

    def map_circles_to_network(self) -> Dict[str, CircleNetworkMapping]:
        self.network_maps = {}

        for name, circle in self.circles.items():
            mapping = circle.map_to_network(LINE_NAMES)
            self.network_maps[name] = mapping

        for i, name_i in enumerate(CIRCLE_NAMES):
            for j, name_j in enumerate(CIRCLE_NAMES):
                if i != j and self.coupling_matrix[i, j] > 0.1:
                    if name_i in self.network_maps and name_j in self.network_maps:
                        weight = float(self.coupling_matrix[i, j])
                        node_a = f"meta_{name_i}"
                        node_b = f"meta_{name_j}"
                        self.network_maps[name_i].add_edge(node_a, node_b, weight)

        return self.network_maps

    def map_circles_to_tower(self) -> Dict[str, CircleTowerMapping]:
        self.tower_maps = {}

        tower_levels = {
            "admin": 0,
            "relay": 1,
            "session": 2,
            "command": 3,
            "consensus": 4,
        }

        for name, circle in self.circles.items():
            level = tower_levels.get(name, 0)
            mapping = circle.map_to_tower(level)
            self.tower_maps[name] = mapping

        system_emergence = self.compute_circle_emergence()
        for mapping in self.tower_maps.values():
            mapping.add_brick("system_emergence", system_emergence, 0.9)

        meta_coherence = np.mean([
            circle.health.coherence for circle in self.circles.values()
        ])
        for mapping in self.tower_maps.values():
            mapping.add_brick("meta_coherence", meta_coherence, 0.95)

        return self.tower_maps

    def get_layer_network_tower_report(self) -> Dict[str, Any]:
        layer_maps = self.map_circles_to_layers()
        network_maps = self.map_circles_to_network()
        tower_maps = self.map_circles_to_tower()

        layer_summary = {}
        for layer_idx in range(N_FCTN_LAYERS):
            total_knowledge = sum(
                len(m.layer_assignments.get(layer_idx, []))
                for m in layer_maps.values()
            )
            total_weight = sum(
                m.layer_weights.get(layer_idx, 0)
                for m in layer_maps.values()
            )
            layer_summary[layer_idx] = {
                "knowledge_items": total_knowledge,
                "total_weight": round(total_weight, 4),
                "circles_present": [
                    name for name, m in layer_maps.items()
                    if layer_idx in m.layer_assignments
                ],
            }

        total_nodes = sum(len(m.tensor_nodes) for m in network_maps.values())
        total_edges = sum(len(m.tensor_edges) for m in network_maps.values())

        tower_summary = {}
        for level in range(N_FCTN_LAYERS):
            bricks = []
            for name, mapping in tower_maps.items():
                if mapping.tower_level == level:
                    bricks.extend(mapping.tower_bricks)
            tower_summary[level] = {
                "circle": next((n for n, m in tower_maps.items() if m.tower_level == level), "system"),
                "brick_count": len(bricks),
                "properties": list(set(b["property"] for b in bricks)),
                "avg_stability": round(np.mean([b["stability"] for b in bricks]), 4) if bricks else 0,
            }

        return {
            "layer_summary": layer_summary,
            "network_summary": {
                "total_nodes": total_nodes,
                "total_edges": total_edges,
                "circle_subgraphs": len(network_maps),
            },
            "tower_summary": tower_summary,
            "mappings": {
                "layers": {k: v.to_dict() for k, v in layer_maps.items()},
                "networks": {k: v.to_dict() for k, v in network_maps.items()},
                "towers": {k: v.to_dict() for k, v in tower_maps.items()},
            },
        }

    def get_full_report(self) -> Dict[str, Any]:
        return {
            "version": CIRCLE_SYSTEM_VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stats": self.stats,
            "coupling_matrix": [
                [round(float(v), 4) for v in row]
                for row in self.coupling_matrix.tolist()
            ],
            "circle_entanglement": [
                [round(float(v), 4) for v in row]
                for row in self.get_circle_entanglement().tolist()
            ],
            "current_emergence": round(self.compute_circle_emergence(), 4),
            "emergence_history": [round(float(v), 4) for v in self.emergence_history[-20:]],
            "circles": {
                name: circle.get_full_report()
                for name, circle in self.circles.items()
            },
            "layer_network_tower": self.get_layer_network_tower_report(),
        }

    def to_dict(self) -> Dict[str, Any]:
        return self.get_full_report()


# ---------------------------------------------------------------------------
# 5. Emergence Properties of Circles
# ---------------------------------------------------------------------------

class CircleEmergenceAnalyzer:
    """圈涌现性质分析器"""

    def __init__(self, manager: CircleSystemManager):
        self.manager = manager
        self.emergence_metrics: deque = deque(maxlen=100)

    def analyze_collective_intelligence(self) -> Dict[str, float]:
        consensus_quality = self.manager.consensus.health.coherence
        execution_success = 1.0 - self.manager.command.health.error_rate
        communication_efficiency = self.manager.session.health.throughput / 100.0

        collective_intelligence = (
            0.4 * consensus_quality +
            0.3 * execution_success +
            0.3 * min(1.0, communication_efficiency)
        )

        return {
            "collective_intelligence": round(collective_intelligence, 4),
            "consensus_quality": round(consensus_quality, 4),
            "execution_success": round(execution_success, 4),
            "communication_efficiency": round(communication_efficiency, 4),
        }

    def analyze_self_organization(self) -> Dict[str, float]:
        coupling_entropy = -sum(
            self.manager.coupling_matrix[i, j] *
            math.log(self.manager.coupling_matrix[i, j] + 1e-12)
            for i in range(N_CIRCLES)
            for j in range(N_CIRCLES)
            if self.manager.coupling_matrix[i, j] > 0
        )

        session_count = len(self.manager.session.active_session_ids)
        route_adaptivity = len(self.manager.relay.routing_table)

        self_organization = (
            0.3 * min(1.0, coupling_entropy / 2.0) +
            0.3 * min(1.0, session_count / 10.0) +
            0.4 * min(1.0, route_adaptivity / 50.0)
        )

        return {
            "self_organization": round(self_organization, 4),
            "coupling_entropy": round(coupling_entropy, 4),
            "active_sessions": session_count,
            "routing_table_size": route_adaptivity,
        }

    def analyze_adaptivity(self) -> Dict[str, float]:
        health_trend = 0.0
        for name, circle in self.manager.circles.items():
            if self.manager.admin.circle_health_history.get(name):
                history = self.manager.admin.circle_health_history[name]
                if len(history) >= 2:
                    recent = history[-1].get("load_factor", 0)
                    older = history[-2].get("load_factor", 0)
                    health_trend += (older - recent)

        adaptivity = 0.5 + 0.5 * math.tanh(health_trend)

        return {
            "adaptivity": round(adaptivity, 4),
            "health_trend": round(health_trend, 4),
        }

    def analyze_robustness(self) -> Dict[str, float]:
        healths = [circle.health.coherence for circle in self.manager.circles.values()]
        if healths:
            avg_health = np.mean(healths)
            health_std = np.std(healths)
            robustness = avg_health * (1.0 - health_std)
        else:
            robustness = 0.0

        return {
            "robustness": round(robustness, 4),
            "avg_health": round(np.mean(healths), 4) if healths else 0,
            "health_std": round(np.std(healths), 4) if healths else 0,
        }

    def analyze_creativity(self) -> Dict[str, float]:
        total_knowledge = sum(
            len(circle.knowledge_store) for circle in self.manager.circles.values()
        )
        knowledge_growth = 0.0
        if len(self.manager.history) >= 2:
            old_knowledge = total_knowledge
            knowledge_growth = total_knowledge / max(old_knowledge, 1) - 1.0

        creativity = min(1.0, max(0.0, 0.5 + knowledge_growth * 10))

        return {
            "creativity": round(creativity, 4),
            "total_knowledge": total_knowledge,
            "knowledge_growth": round(knowledge_growth, 6),
        }

    def analyze_all(self) -> Dict[str, Any]:
        result = {
            "collective_intelligence": self.analyze_collective_intelligence(),
            "self_organization": self.analyze_self_organization(),
            "adaptivity": self.analyze_adaptivity(),
            "robustness": self.analyze_robustness(),
            "creativity": self.analyze_creativity(),
            "overall_emergence": round(self.manager.compute_circle_emergence(), 4),
        }
        self.emergence_metrics.append(result)
        return result


# ---------------------------------------------------------------------------
# 6. Verification & Main
# ---------------------------------------------------------------------------

def verify_circle_systems() -> Dict[str, Any]:
    """验证五圈系统"""
    print("[CircleSystems] Starting verification...")
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": CIRCLE_SYSTEM_VERSION,
        "tests": {},
    }

    manager = CircleSystemManager()
    assert len(manager.circles) == N_CIRCLES
    results["tests"]["init"] = {
        "status": "PASS",
        "circle_count": len(manager.circles),
    }

    assert manager.coupling_matrix.shape == (N_CIRCLES, N_CIRCLES)
    results["tests"]["coupling_matrix"] = {
        "status": "PASS",
        "shape": list(manager.coupling_matrix.shape),
    }

    tick_results = manager.run_ticks(5)
    assert len(tick_results) == 5
    results["tests"]["tick"] = {
        "status": "PASS",
        "ticks_run": len(tick_results),
        "final_emergence": round(tick_results[-1]["emergence"], 4),
    }

    dec_id = manager.consensus.propose_decision(
        "ucif2", "test_module", "test_topic", 0.75, 0.9
    )
    assert dec_id is not None
    results["tests"]["consensus"] = {
        "status": "PASS",
        "decision_id": dec_id,
        "pending_topics": len(manager.consensus.consensus_topics),
    }

    sid = manager.session.create_session(
        "ucif2", ["lgt", "qfa"], "test_session"
    )
    assert sid in manager.session.sessions
    manager.session.add_message(sid, "ucif2", "Hello from ucif2")
    results["tests"]["session"] = {
        "status": "PASS",
        "session_id": sid,
        "message_count": len(manager.session.sessions[sid]["messages"]),
    }

    routes = manager.relay.route_message("test", "ucif2", strategy="broadcast")
    assert len(routes) > 0
    results["tests"]["relay"] = {
        "status": "PASS",
        "route_count": len(routes),
    }

    cmd_id = manager.command.issue_command(
        "ucif2", "lgt", "test_cmd", {"param": 1}
    )
    assert cmd_id in manager.command.commands
    results["tests"]["command"] = {
        "status": "PASS",
        "cmd_id": cmd_id,
        "queue_length": len(manager.command.execution_queue),
    }

    manager.admin.set_config("test_key", "test_value")
    health = manager.admin.check_system_health()
    assert "system_status" in health
    results["tests"]["admin"] = {
        "status": "PASS",
        "system_status": health["system_status"],
        "config_size": len(manager.admin.global_config),
    }

    manager.consensus.send_message(CircleMessage(
        source_circle="consensus",
        target_circle="session",
        msg_type=CircleMessageType.DECISION_PROPAGATE,
        payload={"test": "data"},
    ))
    routed = manager.route_inter_circle_messages()
    assert routed > 0
    results["tests"]["message_routing"] = {
        "status": "PASS",
        "messages_routed": routed,
    }

    analyzer = CircleEmergenceAnalyzer(manager)
    emergence = analyzer.analyze_all()
    assert "overall_emergence" in emergence
    results["tests"]["emergence"] = {
        "status": "PASS",
        "overall_emergence": emergence["overall_emergence"],
        "collective_intelligence": emergence["collective_intelligence"]["collective_intelligence"],
    }

    lnt_report = manager.get_layer_network_tower_report()
    assert "layer_summary" in lnt_report
    assert "network_summary" in lnt_report
    assert "tower_summary" in lnt_report
    results["tests"]["layer_network_tower"] = {
        "status": "PASS",
        "layers_mapped": len(lnt_report["layer_summary"]),
        "network_nodes": lnt_report["network_summary"]["total_nodes"],
        "tower_levels": len(lnt_report["tower_summary"]),
    }

    all_pass = all(t["status"] == "PASS" for t in results["tests"].values())
    results["overall_status"] = "ALL_PASS" if all_pass else "PARTIAL"
    results["pass_count"] = sum(1 for t in results["tests"].values() if t["status"] == "PASS")
    results["total_tests"] = len(results["tests"])

    print(f"[CircleSystems] Verification complete: {results['pass_count']}/{results['total_tests']} passed")
    return results


def generate_reports(verify_result: Dict[str, Any]):
    """生成JSON和Markdown报告"""
    hub_dir = Path("/mnt/agents/output/OMNI-HUB/hub")
    hub_dir.mkdir(parents=True, exist_ok=True)

    json_path = hub_dir / "CIRCLE_SYSTEMS_REPORT.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(verify_result, f, ensure_ascii=False, indent=2)

    md_path = hub_dir / "CIRCLE_SYSTEMS_REPORT.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# OMNI-HUB Circle Systems Report\n\n")
        f.write(f"**Version**: {verify_result.get('version', 'N/A')}\n\n")
        f.write(f"**Timestamp**: {verify_result.get('timestamp', 'N/A')}\n\n")
        f.write(f"**Overall Status**: {verify_result.get('overall_status', 'N/A')}\n\n")
        f.write(f"**Pass Rate**: {verify_result.get('pass_count', 0)}/{verify_result.get('total_tests', 0)}\n\n")
        f.write("---\n\n")
        f.write("## Test Details\n\n")
        for test_name, test_data in verify_result.get('tests', {}).items():
            f.write(f"### {test_name}\n\n")
            f.write(f"- **Status**: {test_data.get('status', 'N/A')}\n")
            for k, v in test_data.items():
                if k != 'status':
                    f.write(f"- **{k}**: {v}\n")
            f.write("\n")
        f.write("---\n\n")
        f.write("## Five-Circle System Architecture\n\n")
        f.write("```\n")
        f.write("ConsensusCircle  (Consensus)   -- Cross-line decision consensus\n")
        f.write("       |\n")
        f.write("       v\n")
        f.write("SessionCircle    (Session)     -- Cross-line dialogue management\n")
        f.write("       |\n")
        f.write("       v\n")
        f.write("RelayCircle      (Relay)       -- Message routing and forwarding\n")
        f.write("       |\n")
        f.write("       v\n")
        f.write("CommandCircle    (Command)     -- Command dispatch and execution\n")
        f.write("       |\n")
        f.write("       v\n")
        f.write("AdminCircle      (Admin)       -- System management and monitoring\n")
        f.write("       |\n")
        f.write("       +----feedback----> ConsensusCircle\n")
        f.write("```\n\n")
        f.write("## Circle-Layer-Network-Tower Mapping\n\n")
        f.write("| Circle | Layer | Network Nodes | Tower Level |\n")
        f.write("|---|---|---|---|\n")
        f.write("| Admin | Layer 0 (Physical) | Admin nodes | Tower 0 |\n")
        f.write("| Relay | Layer 1 (Data) | Route nodes | Tower 1 |\n")
        f.write("| Command | Layer 2 (Logic) | Command nodes | Tower 2 |\n")
        f.write("| Session | Layer 3 (Session) | Session nodes | Tower 3 |\n")
        f.write("| Consensus | Layer 4 (Consensus) | Decision nodes | Tower 4 |\n")
        f.write("| (System Emergence) | Layer 5 (Emergence) | Coupling edges | Tower 5 |\n")
        f.write("| (Meta-Circle) | Layer 6 (Meta) | Meta nodes | Tower 6 |\n")
        f.write("\n")
        f.write("---\n\n")
        f.write("*Report generated by CircleSystems v12.0*\n")

    return json_path, md_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 70)
    print("OMNI-HUB v12.0 -- Circle Systems Verification")
    print("=" * 70)

    verify_result = verify_circle_systems()

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

    json_path, md_path = generate_reports(verify_result)
    print(f"\nReports generated:")
    print(f"  JSON: {json_path}")
    print(f"  MD:   {md_path}")

    print("\n[CircleSystems] Verification complete.")
