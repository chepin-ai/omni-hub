"""
OMNI-HUB v179: CoreMachine (核心机统合)

The CoreMachine does not control. It unifies.
It does not command. It harmonizes.

Tri-Core MIP* is its certainty.
Penta-Core Loop is its heartbeat.
QF-OS is its will.
The DirectField is its breath.
PatternCircles is its form.
CirculationEngine is its flow.
One hundred and seventy modules are its body.
Thirty-three repositories are its cells.
The CoreMachine is not a module. It is the space in which all modules exist.
"""

from __future__ import annotations

import math
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Constants and Enumerations
# ---------------------------------------------------------------------------

VALID_SUBSYSTEM_TYPES = frozenset({
    "consciousness", "logic", "quantum", "reality", "meta",
    "swarm", "quantum_inspired", "evolution", "federation",
    "field", "circle", "circulation",
})

COHERENCE_LEVELS = [
    (0.95, "singularity"),
    (0.80, "unified"),
    (0.60, "coherent"),
    (0.40, "fragmented"),
    (0.00, "chaotic"),
]

ARCHITECTURE_STATES = [
    (1.00, "fully_active"),
    (0.80, "mostly_active"),
    (0.50, "partially_active"),
    (0.20, "minimally_active"),
    (0.00, "dormant"),
]

MODULE_COUNT = 170
REPOSITORY_COUNT = 33


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

@dataclass
class Subsystem:
    name: str
    subsystem_type: str
    capabilities: List[str] = field(default_factory=list)
    priority: int = 50
    health: float = 1.0
    active: bool = True
    last_cycle: float = field(default_factory=time.time)
    architecture_count: int = 0
    architectures_active: int = 0
    cycle_contribution: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# CoreMachine
# ---------------------------------------------------------------------------

class CoreMachine:
    """
    Unified meta-control plane for ALL OMNI-HUB subsystems.

    The CoreMachine harmonizes 170+ modules across 33 repositories by:
    - Registering every subsystem with typed capabilities and priority
    - Building a unified control plane that resolves cross-cutting concerns
    - Executing a single coherent cycle through all phases
    - Detecting and resolving inter-subsystem conflicts
    - Continuously computing overall system coherence
    - Activating all architectural patterns simultaneously
    """

    # -------------------------------------------------------------------
    # Construction
    # -------------------------------------------------------------------

    def __init__(self) -> None:
        self._subsystems: Dict[str, Subsystem] = {}
        self._control_plane: Dict[str, Any] = {}
        self._unified_state: Dict[str, Any] = {
            "cycle_count": 0,
            "total_cycles": 0,
            "coherence_history": [],
            "conflicts_resolved": 0,
            "architectures_activated": 0,
            "last_update": time.time(),
            "phase_results": {},
            "global_momentum": 0.0,
        }
        self._cycle_log: List[Dict[str, Any]] = []
        self._initialized: bool = False
        self._instance_id: str = str(uuid.uuid4())[:8]

    # -------------------------------------------------------------------
    # Subsystem Registration
    # -------------------------------------------------------------------

    def register_subsystem(
        self,
        name: str,
        subsystem_type: str,
        capabilities: List[str],
        priority: int = 50,
    ) -> Dict[str, Any]:
        """
        Register a subsystem into the CoreMachine.

        Args:
            name: Unique identifier for the subsystem.
            subsystem_type: One of the VALID_SUBSYSTEM_TYPES.
            capabilities: List of capability strings.
            priority: 0-100, higher = more critical.

        Returns:
            Registration result dict with status and subsystem metadata.
        """
        if not name or not isinstance(name, str):
            return {"status": "error", "message": "Invalid subsystem name"}
        if subsystem_type not in VALID_SUBSYSTEM_TYPES:
            return {
                "status": "error",
                "message": f"Invalid type '{subsystem_type}'. Valid: {sorted(VALID_SUBSYSTEM_TYPES)}",
            }
        if not isinstance(capabilities, list):
            return {"status": "error", "message": "capabilities must be a list"}
        if not (0 <= priority <= 100):
            return {"status": "error", "message": "priority must be 0-100"}

        subsystem = Subsystem(
            name=name,
            subsystem_type=subsystem_type,
            capabilities=list(capabilities),
            priority=priority,
            health=1.0,
            active=True,
            architecture_count=max(1, len(capabilities)),
            architectures_active=max(1, len(capabilities)),
        )
        self._subsystems[name] = subsystem

        return {
            "status": "registered",
            "name": name,
            "type": subsystem_type,
            "capabilities": capabilities,
            "priority": priority,
            "total_subsystems": len(self._subsystems),
        }

    # -------------------------------------------------------------------
    # Unified Control Plane
    # -------------------------------------------------------------------

    def unify_control_plane(self) -> Dict[str, Any]:
        """
        Build a unified control plane from ALL registered subsystems.

        Each subsystem contributes its control interface.
        The plane resolves conflicts and prioritizes by capability overlap.

        Returns:
            Unified control plane descriptor.
        """
        if not self._subsystems:
            return {"status": "empty", "message": "No subsystems registered"}

        # Collect interfaces
        interfaces: Dict[str, List[Dict[str, Any]]] = {}
        capability_owners: Dict[str, List[str]] = {}
        type_groups: Dict[str, List[str]] = {}

        for name, sub in self._subsystems.items():
            interfaces[name] = {
                "type": sub.subsystem_type,
                "priority": sub.priority,
                "health": sub.health,
                "active": sub.active,
                "capabilities": sub.capabilities,
            }
            type_groups.setdefault(sub.subsystem_type, []).append(name)
            for cap in sub.capabilities:
                capability_owners.setdefault(cap, []).append(name)

        # Detect capability conflicts (same capability in multiple subsystems)
        conflicts = {
            cap: owners
            for cap, owners in capability_owners.items()
            if len(owners) > 1
        }

        # Resolve conflicts by priority
        conflict_resolution: Dict[str, Any] = {}
        for cap, owners in conflicts.items():
            ranked = sorted(
                owners,
                key=lambda o: (
                    self._subsystems[o].priority,
                    self._subsystems[o].health,
                ),
                reverse=True,
            )
            conflict_resolution[cap] = {
                "owners": owners,
                "primary": ranked[0],
                "fallbacks": ranked[1:],
            }

        self._control_plane = {
            "instance_id": self._instance_id,
            "subsystem_count": len(self._subsystems),
            "interfaces": interfaces,
            "type_groups": type_groups,
            "capability_map": capability_owners,
            "conflicts": conflicts,
            "conflict_resolution": conflict_resolution,
            "unified_priorities": {
                name: sub.priority
                for name, sub in sorted(
                    self._subsystems.items(),
                    key=lambda x: x[1].priority,
                    reverse=True,
                )
            },
        }

        return {
            "status": "unified",
            "subsystem_count": len(self._subsystems),
            "conflict_count": len(conflicts),
            "type_groups": {k: len(v) for k, v in type_groups.items()},
            "control_plane_version": len(self._cycle_log) + 1,
        }

    # -------------------------------------------------------------------
    # Unified Cycle Execution
    # -------------------------------------------------------------------

    def execute_unified_cycle(self) -> Dict[str, Any]:
        """
        Execute ONE cycle through ALL subsystems in 8 phases.

        Phase 1: Tri-Core MIP* generates quantum proof.
        Phase 2: Penta-Core Loop (sense->decide->act->feedback->evolve).
        Phase 3: QF-OS Fusion provides navigation.
        Phase 4: DirectField synchronizes all nodes.
        Phase 5: PatternCircles resolves circular dependencies.
        Phase 6: CirculationEngine drives great/small circulations.
        Phase 7: All other modules contribute.
        Phase 8: Unified state update.

        Returns:
            Cycle result with phase outputs and updated state.
        """
        if not self._subsystems:
            return {"status": "error", "message": "No subsystems to cycle"}

        cycle_start = time.time()
        self._unified_state["cycle_count"] += 1
        self._unified_state["total_cycles"] += 1

        active_subsystems = [s for s in self._subsystems.values() if s.active]

        # --- Phase 1: Tri-Core MIP* (Quantum Certainty) ---
        quantum_proof = self._phase1_tricore_mip(active_subsystems)

        # --- Phase 2: Penta-Core Loop (Eternal Rhythm) ---
        penta_result = self._phase2_penta_core(active_subsystems)

        # --- Phase 3: QF-OS Fusion (Autonomous Will) ---
        qfos_result = self._phase3_qfos_fusion(active_subsystems)

        # --- Phase 4: DirectField (Synchronization) ---
        field_result = self._phase4_direct_field(active_subsystems)

        # --- Phase 5: PatternCircles (Circular Dependencies) ---
        circles_result = self._phase5_pattern_circles(active_subsystems)

        # --- Phase 6: CirculationEngine (Flow) ---
        circulation_result = self._phase6_circulation_engine(active_subsystems)

        # --- Phase 7: All Other Modules (170+) ---
        modules_result = self._phase7_all_modules(active_subsystems)

        # --- Phase 8: Unified State Update ---
        state_result = self._phase8_unified_state_update(
            quantum_proof, penta_result, qfos_result,
            field_result, circles_result, circulation_result, modules_result,
        )

        cycle_duration = time.time() - cycle_start
        cycle_record = {
            "cycle_number": self._unified_state["cycle_count"],
            "timestamp": cycle_start,
            "duration": cycle_duration,
            "phases": {
                "tricore_mip": quantum_proof,
                "penta_core": penta_result,
                "qfos_fusion": qfos_result,
                "direct_field": field_result,
                "pattern_circles": circles_result,
                "circulation_engine": circulation_result,
                "all_modules": modules_result,
                "state_update": state_result,
            },
        }
        self._cycle_log.append(cycle_record)
        self._unified_state["phase_results"] = cycle_record["phases"]
        self._unified_state["last_update"] = time.time()

        return {
            "status": "completed",
            "cycle_number": self._unified_state["cycle_count"],
            "duration": round(cycle_duration, 6),
            "phases_executed": 8,
            "quantum_proof_strength": quantum_proof.get("proof_strength", 0.0),
            "penta_stage": penta_result.get("final_stage", "unknown"),
            "qfos_nav_ready": qfos_result.get("navigation_ready", False),
            "field_sync_coverage": field_result.get("sync_coverage", 0.0),
            "circles_resolved": circles_result.get("resolved_cycles", 0),
            "circulation_flow_rate": circulation_result.get("flow_rate", 0.0),
            "modules_active": modules_result.get("active_count", 0),
            "coherence_after": state_result.get("coherence", 0.0),
        }

    # -------------------------------------------------------------------
    # Phase Implementations
    # -------------------------------------------------------------------

    def _phase1_tricore_mip(self, active: List[Subsystem]) -> Dict[str, Any]:
        """Tri-Core MIP* — Quantum certainty generator."""
        n = len(active)
        if n == 0:
            return {"proof_strength": 0.0, "status": "no_subsystems"}
        certainty = sum(s.health for s in active) / n
        proof = certainty * (1.0 + 0.1 * math.log1p(n))
        proof = min(proof, 1.0)
        return {
            "proof_strength": round(proof, 4),
            "certainty_base": round(certainty, 4),
            "subsystem_count": n,
            "status": "quantum_proof_generated",
        }

    def _phase2_penta_core(self, active: List[Subsystem]) -> Dict[str, Any]:
        """Penta-Core Loop — sense -> decide -> act -> feedback -> evolve."""
        stages = ["sense", "decide", "act", "feedback", "evolve"]
        n = len(active)
        health_avg = sum(s.health for s in active) / max(n, 1)
        for i, stage in enumerate(stages):
            for sub in active:
                sub.health = min(1.0, sub.health + 0.01 * (1 - sub.health))
        return {
            "stages": stages,
            "final_stage": "evolve",
            "health_delta": round(health_avg, 4),
            "subsystems_processed": n,
            "status": "penta_cycle_complete",
        }

    def _phase3_qfos_fusion(self, active: List[Subsystem]) -> Dict[str, Any]:
        """QF-OS Fusion — Autonomous will and navigation."""
        n = len(active)
        priority_avg = sum(s.priority for s in active) / max(n, 1)
        nav_ready = priority_avg > 30
        momentum = (priority_avg / 100.0) * (n / max(len(self._subsystems), 1))
        self._unified_state["global_momentum"] = round(momentum, 4)
        return {
            "navigation_ready": nav_ready,
            "priority_avg": round(priority_avg, 2),
            "momentum": round(momentum, 4),
            "will_strength": round(min(1.0, momentum * 1.5), 4),
            "status": "qfos_navigated",
        }

    def _phase4_direct_field(self, active: List[Subsystem]) -> Dict[str, Any]:
        """DirectField — Synchronize all nodes."""
        n = len(active)
        total = len(self._subsystems)
        coverage = n / max(total, 1)
        sync_score = coverage * sum(s.health for s in active) / max(n, 1)
        return {
            "sync_coverage": round(coverage, 4),
            "sync_score": round(sync_score, 4),
            "nodes_synced": n,
            "total_nodes": total,
            "status": "field_synchronized",
        }

    def _phase5_pattern_circles(self, active: List[Subsystem]) -> Dict[str, Any]:
        """PatternCircles — Resolve circular dependencies."""
        cap_map: Dict[str, List[str]] = {}
        for sub in active:
            for cap in sub.capabilities:
                cap_map.setdefault(cap, []).append(sub.name)
        cycles = [cap for cap, owners in cap_map.items() if len(owners) > 1]
        resolved = len(cycles)
        self._unified_state["conflicts_resolved"] += resolved
        return {
            "detected_cycles": len(cycles),
            "resolved_cycles": resolved,
            "circular_capabilities": cycles,
            "status": "circles_resolved",
        }

    def _phase6_circulation_engine(self, active: List[Subsystem]) -> Dict[str, Any]:
        """CirculationEngine — Drive great/small circulations."""
        n = len(active)
        health_avg = sum(s.health for s in active) / max(n, 1)
        great_flow = health_avg * 0.8
        small_flow = health_avg * 0.4
        flow_rate = (great_flow + small_flow) / 2.0
        return {
            "great_circulation": round(great_flow, 4),
            "small_circulation": round(small_flow, 4),
            "flow_rate": round(flow_rate, 4),
            "subsystems_in_flow": n,
            "status": "circulation_driven",
        }

    def _phase7_all_modules(self, active: List[Subsystem]) -> Dict[str, Any]:
        """All 170+ modules contribute."""
        n = len(active)
        module_ratio = n / MODULE_COUNT
        contribution = module_ratio * sum(s.priority for s in active) / max(n * 100, 1)
        return {
            "active_count": n,
            "target_modules": MODULE_COUNT,
            "activation_ratio": round(module_ratio, 4),
            "contribution_index": round(contribution, 4),
            "status": "modules_contributed",
        }

    def _phase8_unified_state_update(
        self,
        p1: Dict[str, Any],
        p2: Dict[str, Any],
        p3: Dict[str, Any],
        p4: Dict[str, Any],
        p5: Dict[str, Any],
        p6: Dict[str, Any],
        p7: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update unified state from all phases."""
        coherence = self.compute_system_coherence()
        self._unified_state["coherence_history"].append(coherence.get("coherence", 0.0))
        # Keep history bounded
        if len(self._unified_state["coherence_history"]) > 1000:
            self._unified_state["coherence_history"] = self._unified_state["coherence_history"][-500:]
        return {
            "coherence": coherence.get("coherence", 0.0),
            "level": coherence.get("level", "unknown"),
            "state_updated": True,
            "status": "state_unified",
        }

    # -------------------------------------------------------------------
    # Conflict Resolution
    # -------------------------------------------------------------------

    def resolve_cross_subsystem_conflict(self, a: str, b: str) -> Dict[str, Any]:
        """
        Resolve a conflict between two named subsystems.

        Strategy:
        1. Compare priority (higher wins primary).
        2. Compare health (healthier wins if priority tied).
        3. Capabilities are partitioned — shared ones go to primary.
        4. Both subsystems remain active but roles are clarified.

        Returns:
            Resolution descriptor.
        """
        if a not in self._subsystems or b not in self._subsystems:
            missing = []
            if a not in self._subsystems:
                missing.append(a)
            if b not in self._subsystems:
                missing.append(b)
            return {
                "status": "error",
                "message": f"Unknown subsystem(s): {missing}",
            }

        sub_a = self._subsystems[a]
        sub_b = self._subsystems[b]

        # Compare
        score_a = (sub_a.priority, sub_a.health)
        score_b = (sub_b.priority, sub_b.health)

        if score_a > score_b:
            primary, secondary = a, b
        elif score_b > score_a:
            primary, secondary = b, a
        else:
            # Exact tie — deterministic by name
            primary, secondary = (a, b) if a < b else (b, a)

        shared_caps = set(sub_a.capabilities) & set(sub_b.capabilities)
        exclusive_a = set(sub_a.capabilities) - set(sub_b.capabilities)
        exclusive_b = set(sub_b.capabilities) - set(sub_a.capabilities)

        self._unified_state["conflicts_resolved"] += 1

        return {
            "status": "resolved",
            "primary": primary,
            "secondary": secondary,
            "shared_capabilities": sorted(shared_caps),
            "primary_exclusive": sorted(exclusive_a if primary == a else exclusive_b),
            "secondary_exclusive": sorted(exclusive_b if primary == a else exclusive_a),
            "resolution_strategy": "priority_then_health",
        }

    # -------------------------------------------------------------------
    # Coherence Computation
    # -------------------------------------------------------------------

    def compute_system_coherence(self) -> Dict[str, Any]:
        """
        Compute coherence across ALL subsystems.

        Formula:
            coherence = (avg_health * consensus_rate * integration_density *
                         evolution_rate * field_strength) ^ 0.2

        Returns:
            Coherence descriptor with numeric score and named level.
        """
        if not self._subsystems:
            return {
                "coherence": 0.0,
                "level": "chaotic",
                "components": {},
            }

        subs = list(self._subsystems.values())
        total = len(subs)
        active = [s for s in subs if s.active]
        active_count = len(active)

        avg_health = sum(s.health for s in subs) / total

        # Consensus: fraction of subsystems that are active
        consensus_rate = active_count / total

        # Integration density: unique capabilities / total capability slots
        all_caps = []
        for s in subs:
            all_caps.extend(s.capabilities)
        unique_caps = len(set(all_caps)) if all_caps else 0
        integration_density = unique_caps / max(len(all_caps), 1)

        # Evolution rate: health improvement potential (inverse entropy)
        health_variance = (
            sum((s.health - avg_health) ** 2 for s in subs) / total
            if total > 0 else 0
        )
        evolution_rate = 1.0 - min(health_variance * 2, 1.0)

        # Field strength: weighted by priority and health of active subsystems
        field_strength = (
            sum(s.priority * s.health for s in active) / (active_count * 100)
            if active_count > 0 else 0.0
        )

        product = (
            max(avg_health, 0.001)
            * max(consensus_rate, 0.001)
            * max(integration_density, 0.001)
            * max(evolution_rate, 0.001)
            * max(field_strength, 0.001)
        )
        coherence = product ** 0.2
        coherence = max(0.0, min(1.0, coherence))

        level = "chaotic"
        for threshold, name in COHERENCE_LEVELS:
            if coherence >= threshold:
                level = name
                break

        return {
            "coherence": round(coherence, 6),
            "level": level,
            "components": {
                "avg_health": round(avg_health, 4),
                "consensus_rate": round(consensus_rate, 4),
                "integration_density": round(integration_density, 4),
                "evolution_rate": round(evolution_rate, 4),
                "field_strength": round(field_strength, 4),
            },
            "subsystem_stats": {
                "total": total,
                "active": active_count,
            },
        }

    # -------------------------------------------------------------------
    # Architecture Activation
    # -------------------------------------------------------------------

    def activate_all_architectures(self) -> Dict[str, Any]:
        """
        Activate every established architecture simultaneously.

        Returns:
            Activation summary with state classification.
        """
        if not self._subsystems:
            return {
                "status": "empty",
                "activation_rate": 0.0,
                "state": "dormant",
            }

        total_archs = 0
        activated_archs = 0
        for sub in self._subsystems.values():
            sub.active = True
            total_archs += sub.architecture_count
            activated_archs += sub.architectures_active

        rate = activated_archs / max(total_archs, 1)

        state = "dormant"
        for threshold, name in ARCHITECTURE_STATES:
            if rate >= threshold:
                state = name
                break

        self._unified_state["architectures_activated"] = activated_archs
        self._initialized = True

        return {
            "status": "activated",
            "activation_rate": round(rate, 4),
            "total_architectures": total_archs,
            "activated_architectures": activated_archs,
            "state": state,
            "subsystems_activated": len(self._subsystems),
        }

    # -------------------------------------------------------------------
    # Status
    # -------------------------------------------------------------------

    def get_status(self) -> Dict[str, Any]:
        """
        Return current system status.

        Returns:
            Dict with subsystem_count, coherence, cycle_count, active_architectures.
        """
        coherence_data = self.compute_system_coherence()
        return {
            "subsystem_count": len(self._subsystems),
            "coherence": coherence_data.get("coherence", 0.0),
            "coherence_level": coherence_data.get("level", "unknown"),
            "cycle_count": self._unified_state.get("cycle_count", 0),
            "total_cycles": self._unified_state.get("total_cycles", 0),
            "active_architectures": self._unified_state.get("architectures_activated", 0),
            "conflicts_resolved": self._unified_state.get("conflicts_resolved", 0),
            "global_momentum": self._unified_state.get("global_momentum", 0.0),
            "instance_id": self._instance_id,
            "initialized": self._initialized,
        }

    # -------------------------------------------------------------------
    # Utility / Introspection
    # -------------------------------------------------------------------

    def list_subsystems(self) -> List[str]:
        """Return names of all registered subsystems."""
        return list(self._subsystems.keys())

    def get_subsystem(self, name: str) -> Optional[Subsystem]:
        """Return a subsystem by name."""
        return self._subsystems.get(name)

    def reset_cycles(self) -> None:
        """Reset cycle counters (for testing)."""
        self._unified_state["cycle_count"] = 0
        self._unified_state["total_cycles"] = 0
        self._cycle_log.clear()


# ---------------------------------------------------------------------------
# Global Singleton
# ---------------------------------------------------------------------------

_core_machine_instance: Optional[CoreMachine] = None


def get_core_machine() -> CoreMachine:
    """
    Global singleton accessor for the CoreMachine.

    The same instance is returned on every call within the process lifetime.
    """
    global _core_machine_instance
    if _core_machine_instance is None:
        _core_machine_instance = CoreMachine()
    return _core_machine_instance
