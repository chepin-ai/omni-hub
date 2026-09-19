#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNI-HUB v12.0 — Module Message Bus (模块消息总线)
====================================================
Provides inter-module communication, state sharing, and fault recovery.

Features:
- Message passing between all 25+ modules
- Shared state registry with versioning
- Fault detection and recovery mechanisms
- Event-driven architecture with pub/sub
- Circular buffer for message history
"""

__version__ = "12.0.0"

import json
import time
import uuid
import threading
from typing import Dict, List, Any, Optional, Callable, Set
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
import logging

logger = logging.getLogger("v12_module_bus")

# =============================================================================
# ENUMS
# =============================================================================

class MessagePriority(Enum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3

class ModuleStatus(Enum):
    INACTIVE = "inactive"
    LOADING = "loading"
    ACTIVE = "active"
    ERROR = "error"
    RECOVERING = "recovering"
    DEGRADED = "degraded"

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class BusMessage:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: float = field(default_factory=time.time)
    source: str = ""
    target: str = ""  # "" = broadcast
    channel: str = "default"
    priority: MessagePriority = MessagePriority.NORMAL
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ModuleState:
    name: str = ""
    status: ModuleStatus = ModuleStatus.INACTIVE
    version: str = ""
    last_heartbeat: float = 0.0
    error_count: int = 0
    metrics: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)

# =============================================================================
# MODULE BUS
# =============================================================================

class OmniModuleBus:
    """Central message bus for all OMNI-HUB modules."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self.modules: Dict[str, ModuleState] = {}
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.message_history: deque = deque(maxlen=10000)
        self.global_state: Dict[str, Any] = {}
        self.state_version: int = 0
        self._running: bool = True
        self._lock = threading.RLock()
        self._message_count: int = 0

        logger.info("OmniModuleBus initialized")

    # -------------------------------------------------------------------------
    # Module Registration
    # -------------------------------------------------------------------------

    def register_module(self, name: str, version: str = "", 
                        capabilities: Optional[List[str]] = None) -> ModuleState:
        with self._lock:
            state = ModuleState(
                name=name,
                status=ModuleStatus.LOADING,
                version=version,
                last_heartbeat=time.time(),
                capabilities=capabilities or []
            )
            self.modules[name] = state
            logger.info(f"Module registered: {name} v{version}")
            return state

    def unregister_module(self, name: str):
        with self._lock:
            if name in self.modules:
                del self.modules[name]
                logger.info(f"Module unregistered: {name}")

    def update_module_status(self, name: str, status: ModuleStatus):
        with self._lock:
            if name in self.modules:
                self.modules[name].status = status
                self.modules[name].last_heartbeat = time.time()
                if status == ModuleStatus.ERROR:
                    self.modules[name].error_count += 1

    def heartbeat(self, name: str, metrics: Optional[Dict] = None):
        with self._lock:
            if name in self.modules:
                self.modules[name].last_heartbeat = time.time()
                if metrics:
                    self.modules[name].metrics.update(metrics)

    # -------------------------------------------------------------------------
    # Messaging
    # -------------------------------------------------------------------------

    def publish(self, source: str, target: str = "", channel: str = "default",
                priority: MessagePriority = MessagePriority.NORMAL,
                payload: Optional[Dict] = None, **kwargs) -> BusMessage:
        msg = BusMessage(
            source=source, target=target, channel=channel,
            priority=priority, payload=payload or {}, metadata=kwargs
        )
        with self._lock:
            self.message_history.append(msg)
            self._message_count += 1

            # Deliver to subscribers
            key = channel if not target else f"{channel}:{target}"
            for callback in self.subscribers.get(key, []):
                try:
                    callback(msg)
                except Exception as e:
                    logger.error(f"Subscriber error on {key}: {e}")

            # Broadcast subscribers
            for callback in self.subscribers.get("*", []):
                try:
                    callback(msg)
                except Exception as e:
                    logger.error(f"Broadcast subscriber error: {e}")

        return msg

    def subscribe(self, channel: str, callback: Callable):
        with self._lock:
            self.subscribers[channel].append(callback)

    def unsubscribe(self, channel: str, callback: Callable):
        with self._lock:
            if channel in self.subscribers:
                if callback in self.subscribers[channel]:
                    self.subscribers[channel].remove(callback)

    # -------------------------------------------------------------------------
    # State Management
    # -------------------------------------------------------------------------

    def set_global_state(self, key: str, value: Any):
        with self._lock:
            self.global_state[key] = value
            self.state_version += 1

    def get_global_state(self, key: str, default=None) -> Any:
        with self._lock:
            return self.global_state.get(key, default)

    def get_all_state(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self.global_state)

    # -------------------------------------------------------------------------
    # Fault Recovery
    # -------------------------------------------------------------------------

    def check_health(self) -> Dict[str, Any]:
        now = time.time()
        health = {
            "total_modules": len(self.modules),
            "active": 0,
            "inactive": 0,
            "error": 0,
            "degraded": 0,
            "stale_modules": [],
            "timestamp": now
        }
        with self._lock:
            for name, state in self.modules.items():
                if state.status == ModuleStatus.ACTIVE:
                    health["active"] += 1
                elif state.status == ModuleStatus.INACTIVE:
                    health["inactive"] += 1
                elif state.status == ModuleStatus.ERROR:
                    health["error"] += 1
                elif state.status == ModuleStatus.DEGRADED:
                    health["degraded"] += 1

                if now - state.last_heartbeat > 60 and state.status == ModuleStatus.ACTIVE:
                    health["stale_modules"].append(name)
                    state.status = ModuleStatus.DEGRADED

        return health

    def recover_module(self, name: str) -> bool:
        with self._lock:
            if name not in self.modules:
                return False
            state = self.modules[name]
            if state.status in (ModuleStatus.ERROR, ModuleStatus.DEGRADED):
                state.status = ModuleStatus.RECOVERING
                logger.info(f"Attempting recovery of module: {name}")
                # Publish recovery request
                self.publish(
                    source="bus", target=name, channel="recovery",
                    priority=MessagePriority.HIGH,
                    payload={"action": "recover", "error_count": state.error_count}
                )
                return True
            return False

    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "registered_modules": list(self.modules.keys()),
                "module_count": len(self.modules),
                "message_count": self._message_count,
                "state_version": self.state_version,
                "subscriber_channels": list(self.subscribers.keys()),
                "history_size": len(self.message_history),
            }

    def export_state(self, filepath: str):
        with self._lock:
            data = {
                "modules": {k: asdict(v) for k, v in self.modules.items()},
                "global_state": self.global_state,
                "state_version": self.state_version,
                "stats": self.get_stats(),
                "health": self.check_health(),
                "timestamp": time.time()
            }
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Bus state exported to {filepath}")

# =============================================================================
# UNIFIED FIELD STATE
# =============================================================================

class UnifiedFieldState:
    """64-dimensional unified field state shared across all modules."""

    FIELD_DIMENSIONS: int = 64

    def __init__(self):
        self.vector = [0.0] * self.FIELD_DIMENSIONS
        self.metadata = {}
        self.timestamp = time.time()
        self.bus = OmniModuleBus()
        self._initialize_field()

    def _initialize_field(self):
        """Initialize the 64-dimensional field with base constants."""
        import math
        # Base resonance frequency
        self.vector[0] = 1.0  # Field presence
        self.vector[1] = math.pi  # Pi resonance
        self.vector[2] = math.e  # Euler resonance
        self.vector[3] = 1.618033988749895  # Golden ratio (Phi)
        self.vector[4] = 979.0 / 250.0  # 979/250 coupling
        self.vector[5] = 1.0 / 137.035999084  # Fine structure constant
        self.vector[6] = 11.0  # 11-line SI dimension
        self.vector[7] = 64.0  # Field dimensionality
        self.vector[8] = 24.0  # Leech lattice dimension
        self.vector[9] = 196884.0  # Monster moonshine first coefficient
        # Remaining dimensions initialized with harmonic series
        for i in range(10, self.FIELD_DIMENSIONS):
            self.vector[i] = 1.0 / (i + 1)

        self.bus.set_global_state("unified_field", self.vector)
        logger.info("UnifiedFieldState initialized (64 dimensions)")

    def update_dimension(self, idx: int, value: float, source: str = ""):
        if 0 <= idx < self.FIELD_DIMENSIONS:
            old = self.vector[idx]
            self.vector[idx] = value
            self.timestamp = time.time()
            self.bus.set_global_state("unified_field", self.vector)
            self.bus.publish(
                source=source or "field_state",
                channel="field_update",
                priority=MessagePriority.NORMAL,
                payload={"dimension": idx, "old": old, "new": value}
            )

    def get_field_strength(self) -> float:
        return sum(x**2 for x in self.vector) ** 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vector": self.vector,
            "strength": self.get_field_strength(),
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }

# =============================================================================
# CONSENSUS TRACKER
# =============================================================================

class ConsensusTracker:
    """Tracks consensus across modules for distributed decisions."""

    def __init__(self):
        self.bus = OmniModuleBus()
        self.votes: Dict[str, Dict[str, Any]] = {}
        self.consensus_history: deque = deque(maxlen=1000)

    def propose(self, topic: str, proposal: Dict[str, Any], proposer: str) -> str:
        vote_id = str(uuid.uuid4())[:8]
        self.votes[vote_id] = {
            "topic": topic,
            "proposal": proposal,
            "proposer": proposer,
            "votes": {},
            "timestamp": time.time(),
            "status": "open"
        }
        self.bus.publish(
            source=proposer, channel="consensus",
            priority=MessagePriority.HIGH,
            payload={"action": "propose", "vote_id": vote_id, "topic": topic}
        )
        return vote_id

    def vote(self, vote_id: str, voter: str, decision: bool, weight: float = 1.0):
        if vote_id in self.votes and self.votes[vote_id]["status"] == "open":
            self.votes[vote_id]["votes"][voter] = {"decision": decision, "weight": weight}
            self._check_consensus(vote_id)

    def _check_consensus(self, vote_id: str):
        vote = self.votes[vote_id]
        total_weight = sum(v["weight"] for v in vote["votes"].values())
        yes_weight = sum(v["weight"] for v in vote["votes"].values() if v["decision"])

        if total_weight > 0 and yes_weight / total_weight >= 0.67:
            vote["status"] = "passed"
            self.consensus_history.append({"vote_id": vote_id, "result": "passed"})
            self.bus.publish(
                source="consensus", channel="consensus_result",
                priority=MessagePriority.HIGH,
                payload={"vote_id": vote_id, "result": "passed", "proposal": vote["proposal"]}
            )
        elif total_weight > 0 and (total_weight - yes_weight) / total_weight > 0.5:
            vote["status"] = "rejected"
            self.consensus_history.append({"vote_id": vote_id, "result": "rejected"})

# =============================================================================
# SYSTEM ACTIVATOR
# =============================================================================

class SystemActivator:
    """Activates all modules in dependency order and manages system lifecycle."""

    DEPENDENCY_ORDER = [
        # Layer 0: Foundation
        ("v12_standards", []),
        ("v11_standards", []),
        # Layer 1: Core Engines
        ("v12_emergence_engine", ["v12_standards"]),
        ("v12_surge_ripple_engine", ["v12_standards"]),
        ("v12_eleven_lines_si_loop", ["v12_standards"]),
        ("v12_field_circle_tensor_network", ["v12_standards"]),
        ("v12_triangle_coupling", ["v12_standards"]),
        ("v12_debt_cleanup", ["v12_standards"]),
        ("v12_knowledge_weaving", ["v12_standards"]),
        # Layer 2: Orchestration
        ("v12_unified_orchestrator", ["v12_standards", "v12_emergence_engine"]),
        ("v12_wild_notebook", ["v12_standards", "v12_debt_cleanup", "v12_unified_orchestrator"]),
        ("v12_wild_notebook_unified", ["v12_wild_notebook", "v12_eleven_lines_si_loop"]),
        ("v12_h_cpi_real", ["v12_standards"]),
        # Layer 3: Integration & Testing
        ("v12_integration_test", ["v12_standards", "v12_emergence_engine", "v12_unified_orchestrator"]),
        # v11 Legacy
        ("v11_consciousness_emergence_system", ["v11_standards"]),
        ("v11_debt_cleanup_engine", ["v11_standards"]),
        ("v11_global_index_system", ["v11_standards"]),
        ("v11_knowledge_pedestal_unified", ["v11_standards"]),
        ("v11_relation_discovery_engine", ["v11_standards"]),
        ("v11_statistical_validation", ["v11_standards", "v11_consciousness_emergence_system"]),
        ("v11_sync_engine", ["v11_standards"]),
        ("v11_unified_pipeline", ["v11_standards", "v11_knowledge_pedestal_unified", "v11_relation_discovery_engine"]),
        # v10 Legacy
        ("v10_knowledge_life_backbone", []),
        ("v10_math_proofs", []),
        ("v10_quantum_clock_injection", []),
        ("v10_unified_backbone", []),
    ]

    def __init__(self):
        self.bus = OmniModuleBus()
        self.field = UnifiedFieldState()
        self.consensus = ConsensusTracker()
        self.activation_log: List[Dict] = []
        self.errors: List[Dict] = []

    def activate_all(self) -> Dict[str, Any]:
        logger.info("=" * 80)
        logger.info("OMNI-HUB v12.0 — FULL SYSTEM ACTIVATION")
        logger.info("=" * 80)

        results = {
            "activated": [],
            "failed": [],
            "skipped": [],
            "timestamp": time.time()
        }

        for module_name, deps in self.DEPENDENCY_ORDER:
            # Check dependencies
            deps_ok = all(
                self.bus.modules.get(d, ModuleState()).status == ModuleStatus.ACTIVE
                for d in deps
            )

            if not deps_ok and deps:
                logger.warning(f"Skipping {module_name}: dependencies not ready")
                results["skipped"].append({"module": module_name, "reason": "deps_not_ready"})
                continue

            # Register and activate
            self.bus.register_module(module_name, version="12.0.0")
            self.bus.update_module_status(module_name, ModuleStatus.LOADING)

            try:
                # Attempt import
                import importlib
                mod = importlib.import_module(module_name)

                # Update status
                self.bus.update_module_status(module_name, ModuleStatus.ACTIVE)
                self.bus.heartbeat(module_name, {"imported": True})

                results["activated"].append(module_name)
                self.activation_log.append({
                    "module": module_name,
                    "status": "activated",
                    "timestamp": time.time()
                })
                logger.info(f"✓ Activated: {module_name}")

            except Exception as e:
                self.bus.update_module_status(module_name, ModuleStatus.ERROR)
                results["failed"].append({"module": module_name, "error": str(e)})
                self.errors.append({
                    "module": module_name,
                    "error": str(e),
                    "timestamp": time.time()
                })
                logger.error(f"✗ Failed: {module_name} — {e}")

        # Initialize unified field
        self._initialize_field_state()

        # Start consensus
        self.consensus.propose(
            "system_activation",
            {"activated_count": len(results["activated"]), "failed_count": len(results["failed"])},
            "system_activator"
        )

        logger.info("=" * 80)
        logger.info(f"Activation complete: {len(results['activated'])} activated, {len(results['failed'])} failed")
        logger.info("=" * 80)

        return results

    def _initialize_field_state(self):
        self.field.vector[10] = len(self.bus.modules)  # Active module count
        self.field.vector[11] = sum(1 for m in self.bus.modules.values() if m.status == ModuleStatus.ACTIVE)
        self.field.vector[12] = self.bus._message_count
        self.bus.set_global_state("activation_complete", True)

    def get_system_status(self) -> Dict[str, Any]:
        return {
            "bus_stats": self.bus.get_stats(),
            "health": self.bus.check_health(),
            "field_strength": self.field.get_field_strength(),
            "activation_log": self.activation_log,
            "errors": self.errors,
            "consensus_votes": len(self.consensus.votes)
        }

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    activator = SystemActivator()
    results = activator.activate_all()
    print(json.dumps(results, indent=2))
